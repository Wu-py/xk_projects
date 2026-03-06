
import hashlib

import pymysql
from pymysql.cursors import DictCursor
from scrapy.exceptions import DropItem
from twisted.enterprise import adbapi
import logging

from spider.ft_data.ft_data.items import FtDataRepairListItem, FtDataRepairDetailItem

logger = logging.getLogger(__name__)

class FtDataPipeline:
    def __init__(self, db_pool, db_params=None):
        self.db_pool = db_pool
        self.db_params = db_params or {}  # 保存数据库连接参数供后续使用
        self.items_buffer = {
            'ft_repair_list': [],
            'ft_repair_detail': [],
            'ft_ncf_list': [],
            'ft_ncf_detail': [],
            'ft_ewd_list': [],
            'ft_ewd_detail': []
        }
        self.batch_size = 100
        self.dedup_method = 'ignore'
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
        if isinstance(item, FtDataRepairDetailItem):
            table_name = spider.table_name + '_detail'
        else:
            item = self._normalize_item(item, spider)
            table_name = spider.table_name + '_list'
        self.items_buffer[table_name].append(dict(item))
        if len(self.items_buffer[table_name]) >= self.batch_size:
            self._flush_buffer(table_name)
        return item

    def _normalize_item(self, item, spider):
        list_text = item.get('model', '') + item.get('year', '') + item.get('type', '') + item.get('title_1', '') + item.get('title_2', '') + item.get('title_3', '') + item.get('title_4', '') + item.get('title_5', '') + item.get('title_6', '')
        list_key = self.get_md5_basic(list_text)
        item['car_title_key'] = list_key
        return item

    def get_md5_basic(self, text):
        # 1. 字符串必须编码为 bytes (utf-8)
        # 2. 计算 hash
        # 3. 转换为十六进制字符串
        return hashlib.md5(text.encode('utf-8')).hexdigest()


    def _flush_buffer(self, table_name):
        if not self.items_buffer[table_name]:
            return
        try:
            if self.dedup_method == 'query':
                self._insert_with_query()
            else:
                self._insert_batch(table_name)
            logger.info(f"成功插入 {len(self.items_buffer[table_name])} 条数据")
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
        finally:
            self.items_buffer[table_name].clear()

    def _insert_batch(self, table_name):
        if not self.items_buffer[table_name]:
            return
        # 动态获取批次内所有字段的并集
        all_fields = set()
        for item in self.items_buffer[table_name]:
            all_fields.update(item.keys())

        # 确保去重字段在列中（防止去重字段缺失导致 SQL 错误）
        # 如果去重字段在某些 item 中完全缺失，这里会报错，需在 process_item 中过滤
        fields = sorted(list(all_fields))

        values = [tuple(item.get(f) for f in fields) for item in self.items_buffer[table_name]]
        placeholders = ', '.join(['%s'] * len(fields))
        field_names = ', '.join([f'`{f}`' for f in fields])
        if self.dedup_method == 'ignore':
            sql = f"INSERT IGNORE INTO `{table_name}` ({field_names}) VALUES ({placeholders})"
        elif self.dedup_method == 'replace':
            sql = f"REPLACE INTO `{table_name}` ({field_names}) VALUES ({placeholders})"
        else:
            raise ValueError("不支持的去重方式")
        return self.db_pool.runInteraction(self._execute_sql, sql, values)

    def _insert_with_query(self, table_name):
        for item in self.items_buffer[table_name]:
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


    def close_spider(self, spider):
        for table_name in self.items_buffer.keys():
            self._flush_buffer(table_name)
        self.db_pool.close()


