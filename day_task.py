#!/usr/bin/python
# -*- coding: UTF-8 -*-
from db import MySQL
import cymysql,time,datetime,calendar
def get_service(uid,types):
    conn = MySQL.db()
    today = time.strftime("%Y-%m-%d")
    cur = conn.cursor(cursor=cymysql.cursors.DictCursor)
    cur.execute("""
    SELECT * FROM 
    t_user_service  
    where state=1 
    and uid=%s 
    and service_type in %s 
    and end_date>=%s 
    and start_date<=%s 
    order by end_date ASC limit 1
    """,[uid,types,today,today])
    data = cur.fetchone()
    cur.close()
    conn.close()
    return data
#不是同一年且不是同一月，则说明当前时间已经过了
def date_test(d1,d2,today,days):
    if d1.year != today.year and d1.month != today.month:
        if d1.day==today.day or d1.day>=days:
            return True
    return False
#包月月结
def up_month_user(service,type):
    conn = MySQL.db()
    cur = conn.cursor()
    cur.execute("""
    update user 
    set 
    month_u=0,
    month_d=0,
    month_flows=%s,
    service_type=%s
    where uid=%s
    """,[service['transfer'],service['service_type'],service['uid']])
    conn.commit()
    cur.close()
    conn.close()
def up_flow_user(uid,type):
    conn = MySQL.db()
    cur = conn.cursor()
    cur.execute("""
    update user set
    service_type=%s
    where uid=%s
    """,[type,uid])
    conn.commit()
    cur.close()
    conn.close()
def run():
    conn = MySQL.db()
    cur = conn.cursor(cursor=cymysql.cursors.DictCursor)
    cur.execute("SELECT * FROM user where switch=1 and enable=1")
    today = datetime.datetime.now()
    days = calendar.monthrange(today.year, today.month)[1]
    for user in cur.fetchall():
        service = get_service(user['uid'],[1,2])
        #如果当前用户包含包月服务
        if service and (date_test(service['start_date'],service['end_date'],today,days)):
#             重新初始化包月流量
            up_month_user(service,user['service_type'])
        #包月服务不存在或者服务存在且为固定流量包月用完的需要更新为固定流量
        elif not service or (service and user['month_u']+user['month_d']>=user['month_flows'] and user['service_type']==1):
            service = get_service(user['uid'],[3])
            if service and user['service_type'] in [1,2]:
                up_flow_user(3,user['uid'])
            else :
                up_flow_user(0,user['uid'])
    cur.close()
    conn.close()
if __name__ == '__main__':
    run()