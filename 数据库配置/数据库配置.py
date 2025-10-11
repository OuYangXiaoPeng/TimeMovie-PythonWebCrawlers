# 数据库配置.py
import pymysql


def get_connection():
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='xueniansheji',
        charset='utf8mb4',
        autocommit=True
    )
