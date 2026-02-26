# pipelines.py
import hashlib

import pymysql
from pymysql.cursors import DictCursor
from scrapy.exceptions import DropItem
from twisted.enterprise import adbapi
import logging

logger = logging.getLogger(__name__)

class ChangyiPcPipeline:
    def __init__(self, db_pool, db_params=None):
        self.db_pool = db_pool
        self.db_params = db_params or {}  # 保存数据库连接参数供后续使用
        self.items_buffer = []
        self.batch_size = 100
        self.dedup_method = 'ignore'
        self.unique_fields = ['pp_id', 'chex_name', 'year', 'index_1', 'index_2', 'index_3', 'index_4', 'index_5']
        self.table_name = None
        self.NULL_PLACEHOLDER = 0

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        db_params = {
            'host': settings.get('MYSQL_HOST', 'localhost'),
            'port': settings.getint('MYSQL_PORT', 3306),
            'user': settings.get('MYSQL_USER'),
            'password': settings.get('MYSQL_PASSWORD'),
            'db': settings.get('MYSQL_DB'),
            'charset': settings.get('MYSQL_CHARSET', 'utf8mb4'),
            'cursorclass': DictCursor,
            'use_unicode': True,
        }
        db_pool = adbapi.ConnectionPool('pymysql', **db_params, autocommit=True)
        pipeline = cls(db_pool, db_params)  # 传入 db_params
        pipeline.batch_size = settings.getint('MYSQL_BATCH_SIZE', 100)
        pipeline.dedup_method = settings.get('MYSQL_DEDUPLICATE_METHOD', 'ignore')
        return pipeline

    def process_item(self, item, spider):
        item = self._normalize_item(item, spider)
        if not self.table_name:
            self.table_name = spider.table_name
        self.items_buffer.append(dict(item))
        if len(self.items_buffer) >= self.batch_size:
            self._flush_buffer()
        return item

    def _normalize_item(self, item, spider):

        if 'list' in spider.name:
            """将去重字段中的 None 转换为占位符"""
            for field in self.unique_fields:
                if field in item:
                    if item[field] is None:
                        if field == 'year':
                            item[field] = '__null__'
                        else:
                            item[field] = self.NULL_PLACEHOLDER
                    # 如果是字符串，建议也去除首尾空格，防止 'url ' 和 'url' 被认为不同
                    elif isinstance(item[field], str):
                        item[field] = item[field].strip()
        elif 'chex' in spider.name:
            item['year'] = item['year'] if item['year'] else '__null__'
            list_text = str(item['pp_id']) + item['chex_name'] + item['year']
            list_key = self.get_md5_basic(list_text)
            item['list_key'] = list_key
        return item

    def get_md5_basic(self, text):
        # 1. 字符串必须编码为 bytes (utf-8)
        # 2. 计算 hash
        # 3. 转换为十六进制字符串
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def _flush_buffer(self):
        if not self.items_buffer:
            return
        try:
            if self.dedup_method == 'query':
                self._insert_with_query()
            else:
                self._insert_batch()
            logger.info(f"成功插入 {len(self.items_buffer)} 条数据")
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
        finally:
            self.items_buffer.clear()

    def _insert_batch(self):
        if not self.items_buffer:
            return
        fields = list(self.items_buffer[0].keys())
        values = [tuple(item.get(f) for f in fields) for item in self.items_buffer]
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join([f'`{f}`' for f in fields])
        if self.dedup_method == 'ignore':
            sql = f"INSERT IGNORE INTO `{self.table_name}` ({field_names}) VALUES ({placeholders})"
        elif self.dedup_method == 'replace':
            sql = f"REPLACE INTO `{self.table_name}` ({field_names}) VALUES ({placeholders})"
        else:
            raise ValueError("不支持的去重方式")
        return self.db_pool.runInteraction(self._execute_sql, sql, values)

    def _insert_with_query(self):
        for item in self.items_buffer:
            where_clause = ' AND '.join([f"`{f}` = %s" for f in self.unique_fields])
            select_sql = f"SELECT 1 FROM `{self.table_name}` WHERE {where_clause} LIMIT 1"
            where_values = tuple(item[f] for f in self.unique_fields)
            d = self.db_pool.runInteraction(self._execute_sql, select_sql, [where_values])
            d.addCallback(self._handle_query_result, item)
            d.addErrback(self._handle_error)

    def _handle_query_result(self, result, item):
        if not result:
            fields = list(item.keys())
            values = [tuple(item[f] for f in fields)]
            placeholders = ', '.join(['%s'] * len(fields))
            field_names = ', '.join([f'`{f}`' for f in fields])
            insert_sql = f"INSERT INTO `{self.table_name}` ({field_names}) VALUES ({placeholders})"
            return self.db_pool.runInteraction(self._execute_sql, insert_sql, values)

    def _execute_sql(self, cursor, sql, params=None):
        if params:
            cursor.executemany(sql, params) if isinstance(params[0], (list, tuple)) else cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor.fetchall() if cursor.description else None

    def _handle_error(self, failure):
        logger.error(f"数据库操作失败: {failure.getErrorMessage()}")

    def _update_not_data_notes_sync(self, not_data_cars):
        """同步更新无数据车辆的note字段为'无数据'"""
        if not not_data_cars:
            return

        try:
            # 使用保存的 db_params 创建新连接（避免访问 adbapi 私有属性）
            conn_params = self.db_params.copy()
            # 移除 adbapi 特有参数，避免 pymysql.connect 报错
            conn_params.pop('cursorclass', None)
            conn_params.pop('autocommit', None)

            conn = pymysql.connect(**conn_params)
            try:
                with conn.cursor() as cursor:
                    # 去重 list_key，避免重复更新
                    unique_keys = list(set(not_data_cars))
                    if unique_keys:
                        placeholders = ', '.join(['%s'] * len(unique_keys))
                        sql = f"UPDATE `changyi_chex` SET `note` = '无数据' WHERE `list_key` IN ({placeholders})"
                        cursor.execute(sql, unique_keys)
                        conn.commit()
                        logger.info(f"成功更新 {cursor.rowcount} 条无数据记录的note字段")
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"更新无数据记录失败: {e}")

    def close_spider(self, spider):
        self._flush_buffer()
        # 更新无数据的车辆记录：遍历 spider.not_data_cars，更新 note 字段
        if hasattr(spider, 'not_data_cars') and spider.not_data_cars:
            # 提取所有 list_key（假设 not_data_cars 是 list_key 的列表）
            list_keys = [key for key in spider.not_data_cars if key]
            if list_keys:
                self._update_not_data_notes_sync(list_keys)
        self.db_pool.close()

