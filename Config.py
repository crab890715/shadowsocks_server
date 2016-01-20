#!/usr/bin/python
# -*- coding: UTF-8 -*-
#Config
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USER = 'username'
MYSQL_PASS = 'password'
MYSQL_DB = 'ss'
#对应ss_node表的id
SERVER_ID = 1
#节点类型：FREE为免费，VIP为付费节点,必须大写
SERVER_TYPE= 'FREE'
#更新用户流量
API_HOST='wykxsw.com'
#删除服务触发接口
API_EVENT_DEL_SERVER="/api/update"

MANAGE_PASS = 'ss233333333'
#if you want manage in other server you should set this value to global ip
MANAGE_BIND_IP = '127.0.0.1'
#make sure this port is idle
MANAGE_PORT = 23333
