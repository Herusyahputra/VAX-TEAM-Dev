import os
from app.core.config import settings

def text_to_image(
    prompt: str,
    negative_prompt: str = "blurry, low quality, distorted, watermark",
    width: int = 1024,
    height: int = 576,
    num_inference_steps: int = 30,
    guidance_scale: float = 7.5,
    seed: int = 42,
    save_path: str = None
):
    """
    Fungsi Logic Model untuk Text to Image (Stable Diffusion v1.5).
    Dalam arsitektur VAX Studio, fungsi ini merepresentasikan logic yang akan dijalankan 
    di Google Colab Engine.
    """
    
    # Generate filename jika tidak ada
    if save_path is None:
        filename = f"img_{os.urandom(4).hex()}.png"
        save_path = str(settings.OUTPUT_DIR / filename)

    print(f"🖼️  [Model Logic] Menyiapkan parameter untuk: {prompt[:30]}...")
    
    # Return dictionary parameter untuk dikirim ke Colab via Service
    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "num_inference_steps": num_inference_steps,
        "guidance_scale": guidance_scale,
        "seed": seed,
        "save_path": save_path
    }
