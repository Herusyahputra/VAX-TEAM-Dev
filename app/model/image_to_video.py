import os
from app.core.config import settings

def image_to_video(
    image_base64: str,
    num_frames: int = 25,
    motion_bucket_id: int = 127,
    noise_aug_strength: float = 0.02,
    seed: int = 42,
    duration: int = 5,
    save_path: str = None
):
    """
    Fungsi Logic Model untuk Image to Video (Stable Video Diffusion).
    Dalam arsitektur VAX Studio, fungsi ini merepresentasikan logic yang akan dijalankan 
    di Google Colab Engine.
    """
    
    # Generate filename jika tidak ada
    if save_path is None:
        filename = f"vid_{os.urandom(4).hex()}.mp4"
        save_path = str(settings.OUTPUT_DIR / filename)

    print(f"🎞️  [Model Logic] Menyiapkan parameter animasi untuk gambar...")
    
    # Return dictionary parameter untuk dikirim ke Colab via Service
    return {
        "image_base64": image_base64,
        "num_frames": num_frames,
        "motion_bucket_id": motion_bucket_id,
        "noise_aug_strength": noise_aug_strength,
        "seed": seed,
        "duration": duration,
        "save_path": save_path
    }
