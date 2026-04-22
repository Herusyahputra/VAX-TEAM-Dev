import pymysql

try:
    print("Mencoba membuat database 'vax_dev'...")
    conn = pymysql.connect(host='localhost', user='root', password='')
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS vax_dev;")
    print("Database 'vax_dev' berhasil dibuat!")
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
