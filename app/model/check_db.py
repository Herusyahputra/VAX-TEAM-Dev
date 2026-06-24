import sys
from sqlalchemy.engine.url import make_url
from sqlalchemy import create_engine
import pymysql

# Add import config to read settings
try:
    from app.core.config import settings
    db_url = settings.DB_URL
    print(f"Menggunakan DB_URL dari konfigurasi: {db_url}")
except Exception as e:
    db_url = "mysql+aiomysql://root:@localhost:3306/vax_dev"
    print(f"Gagal membaca konfigurasi, menggunakan default: {db_url}")

try:
    # Parsing URL menggunakan SQLAlchemy make_url
    url = make_url(db_url)
    
    # Dapatkan nama database yang ingin dibuat
    db_name = url.database
    if not db_name:
        print("Error: Tidak ada nama database dalam DB_URL!")
        sys.exit(1)
        
    print(f"Nama database yang akan dicek/dibuat: '{db_name}'")
    
    # Buat connection string ke MySQL server tanpa database (menggunakan pymysql secara langsung/sinkron untuk setup)
    # Ganti driver ke pymysql karena kita akan membuat DB secara sinkron sebelum server utama berjalan
    sync_url = f"mysql+pymysql://{url.username or 'root'}:{url.password or ''}@{url.host or 'localhost'}:{url.port or 3306}/"
    
    print(f"Menghubungkan ke MySQL server pada {url.host or 'localhost'}:{url.port or 3306}...")
    temp_engine = create_engine(sync_url)
    
    with temp_engine.connect() as conn:
        # Jalankan query untuk membuat database jika belum ada
        # Gunakan text() dari sqlalchemy untuk keamanan/standarisasi
        from sqlalchemy import text
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        print(f"Sukses: Database '{db_name}' berhasil dipastikan ada (dibuat jika belum ada)!")
        
except Exception as e:
    print("\n❌ Gagal menghubungkan ke MySQL atau membuat database!")
    print(f"Error Detail: {str(e)}")
    print("\nSilakan pastikan:")
    print("1. MySQL server (seperti XAMPP, WampServer, Laragon, atau MySQL Installer) sudah dijalankan.")
    print("2. Port MySQL (default: 3306) sudah benar.")
    print("3. Username dan password di file .env sudah sesuai.")
    sys.exit(1)

print("\nSemua beres! Database siap digunakan.")
sys.exit(0)
