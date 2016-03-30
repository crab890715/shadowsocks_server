#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import cymysql
import time
import sys
from server_pool import ServerPool
import Config

class DbTransfer(object):

    instance = None

    def __init__(self):
        self.last_get_transfer = {}

    @staticmethod
    def get_instance():
        if DbTransfer.instance is None:
            DbTransfer.instance = DbTransfer()
        return DbTransfer.instance

    def push_db_all_user(self):
        #更新用户流量到数据库
        last_transfer = self.last_get_transfer
        curr_transfer = ServerPool.get_instance().get_servers_transfer()
        #上次和本次的增量
        dt_transfer = {}
        for id in curr_transfer.keys():
            if id in last_transfer:
                if last_transfer[id][0] == curr_transfer[id][0] and last_transfer[id][1] == curr_transfer[id][1]:
                    continue
                elif curr_transfer[id][0] == 0 and curr_transfer[id][1] == 0:
                    continue
                elif last_transfer[id][0] <= curr_transfer[id][0] and \
                last_transfer[id][1] <= curr_transfer[id][1]:
                    dt_transfer[id] = [curr_transfer[id][0] - last_transfer[id][0],
                                       curr_transfer[id][1] - last_transfer[id][1]]
                else:
                    dt_transfer[id] = [curr_transfer[id][0], curr_transfer[id][1]]
            else:
                if curr_transfer[id][0] == 0 and curr_transfer[id][1] == 0:
                    continue
                dt_transfer[id] = [curr_transfer[id][0], curr_transfer[id][1]]

        self.last_get_transfer = curr_transfer
        query_head = 'UPDATE user'
        query_sub_when = ''
        query_sub_when2 = ''
        query_sub_when3 = ''
        query_sub_when4 = ''
        query_sub_when5 = ''
        query_sub_when6 = ''
        query_sub_in = None
        last_time = time.time()
        for id in dt_transfer.keys():
            query_sub_when += ' WHEN %s THEN u+%s' % (id, dt_transfer[id][0])
            query_sub_when2 += ' WHEN %s THEN d+%s' % (id, dt_transfer[id][1])
            query_sub_when3 += ' WHEN %s THEN month_u+%s' % (id, dt_transfer[id][0])
            query_sub_when4 += ' WHEN %s THEN month_d+%s' % (id, dt_transfer[id][1])
            query_sub_when5 += ' WHEN %s THEN sign_u+%s' % (id, dt_transfer[id][0])
            query_sub_when6 += ' WHEN %s THEN sign_d+%s' % (id, dt_transfer[id][1])
            if query_sub_in is not None:
                query_sub_in += ',%s' % id
            else:
                query_sub_in = '%s' % id
        if query_sub_when == '' and query_sub_when3 == '' and query_sub_when5== '':
            return
        query_sql = query_head + ' SET u = CASE port' + query_sub_when + \
                    ' END, d = CASE port' + query_sub_when2 + \
                    ' END, t = ' + str(int(last_time)) + \
                    ',last_login_server_id = ' +str(int(Config.SERVER_ID)) + \
                    ' WHERE service_type in (0,3) and port IN (%s)' % query_sub_in
        query_sql2 = query_head + ' SET month_u = CASE port' + query_sub_when3 + \
                    ' END, month_d = CASE port' + query_sub_when4 + \
                    ' END, t = ' + str(int(last_time)) + \
                    ',last_login_server_id = ' +str(int(Config.SERVER_ID)) + \
                    ' WHERE service_type in (1,2) and port IN (%s)' % query_sub_in       
        query_sql3 = query_head + ' SET sign_u = CASE port' + query_sub_when5 + \
                    ' END, sign_d = CASE port' + query_sub_when6 + \
                    ' END, t = ' + str(int(last_time)) + \
                    ',last_login_server_id = ' +str(int(Config.SERVER_ID)) + \
                    ' WHERE service_type = 0 and port IN (%s)' % query_sub_in          
        #print query_sql
        conn = cymysql.connect(host=Config.MYSQL_HOST, port=Config.MYSQL_PORT, user=Config.MYSQL_USER,
                               passwd=Config.MYSQL_PASS, db=Config.MYSQL_DB, charset='utf8')
        cur = conn.cursor()
        cur.execute(query_sql)
        cur.execute(query_sql2)
        if Config.SERVER_TYPE=='SIGN' :
            cur.execute(query_sql3)
        cur.close()
        conn.commit()
        conn.close()

    @staticmethod
    def pull_db_all_user():
        #数据库所有用户信息
        conn = cymysql.connect(host=Config.MYSQL_HOST, port=Config.MYSQL_PORT, user=Config.MYSQL_USER,
                               passwd=Config.MYSQL_PASS, db=Config.MYSQL_DB, charset='utf8')
        cur = conn.cursor()
        cur.execute("""
            SELECT port, 
            u, d, transfer_enable,
             passwd, switch, 
             enable,service_type,
             month_flows,month_u,
             month_d,active_time,
             sign_u ,sign_d,sign_total
             FROM user""")
        rows = []
        for r in cur.fetchall():
            rows.append(list(r))
        cur.close()
        conn.close()
        return rows

    @staticmethod
    def del_server_out_of_bound_safe(rows):
    #停止超流量的服务
    #启动没超流量的服务
    #修改下面的逻辑要小心包含跨线程访问
        for row in rows:
            if ServerPool.get_instance().server_is_run(row[0]) is True:
                if Config.SERVER_TYPE=='SIGN' and row[7] in [0]:
                    #状态为0时关闭服务
                    if row[5] == 0 or row[6] == 0:
                        #stop disable or switch off user
                        logging.info('db stop server at port [%s] reason: disable' % (row[0]))
                        ServerPool.get_instance().del_server(row[0])
                    if row[11]<=time.time() or row[12]+row[13]>=row[14]:
                        #stop disable or switch off user
                        logging.info('db stop server at port [%s] reason: disable' % (row[0]))
                        ServerPool.get_instance().del_server(row[0])
                else :
                    #状态为0时关闭服务
                    if row[5] == 0 or row[6] == 0:
                        #stop disable or switch off user
                        logging.info('db stop server at port [%s] reason: disable' % (row[0]))
                        ServerPool.get_instance().del_server(row[0])
                        #固定流量超额停止服务
                    elif row[1] + row[2] >= row[3] and (row[7] in [0,3]):
                        #stop out bandwidth user
                        logging.info('db stop server at port [%s] reason: out bandwidth' % (row[0]))
                        ServerPool.get_instance().del_server(row[0])
                        #包月限流超额停止服务
                    elif row[10] + row[9] >= row[8] and (row[7] in [1]):
                        #stop out bandwidth user
                        logging.info('db stop server at port [%s] reason: out bandwidth' % (row[0]))
                        ServerPool.get_instance().del_server(row[0])
    #                 elif (row[7] in [2,1]) and time.time() > row[8]*24*60*60+row[9]:
    #                     logging.info('db stop server at port [%s] reason: Service maturity' % (row[0]))
    #                     ServerPool.get_instance().del_server(row[0])
                        #修改密码停止服务
                    if ServerPool.get_instance().tcp_servers_pool[row[0]]._config['password'] != row[4]:
                        #password changed
                        logging.info('db stop server at port [%s] reason: password changed' % (row[0]))
                        ServerPool.get_instance().del_server(row[0]) 
                        #如果当前节点是VIP且当前用户没有充值过则停止服务
                    if Config.SERVER_TYPE=='VIP' and row[7] == 0:
                        ServerPool.get_instance().del_server(row[0])
                  
            else:
                if row[5] == 1 and row[6] == 1 :
                    
                    if Config.SERVER_TYPE=='FREE':
                            #固定流量
                        if (row[7] in [0,3]) and row[1] + row[2] < row[3]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])
