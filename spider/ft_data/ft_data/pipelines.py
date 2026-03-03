
import hashlib

import pymysql
from pymysql.cursors import DictCursor
from scrapy.exceptions import DropItem
from twisted.enterprise import adbapi
import logging

logger = logging.getLogger(__name__)

class FtDataPipeline:
    def __init__(self, db_pool, db_params=None):
        self.db_pool = db_pool
        self.db_params = db_params or {}  # 保存数据库连接参数供后续使用
        self.items_buffer = []
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
        if not self.table_name:
            self.table_name = spider.table_name
        self.items_buffer.append(dict(item))
        if len(self.items_buffer) >= self.batch_size:
            self._flush_buffer()
        return item


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


    def close_spider(self, spider):
        self._flush_buffer()
        self.db_pool.close()


