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
    """Cek status Colab/Kaggle Endpoint secara real-time."""
    colab_url = settings.COLAB_API_URL
    if not colab_url:
        return {
            "status": "error",
            "model_loaded": False,
            "message": "COLAB_API_URL belum di-set",
            "colab_url": None
        }
    
    colab_url = colab_url.rstrip("/")
    import requests
    try:
        headers = {"ngrok-skip-browser-warning": "true"}
        resp = requests.get(f"{colab_url}/health", headers=headers, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            gpu_name = data.get("gpu", "GPU")
            free_gb = data.get("gpu_memory_free_gb")
            
            # Format vram_info untuk monitor VRAM di frontend colab.html
            vram_info = None
            if free_gb is not None:
                total_vram = 15.0  # Estimasi total VRAM Tesla T4 di Kaggle
                used_vram = max(0.0, total_vram - free_gb)
                vram_info = f"{round(used_vram, 1)}/{total_vram} GiB"
                
            return {
                "status": "ok",
                "model_loaded": True,
                "message": f"Connected to Kaggle ({gpu_name})",
                "colab_url": colab_url,
                "vram_info": vram_info
            }
        else:
            return {
                "status": "error",
                "model_loaded": False,
                "message": f"Kaggle API merespons dengan status {resp.status_code}",
                "colab_url": colab_url
            }
    except Exception as e:
        return {
            "status": "error",
            "model_loaded": False,
            "message": f"Gagal terhubung ke Kaggle API: {str(e)}",
            "colab_url": colab_url
        }
