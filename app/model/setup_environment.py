# ============================================================
# VAX Studio Colab AI Engine v4.0 — ULTRA HD & SPEED OPTIMIZED
# FIXED: Real-time progress, DPM++ Karras Scheduler, Better VAE
# ============================================================

import os, nest_asyncio, gc, torch, imageio, numpy as np, uuid, base64, io, subprocess, re, tempfile
from PIL import Image
from typing import Optional, Literal
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import asyncio

from diffusers import (
    StableDiffusionPipeline,
    StableVideoDiffusionPipeline,
    DPMSolverMultistepScheduler,
    AutoencoderKL
)
from diffusers.utils import export_to_video

# ── OPTIMIZATION UNTUK KECEPATAN MAKSIMAL DI GPU T4 ──────────
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
torch.backends.cudnn.benchmark = True # Mempercepat iterasi statis

from google.colab import drive
if not os.path.exists('/content/drive'): drive.mount('/content/drive')
nest_asyncio.apply()

# Directories
HF_CACHE = '/content/drive/MyDrive/vax_models_cache'
os.environ["HF_HOME"] = HF_CACHE
os.makedirs(HF_CACHE, exist_ok=True)
BASE_DIR = '/content/drive/MyDrive/AI_Video_Output'
os.makedirs(BASE_DIR, exist_ok=True)

# ── NGROK SETUP ──────────────────────────────────────────────
from pyngrok import ngrok, conf
NGROK_TOKEN = "3ChitPHrdVx5vCS2ObT3PiSmcKT_5VMi8Ms4gZcPA2cp34a4t"
conf.get_default().auth_token = NGROK_TOKEN

