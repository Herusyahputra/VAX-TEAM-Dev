import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.controller import job_controller, model_controller
from app.core.monitor import monitor

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Buat tabel database saat startup jika belum ada
    async with engine.begin() as conn:
        # PENTING: Untuk production disarankan pakai Alembic untuk migration
        await conn.run_sync(Base.metadata.create_all)
    
    # Mulai monitor statistik di terminal
    monitor.start()
    yield
    # Cleanup saat shutdown
    monitor.stop()
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Generate video dari teks dengan arsitektur MVC & MySQL",
    lifespan=lifespan
)

# Konfigurasi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounting static files (output videos & frontend views)
if settings.OUTPUT_DIR.exists():
    app.mount("/outputs", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="outputs")

if settings.VIEW_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(settings.VIEW_DIR), html=True), name="view")

# Register Routers (Controllers)
app.include_router(job_controller.router)
app.include_router(model_controller.router)

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs_url": "/docs",
        "health_check": "/model/status"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        workers=1,
    )
