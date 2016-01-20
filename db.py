#!/usr/bin/python
# -*- coding: UTF-8 -*-
import Config,cymysql
class MySQL:
    instance = None
    @staticmethod    
    def db(host=Config.MYSQL_HOST, port=Config.MYSQL_PORT, user=Config.MYSQL_USER,
                                   passwd=Config.MYSQL_PASS, db=Config.MYSQL_DB, charset='utf8'):
        return cymysql.connect(host=host, port=port, user=user,passwd=passwd, db=db, charset=charset)
    
if __name__ == '__main__':
    MySQL.db()
    MySQL.db().close()
    MySQL.db()