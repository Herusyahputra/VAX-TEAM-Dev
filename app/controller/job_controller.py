import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.config import settings
from app.model.job_model import Job
from app.schemas.job_schema import GenerateRequest, GenerateImageRequest, GenerateVideoFromImageRequest, GenerateResponse, JobStatusResponse, VideoItem
from app.services.ai_service import queue_video_generation, queue_image_generation, queue_video_generation_from_image

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/generate", response_model=GenerateResponse)
async def generate_video(
    request: GenerateRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    (Legacy) Membuat antrian job baru untuk menghasilkan video langsung dari teks.
    """
    job_id = str(uuid.uuid4())[:12]
    new_job = Job(
        id=job_id, prompt=request.prompt, negative_prompt=request.negative_prompt,
        width=request.width, height=request.height, num_frames=request.num_frames,
        num_inference_steps=request.num_inference_steps, guidance_scale=request.guidance_scale,
        seed=request.seed, status="queued", type="video"
    )
    db.add(new_job)
    await db.commit()
    await queue_video_generation(job_id, request, background_tasks)
    return GenerateResponse(success=True, job_id=job_id, message="Tugas generate video dimasukkan ke antrian.")

@router.post("/generate_image", response_model=GenerateResponse)
async def generate_image(
    request: GenerateImageRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    job_id = f"img_{uuid.uuid4().hex[:8]}"
    new_job = Job(
        id=job_id, prompt=request.prompt, seed=request.seed, status="queued", type="image"
    )
    db.add(new_job)
    await db.commit()
    await queue_image_generation(job_id, request, background_tasks)
    return GenerateResponse(success=True, job_id=job_id, message="Tugas generate image dimasukkan ke antrian.")

@router.post("/generate_video_from_image", response_model=GenerateResponse)
async def generate_video_from_image(
    request: GenerateVideoFromImageRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    job_id = f"vid_{uuid.uuid4().hex[:8]}"
    new_job = Job(
        id=job_id, prompt="", seed=request.seed, status="queued", type="video"
    )
    db.add(new_job)
    await db.commit()
    await queue_video_generation_from_image(job_id, request, background_tasks)
    return GenerateResponse(success=True, job_id=job_id, message="Tugas generate video dari image dimasukkan ke antrian.")

@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
        
    return JobStatusResponse(
        job_id=job.id, status=job.status, type=job.type, prompt=job.prompt,
        image_url=job.image_url, video_url=job.video_url, filename=job.filename,
        seed=job.seed, error=job.error_message, duration_seconds=job.duration_seconds,
        progress=job.progress,
        created_at=job.created_at, model_loaded=bool(settings.COLAB_API_URL)
    )

@router.get("/history")
async def list_jobs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).order_by(desc(Job.created_at)).limit(limit))
    jobs = result.scalars().all()
    return {"jobs": jobs}

@router.get("/videos")
def list_videos():
    videos = []
    output_dir = settings.OUTPUT_DIR
    if output_dir.exists():
        for f in sorted(output_dir.glob("*.mp4"), reverse=True):
            stat = f.stat()
            videos.append({
                "filename": f.name, "url": f"/outputs/{f.name}",
                "size_mb": round(stat.st_size / 1024**2, 2), "created_at": stat.st_mtime,
            })
    return {"videos": videos[:20]}

@router.delete("/videos/{filename}")
def delete_video(filename: str):
    filepath = settings.OUTPUT_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    filepath.unlink()
    return {"message": f"{filename} berhasil dihapus"}