app = FastAPI(title="VAX Studio Engine v4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── GLOBAL STATE ─────────────────────────────────────────────
jobs = {}
current_model_name = None
pipe = None

def clear_memory():
    global pipe, current_model_name
    pipe = None; current_model_name = None
    gc.collect()
    if torch.cuda.is_available(): torch.cuda.empty_cache(); torch.cuda.ipc_collect()

try:
    import vtracer
except ImportError:
    subprocess.run(["pip", "install", "vtracer", "-q"], check=True)
    import vtracer

def png_to_svg(png_path: str, svg_path: str):
    vtracer.convert_image_to_svg_py(png_path, svg_path, colormode="color", mode="spline")

def frames_to_animated_svg(frames, svg_path: str, fps: int = 8):
    frame_duration = round(1 / fps, 3)
    total_duration = round(len(frames) * frame_duration, 3)
    frame_svgs = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, frame in enumerate(frames):
            f_small = frame.resize((frame.width//2, frame.height//2), Image.LANCZOS)
            p, s = os.path.join(tmpdir, f"f_{i}.png"), os.path.join(tmpdir, f"f_{i}.svg")
            f_small.save(p)
            vtracer.convert_image_to_svg_py(p, s, colormode="color", color_precision=5)
            with open(s, "r") as f: content = f.read()
            inner = re.search(r"<svg[^>]*>(.*?)</svg>", content, re.DOTALL)
            frame_svgs.append(inner.group(1) if inner else content)

    w, h = frames[0].width // 2, frames[0].height // 2
    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    for i, content in enumerate(frame_svgs):
        begin = round(i * frame_duration, 3)
        svg_parts.append(f'<g opacity="0">{content}<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;{round(frame_duration/total_duration,4)};{round(frame_duration/total_duration,4)};1" begin="{begin}s" dur="{total_duration}s" repeatCount="indefinite"/></g>')
    svg_parts.append('</svg>')
    with open(svg_path, "w") as f: f.write("\n".join(svg_parts))

# ── SCHEMAS & HANDLERS ────────────────────────────────────────
class GenerateImageRequest(BaseModel):
    prompt: str; negative_prompt: str = "blurry"; width: int = 512; height: int = 512; num_inference_steps: int = 25; guidance_scale: float = 7.5; seed: int = -1

class GenerateVideoRequest(BaseModel):
    image_base64: str; prompt: str = ""; model: str = "svd"; width: int = 480; height: int = 272; seed: int = -1

def run_sd15(job_id, req):
    global pipe, current_model_name
    try:
        if current_model_name != "sd15":
            clear_memory()
            print("🚀 Loading VAE & Model for HD Rendering...")
            # OPTIMIZATION 1: Use MSE VAE for much sharper colors and HD look
            vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=torch.float16)
            
            # Load Base Model
            pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5", 
                vae=vae, 
                torch_dtype=torch.float16
            ).to("cuda")
            
            # OPTIMIZATION 2: Use DPM++ 2M Karras Scheduler (Super Fast & Super HD for high steps)
            pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
            
            current_model_name = "sd15"

        actual_seed = req.seed if req.seed != -1 else int(np.random.randint(0, 1000000))
        jobs[job_id]["seed"] = actual_seed

        # CALLBACK UNTUK PROGRESS REAL-TIME LOKAL & COLAB
        def cb(pipe, step, t, kwargs):
            prog = int(((step + 1) / req.num_inference_steps) * 100)
            jobs[job_id]["progress"] = prog
            bar = '█' * (prog // 5) + '░' * (20 - prog // 5)
            print(f"\r🚀 [SD1.5 HD] Job: {job_id} |{bar}| {prog}%", end="", flush=True)
            return kwargs

        image = pipe(
            prompt=req.prompt, negative_prompt=req.negative_prompt,
            width=req.width, height=req.height,
            num_inference_steps=req.num_inference_steps,
            guidance_scale=req.guidance_scale,
            generator=torch.manual_seed(actual_seed),
            callback_on_step_end=cb
        ).images[0]

        raster_path = os.path.join(BASE_DIR, f"{job_id}.png")
        svg_path = os.path.join(BASE_DIR, f"{job_id}.svg")
        image.save(raster_path)
        png_to_svg(raster_path, svg_path)
        jobs[job_id].update({"status": "done", "raster": raster_path, "svg": svg_path, "progress": 100})
    except Exception as e: jobs[job_id].update({"status": "failed", "error": str(e)})

def run_svd(job_id, req):
    global pipe, current_model_name
    try:
        if current_model_name != "svd":
            clear_memory()
            pipe = StableVideoDiffusionPipeline.from_pretrained("stabilityai/stable-video-diffusion-img2vid-xt", torch_dtype=torch.float16, variant="fp16").to("cuda")
            pipe.enable_model_cpu_offload()
            current_model_name = "svd"

        actual_seed = req.seed if req.seed != -1 else int(np.random.randint(0, 1000000))
        jobs[job_id]["seed"] = actual_seed

        # CALLBACK UNTUK PROGRESS REAL-TIME LOKAL & COLAB
        def cb_svd(pipe, step, t, kwargs):
            prog = int(((step + 1) / 25) * 100)
            jobs[job_id]["progress"] = prog
            bar = '█' * (prog // 5) + '░' * (20 - prog // 5)
            print(f"\r🚀 [SVD] Job: {job_id} |{bar}| {prog}%", end="", flush=True)
            return kwargs

        img = Image.open(io.BytesIO(base64.b64decode(req.image_base64))).convert("RGB").resize((req.width, req.height))
        frames = pipe(img, decode_chunk_size=2, num_frames=25, generator=torch.manual_seed(actual_seed), callback_on_step_end=cb_svd).frames[0]

        raster_path = os.path.join(BASE_DIR, f"{job_id}.mp4")
        svg_path = os.path.join(BASE_DIR, f"{job_id}.svg")
        export_to_video(frames, raster_path, fps=7)
        frames_to_animated_svg(frames, svg_path, fps=7)
        jobs[job_id].update({"status": "done", "raster": raster_path, "svg": svg_path, "progress": 100})
    except Exception as e: jobs[job_id].update({"status": "failed", "error": str(e)})

# ── ENDPOINTS ──────────────────────────────────────────────────
@app.post("/generate_image")
def gen_image(req: GenerateImageRequest, bg: BackgroundTasks):
    job_id = f"img_{uuid.uuid4().hex[:8]}"
    jobs[job_id] = {"status": "processing", "progress": 0, "seed": req.seed}
    bg.add_task(run_sd15, job_id, req)
    return {"success": True, "job_id": job_id}

@app.post("/generate_video")
def gen_video(req: GenerateVideoRequest, bg: BackgroundTasks):
    job_id = f"vid_{uuid.uuid4().hex[:8]}"
    jobs[job_id] = {"status": "processing", "progress": 0, "seed": req.seed}
    bg.add_task(run_svd, job_id, req)
    return {"success": True, "job_id": job_id}

@app.get("/status/{job_id}")
def get_status(job_id: str): return jobs.get(job_id, {"status": "not_found"})

@app.get("/download/{job_id}/raster")
def dl_raster(job_id: str):
    job = jobs.get(job_id)
    if job and job["status"] == "done": return FileResponse(job["raster"])
    return JSONResponse(status_code=404, content={"error": "Not ready"})

@app.get("/download/{job_id}/svg")
def dl_svg(job_id: str):
    job = jobs.get(job_id)
    if job and job["status"] == "done": return FileResponse(job["svg"])
    return JSONResponse(status_code=404, content={"error": "Not ready"})

# ── START ────────────────────────────────────────────────────
ngrok.kill()
public_url = ngrok.connect(8000).public_url
print(f"\n🚀 VAX ENGINE v4.0 ONLINE (ULTRA HD & REALTIME PROGRESS)")
print(f"📡 URL: {public_url}\n")
config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
server = uvicorn.Server(config)
asyncio.run(server.serve())
