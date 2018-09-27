import os
import sqlite3

from logger import logger

## reference : https://www.cndba.cn/dave/article/2154


class DataBase(object):
    """数据库"""

    def __init__(self, path):
        self.path = path

    def get_conn(self):
        """
        获取数据库连接
        """
        conn = sqlite3.connect(self.path)
        return conn

    def get_cursor(self, conn):
        """
        该方法是获取数据库的游标对象，参数为数据库的连接对象
        """
        if conn is not None:
            return conn.cursor()
        else:
            return self.get_conn().cursor()

    def close_all(self, conn, cu):
        """
        关闭数据库游标对象和数据库连接对象
        """
        cu.close()
        conn.close()

    def create_table(self, sql):
        """
        创建数据库表
        """
        if sql is not None and sql != '':
            conn = self.get_conn()
            cu = self.get_cursor(conn)
            logger.debug('SQL:[{}]'.format(sql))
            cu.execute(sql)
            conn.commit()
            self.close_all(conn, cu)
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))

    def drop_table(self, table):
        """
        如果表存在,则删除表
        """
        if table is not None and table != '':
            sql = 'DROP TABLE IF EXISTS ' + table
            logger.debug('SQL:[{}]'.format(sql))
            conn = self.get_conn()
            cu = self.get_cursor(conn)
            cu.execute(sql)
            conn.commit()
            cu.close()
            conn.close()
            # self.close_all(conn, cu)
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))

    def insert(self, sql, data):
        """
        插入数据
        """
        if sql is not None and sql != '':
            if data is not None:
                conn = self.get_conn()
                cu = self.get_cursor(conn)
                for d in data:
                    logger.debug('SQL:[{}]'.format(str(sql + str(d))))
                    cu.execute(sql, d)
                    conn.commit()
                self.close_all(conn, cu)
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))

    def fetchall(self, sql):
        """
        查询所有数据
        """
        if sql is not None and sql != '':
            conn = self.get_conn()
            cu = self.get_cursor(conn)
            logger.debug('SQL:[{}]'.format(sql))
            cu.execute(sql)
            r = cu.fetchall()
            self.close_all(conn, cu)
            return r
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))

    def fetchone(self, sql, data):
        """
        查询一条数据
        """
        if sql is not None and sql != '':
            if data is not None:
                d = (data, )
                conn = self.get_conn()
                cu = self.get_cursor(conn)
                logger.debug('SQL:[{}]'.format(str(sql + str(data))))
                cu.execute(sql, d)
                r = cu.fetchall()
                self.close_all(conn, cu)
                return r
            else:
                logger.error('the [{}] equal None!'.format(data))
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))

    def update(self, sql, data):
        """
        更新数据
        """
        if sql is not None and sql != '':
            if data is not None:
                conn = self.get_conn()
                cu = self.get_cursor(conn)
                for d in data:
                    logger.debug('SQL:[{}]'.format(str(sql + str(d))))
                    cu.execute(sql, d)
                    conn.commit()
                self.close_all(conn, cu)
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))

    def delete(self, sql, data):
        """
        删除数据
        """
        if sql is not None and sql != '':
            if data is not None:
                d = (data, )
                conn = self.get_conn()
                cu = self.get_cursor(conn)
                logger.debug('SQL:[{}]'.format(str(sql + str(data))))
                cu.execute(sql, d)
                conn.commit()
                self.close_all(conn, cu)
        else:
            logger.error('the [{}] is empty or equal None!'.format(sql))
