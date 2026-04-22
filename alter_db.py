import pymysql

try:
    print("Mencoba alter table jobs...")
    conn = pymysql.connect(host='localhost', user='root', password='', database='vax_dev')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN type VARCHAR(20) DEFAULT 'video';")
        print("Kolom 'type' berhasil ditambahkan.")
    except Exception as e:
        print("Kolom 'type' mungkin sudah ada:", e)
        
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN image_url VARCHAR(255) DEFAULT NULL;")
        print("Kolom 'image_url' berhasil ditambahkan.")
    except Exception as e:
        print("Kolom 'image_url' mungkin sudah ada:", e)

    conn.commit()
    conn.close()
    print("Alter table selesai.")
except Exception as e:
    print(f"Error altering database: {e}")
