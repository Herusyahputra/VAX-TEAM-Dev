import asyncio
import time
import aiohttp
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.model.job_model import Job
from app.model.job_schema import GenerateImageRequest, GenerateVideoFromImageRequest
from app.model.text_to_image import text_to_image
from app.model.image_to_video import image_to_video

async def _poll_colab_and_download(session, colab_url, colab_job_id, job_id, is_video=True, db=None):
    done = False
    status_data_final = {}
    while not done:
        await asyncio.sleep(1.5)  # Polling lebih cepat untuk progress real-time
        async with session.get(f"{colab_url}/status/{colab_job_id}") as status_resp:
            if status_resp.status == 200:
                status_data = await status_resp.json()
                
                status_str = str(status_data.get("status", "")).lower()
                
                # Update progress di DB Lokal
                if db and "progress" in status_data:
                    result = await db.execute(select(Job).where(Job.id == job_id))
                    job_local = result.scalar_one_or_none()
                    if job_local:
                        job_local.progress = status_data["progress"]
                        await db.commit()

                if status_str in ["done", "completed", "success", "finished"] or status_data.get("progress") == 100:
                    print(f"\n✅ [JOB DONE] {job_id} completed successfully!")
                    
                    # Handle jika Colab mengembalikan base64 langsung di status
                    if "image_base64" in status_data or "video_base64" in status_data:
                        import base64
                        b64_data = status_data.get("video_base64") if is_video else status_data.get("image_base64")
                        if b64_data:
                            file_ext = "mp4" if is_video else "png"
                            filename = f"{job_id}.{file_ext}"
                            output_path = settings.OUTPUT_DIR / filename
                            with open(output_path, "wb") as f:
                                f.write(base64.b64decode(b64_data))
                            return filename
                    
                    status_data_final = status_data
                    done = True
                elif status_str in ["failed", "error"]:
                    print(f"\n❌ [JOB FAILED] {job_id} failed: {status_data.get('error')}")
                    raise Exception(f"Generate gagal di Colab: {status_data.get('error')}")
                else:
                    # Print progress update
                    p = status_data.get("progress", 0)
                    print(f"\r🚀 [ENGINE PROGRESS] {job_id}: {p}% {'█' * (p // 5)}{'░' * (20 - p // 5)}", end="", flush=True)
            else:
                print(f"Gagal cek status: {status_resp.status} - {await status_resp.text()}")

    # Download file
    file_ext = "mp4" if is_video else "png"
    filename = f"{job_id}.{file_ext}"
    output_path = settings.OUTPUT_DIR / filename
    
    download_endpoints = []
    if is_video:
        download_endpoints = [
            f"/download/{colab_job_id}/raster",
            status_data_final.get("video_url"),
            status_data_final.get("url"),
            f"/outputs/{colab_job_id}.mp4",
            f"/outputs/{colab_job_id}",
            f"/download/{colab_job_id}",
            f"/download?job_id={colab_job_id}"
        ]
    else:
        download_endpoints = [
            f"/download/{colab_job_id}/raster",
            status_data_final.get("image_url"),
            status_data_final.get("url"),
            f"/outputs/{colab_job_id}.png",
            f"/outputs/{colab_job_id}.jpg",
            f"/outputs/{colab_job_id}",
            f"/download/{colab_job_id}",
            f"/download?job_id={colab_job_id}"
        ]
    
    download_endpoints = [e for e in download_endpoints if e]
    
    last_err_text = ""
    last_status = 0
    
    for endpoint in download_endpoints:
        if endpoint.startswith("http"):
            full_download_url = endpoint
        else:
            full_download_url = f"{colab_url}{endpoint}" if endpoint.startswith("/") else f"{colab_url}/{endpoint}"
        
        try:
            async with session.get(full_download_url) as download_resp:
                if download_resp.status == 200:
                    with open(output_path, 'wb') as f:
                        while True:
                            chunk = await download_resp.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                    
                    if output_path.stat().st_size > 0:
                        svg_filename = None
                        try:
                            svg_path = settings.OUTPUT_DIR / f"{job_id}.svg"
                            async with session.get(f"{colab_url}/download/{colab_job_id}/svg") as svg_resp:
                                if svg_resp.status == 200:
                                    with open(svg_path, 'wb') as sf:
                                        sf.write(await svg_resp.content.read())
                                    if svg_path.stat().st_size > 0:
                                        svg_filename = f"{job_id}.svg"
                        except Exception:
                            pass
                        
                        return filename, svg_filename, status_data_final.get("seed")
                else:
                    last_status = download_resp.status
                    last_err_text = await download_resp.text()
        except Exception:
            pass
            
    raise Exception(f"Gagal download dari semua endpoint. Terakhir dicoba: {full_download_url} | Status: {last_status} | Response: {last_err_text} | Status Data: {status_data_final}")

