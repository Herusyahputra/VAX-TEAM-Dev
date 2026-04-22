import pymysql

try:
    print("Mencoba menambahkan kolom progress...")
    conn = pymysql.connect(host='localhost', user='root', password='', database='vax_dev')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN progress INT DEFAULT 0;")
        print("Kolom 'progress' berhasil ditambahkan.")
    except Exception as e:
        print("Kolom 'progress' mungkin sudah ada:", e)

    conn.commit()
    conn.close()
    print("Alter table selesai.")
except Exception as e:
    print(f"Error altering database: {e}")
