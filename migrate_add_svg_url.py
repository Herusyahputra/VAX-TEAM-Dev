"""
Migration: Add svg_url column to jobs table
Run once: python migrate_add_svg_url.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='vax_dev',
    charset='utf8mb4'
)
cur = conn.cursor()

try:
    # Cek apakah kolom sudah ada
    cur.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'vax_dev'
          AND TABLE_NAME   = 'jobs'
          AND COLUMN_NAME  = 'svg_url'
    """)
    exists = cur.fetchone()[0]

    if exists:
        print("[OK] Kolom 'svg_url' sudah ada -- tidak perlu migrasi.")
    else:
        cur.execute("""
            ALTER TABLE jobs
            ADD COLUMN svg_url VARCHAR(255) NULL
            COMMENT 'SVG vector output URL'
            AFTER video_url
        """)
        conn.commit()
        print("[OK] Migration sukses! Kolom 'svg_url' berhasil ditambahkan ke tabel 'jobs'.")

except Exception as e:
    conn.rollback()
    print(f"[ERROR] Migration gagal: {e}")
finally:
    cur.close()
    conn.close()
