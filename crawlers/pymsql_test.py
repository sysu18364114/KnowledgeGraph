
import pymysql

if __name__ == '__main__':
    db = pymysql.connect(host="localhost", user="root", password="zhang79367", port=3306, db='spiders')  #本机数据库连接

    cursor=db.cursor()
    cursor.execute('SELECT VERSION()')
    data = cursor.fetchone()
    print('Database version:',data)
    cursor.execute('CREATE DATABASE IF NOT EXISTS spiders DEFAULT CHARACTER SET utf8')
    create_table_sql='CREATE TABLE IF NOT EXISTS students (id VARCHAR(255) NOT NULL, name VARCHAR(255) NOT NULL, age INT NOT NULL, PRIMARY KEY(id))'
    cursor.execute(create_table_sql)
    db.close()