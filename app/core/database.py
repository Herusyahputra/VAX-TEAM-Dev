import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Automatically create database if it doesn't exist
def create_database_if_not_exists():
    from sqlalchemy.engine.url import make_url
    from sqlalchemy import create_engine, text
    
    db_url = settings.DB_URL
    if not db_url or not db_url.startswith("mysql"):
        return
        
    try:
        url = make_url(db_url)
        db_name = url.database
        if not db_name:
            return
            
        # Build sync connection string to MySQL server without the database name
        sync_url = f"mysql+pymysql://{url.username or 'root'}:{url.password or ''}@{url.host or 'localhost'}:{url.port or 3306}/"
        
        # Connect to MySQL and create database
        temp_engine = create_engine(sync_url)
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            print(f"Database '{db_name}' verified/created successfully.")
    except Exception as e:
        print(f"Warning: Failed to auto-create database '{db_name}': {e}")

create_database_if_not_exists()

# Create Async Engine for MySQL
engine = create_async_engine(
    settings.DB_URL,
    echo=False,  # Set True to see SQL queries in console
    pool_pre_ping=True, # Verify connection before using from pool
)

# Create Async Session Maker
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Declarative Base for Models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
