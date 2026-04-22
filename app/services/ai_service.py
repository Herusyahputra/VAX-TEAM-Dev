import asyncio
import time
import aiohttp
import os
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.model.job_model import Job
from app.schemas.job_schema import GenerateImageRequest, GenerateVideoFromImageRequest

async def _poll_colab_and_download(session, colab_url, colab_job_id, job_id, is_video=True, db=None):
    done = False
    while not done:
        await asyncio.sleep(3)  # Cek setiap 3 detik agar progres lancar
        async with session.get(f"{colab_url}/status/{colab_job_id}") as status_resp:
            if status_resp.status == 200:
                status_data = await status_resp.json()
                
                # Update progress di DB Lokal
                if db and "progress" in status_data:
                    result = await db.execute(select(Job).where(Job.id == job_id.replace("_img", "")))
                    job_local = result.scalar_one_or_none()
                    if job_local:
                        job_local.progress = status_data["progress"]
                        await db.commit()

                if status_data.get("status") == "done":
                    done = True
                elif status_data.get("status") == "failed":
                    raise Exception(f"Generate gagal di Colab: {status_data.get('error')}")
            else:
                print(f"Gagal cek status: {status_resp.status}")

    # Download file
    file_ext = "mp4" if is_video else "png"
    filename = f"{'vid' if is_video else 'img'}_{job_id}.{file_ext}"
    output_path = settings.OUTPUT_DIR / filename
    
    async with session.get(f"{colab_url}/download/{colab_job_id}") as download_resp:
        if download_resp.status == 200:
            with open(output_path, 'wb') as f:
                while True:
                    chunk = await download_resp.content.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
            return filename
        else:
            raise Exception("Gagal download file dari Colab")

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
                    
                filename = await _poll_colab_and_download(session, colab_url, colab_job_id, job_id, is_video=False, db=db)
                
            job.duration_seconds = round(time.time() - start_time, 1)
            job.status = "done"
            job.image_url = f"/outputs/{filename}"
            job.filename = filename
            job.seed = request_data.get("seed", -1)
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
                    
                filename = await _poll_colab_and_download(session, colab_url, colab_job_id, job_id, is_video=True, db=db)
                
            job.duration_seconds = round(time.time() - start_time, 1)
            job.status = "done"
            job.video_url = f"/outputs/{filename}"
            job.filename = filename
            job.seed = request_data.get("seed", -1)
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
        await db.commit()

async def _run_legacy_generation_task(job_id: str, request_data: dict):
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
                # 1. Text to Image
                img_req = {"prompt": request_data["prompt"], "seed": request_data.get("seed", -1)}
                async with session.post(f"{colab_url}/generate_image", json=img_req) as resp:
                    if resp.status != 200: raise Exception(f"Error Colab (Img): {await resp.text()}")
                    img_job_id = (await resp.json()).get("job_id")
                    
                img_filename = await _poll_colab_and_download(session, colab_url, img_job_id, f"{job_id}_img", is_video=False, db=db)
                
                # Convert img to base64
                with open(settings.OUTPUT_DIR / img_filename, "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                
                # 2. Image to Video
                vid_req = {"image_base64": img_b64, "seed": request_data.get("seed", -1), "duration": request_data.get("duration", 5)}
                async with session.post(f"{colab_url}/generate_video", json=vid_req) as resp:
                    if resp.status != 200: raise Exception(f"Error Colab (Vid): {await resp.text()}")
                    vid_job_id = (await resp.json()).get("job_id")
                    
                vid_filename = await _poll_colab_and_download(session, colab_url, vid_job_id, job_id, is_video=True, db=db)
                
            job.duration_seconds = round(time.time() - start_time, 1)
            job.status = "done"
            job.video_url = f"/outputs/{vid_filename}"
            job.image_url = f"/outputs/{img_filename}"
            job.filename = vid_filename
            job.seed = request_data.get("seed", -1)
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
        await db.commit()

async def queue_image_generation(job_id: str, request: GenerateImageRequest, background_tasks):
    request_data = {"prompt": request.prompt, "seed": request.seed}
    background_tasks.add_task(_run_image_generation_task, job_id=job_id, request_data=request_data)

async def queue_video_generation_from_image(job_id: str, request: GenerateVideoFromImageRequest, background_tasks):
    request_data = {
        "image_base64": request.image_base64, 
        "seed": request.seed,
        "duration": request.duration
    }
    background_tasks.add_task(_run_video_generation_from_image_task, job_id=job_id, request_data=request_data)

async def queue_video_generation(job_id: str, request, background_tasks):
    request_data = {
        "prompt": request.prompt,
        "width": request.width,
        "height": request.height,
        "seed": request.seed,
    }
    background_tasks.add_task(_run_legacy_generation_task, job_id=job_id, request_data=request_data)