async def _run_image_generation_task(job_id: str, request_data: dict):
    start_time = time.time()
    colab_url = settings.COLAB_API_URL
    if not colab_url:
        return
    colab_url = colab_url.rstrip("/")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job: return
        job.status = "processing"
        await db.commit()
        
        try:
            headers = {"ngrok-skip-browser-warning": "true"}
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(f"{colab_url}/generate_image", json=request_data) as resp:
                    if resp.status != 200: raise Exception(f"Error Colab: {await resp.text()}")
                    colab_job_id = (await resp.json()).get("job_id")
                    
                filename, svg_filename, actual_seed = await _poll_colab_and_download(session, colab_url, colab_job_id, job_id, is_video=False, db=db)
                
            job.duration_seconds = round(time.time() - start_time, 1)
            job.status = "done"
            job.image_url = f"/outputs/{filename}"
            if svg_filename:
                job.svg_url = f"/outputs/{svg_filename}"
            job.filename = filename
            job.seed = actual_seed if actual_seed is not None else request_data.get("seed", -1)
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
        await db.commit()

async def _run_video_generation_from_image_task(job_id: str, request_data: dict):
    start_time = time.time()
    colab_url = settings.COLAB_API_URL
    if not colab_url: return
    colab_url = colab_url.rstrip("/")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job: return
        job.status = "processing"
        await db.commit()
        
        try:
            headers = {"ngrok-skip-browser-warning": "true"}
            async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(limit=10)) as session:
                async with session.post(f"{colab_url}/generate_video", json=request_data) as resp:
                    if resp.status != 200: raise Exception(f"Error Colab: {await resp.text()}")
                    colab_job_id = (await resp.json()).get("job_id")
                    
                filename, svg_filename, actual_seed = await _poll_colab_and_download(session, colab_url, colab_job_id, job_id, is_video=True, db=db)
                
            job.duration_seconds = round(time.time() - start_time, 1)
            job.status = "done"
            job.video_url = f"/outputs/{filename}"
            if svg_filename:
                job.svg_url = f"/outputs/{svg_filename}"
            job.filename = filename
            job.seed = actual_seed if actual_seed is not None else request_data.get("seed", -1)
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
        await db.commit()

async def queue_image_generation(job_id: str, request: GenerateImageRequest, background_tasks):
    """Kirim ke Colab engine v3.0 endpoint /generate_image"""
    request_data = {
        "prompt": request.prompt,
        "negative_prompt": request.negative_prompt or "blurry, low quality, distorted, watermark",
        "width": request.width,
        "height": request.height,
        "num_inference_steps": request.num_inference_steps,
        "guidance_scale": request.guidance_scale,
        "seed": request.seed,
    }
    background_tasks.add_task(_run_image_generation_task, job_id=job_id, request_data=request_data)

async def queue_video_generation_from_image(job_id: str, request: GenerateVideoFromImageRequest, background_tasks):
    """
    Kirim ke Colab engine v3.0 endpoint /generate_video
    Default: CogVideoX (image + prompt → video berkualitas tinggi)
    """
    request_data = {
        "image_base64": request.image_base64,
        "images_extra": request.images_extra,
        "video_ref": request.video_ref,
        "audio_ref": request.audio_ref,
        "prompt": request.prompt or "cinematic video, smooth motion, high quality, 4K",
        "model": request.model,  # "cogvideox" atau "svd"
        # SVD params
        "num_frames_svd": request.num_frames,
        "motion_bucket_id": request.motion_bucket_id,
        "noise_aug_strength": request.noise_aug_strength,
        "fps_svd": request.fps_svd,
        # CogVideoX params
        "num_frames_cog": request.num_frames_cog,
        "guidance_scale_cog": request.guidance_scale_cog,
        "num_inference_steps_cog": request.num_inference_steps_cog,
        # Shared
        "width": request.width,
        "height": request.height,
        "seed": request.seed,
    }
    background_tasks.add_task(_run_video_generation_from_image_task, job_id=job_id, request_data=request_data)