#                           #包月限流流量
                        if  row[7] == 1 and row[10] + row[9] < row[8]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])
                            #包月不限流量
                        if row[7]==2 :
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])  
                    if Config.SERVER_TYPE=='VIP':
                            #固定流量
                        if  row[7] == 1 and row[10] + row[9] < row[8]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])
                            #包月限流流量
                        if row[7]==2 :
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])  
                            #包月不限流量
                        if row[7]==3 and row[1] + row[2] < row[3]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4]) 
                    if Config.SERVER_TYPE=='SIGN':
                        if row[11]>time.time() and row[12]+row[13]<row[14]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4]) 
                        if  row[7] == 1 and row[10] + row[9] < row[8]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])
                            #包月限流流量
                        if row[7]==2 :
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4])  
                            #包月不限流量
                        if row[7]==3 and row[1] + row[2] < row[3]:
                            logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                            ServerPool.get_instance().new_server(row[0], row[4]) 
    @staticmethod
    def thread_db():
        import socket
        import time
        timeout = 60
        socket.setdefaulttimeout(timeout)
        while True:
            #logging.warn('db loop')
            try:
                DbTransfer.get_instance().push_db_all_user()
                rows = DbTransfer.get_instance().pull_db_all_user()
                DbTransfer.del_server_out_of_bound_safe(rows)
            except Exception as e:
                logging.warn('db thread except:%s' % e)
            finally:
                time.sleep(15)


#SQLData.pull_db_all_user()
#print DbTransfer.get_instance().test()
