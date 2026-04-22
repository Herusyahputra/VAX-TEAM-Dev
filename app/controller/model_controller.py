from fastapi import APIRouter, Body
from app.core.config import settings
import os

router = APIRouter(prefix="/model", tags=["Model Management"])

@router.post("/set-colab-url")
def set_colab_url(url: str = Body(..., embed=True)):
    """Menyimpan URL Colab Ngrok ke dalam file .env dan settings."""
    settings.COLAB_API_URL = url
    
    # Update file .env
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
            
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("COLAB_API_URL="):
                    f.write(f"COLAB_API_URL={url}\n")
                else:
                    f.write(line)
        return {"success": True, "message": "URL Colab berhasil disimpan!"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/load")
def load_model():
    """Load model tidak relevan karena model ada di Colab."""
    return {"success": True, "model_loaded": True, "message": "Model berjalan di Google Colab"}

@router.post("/unload")
def unload_model():
    """Unload model tidak relevan."""
    return {"success": True, "model_loaded": True, "message": "Model berjalan di Google Colab"}

@router.get("/status")
def model_status():
    """Cek status Colab Endpoint."""
    colab_ready = bool(settings.COLAB_API_URL)
    
    return {
        "status": "ok" if colab_ready else "error",
        "model_loaded": colab_ready,
        "message": f"Menggunakan Colab API: {settings.COLAB_API_URL}" if colab_ready else "COLAB_API_URL belum di-set",
        "colab_url": settings.COLAB_API_URL
    }
