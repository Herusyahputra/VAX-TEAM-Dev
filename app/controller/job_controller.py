import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from app.core.database import get_db
from app.core.config import settings
from app.model.job_model import Job
from app.model.job_schema import GenerateImageRequest, GenerateVideoFromImageRequest, GenerateResponse, JobStatusResponse
from app.services.ai_service import queue_image_generation, queue_video_generation_from_image

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    # Total jobs
    total_result = await db.execute(select(func.count(Job.id)))
    total_jobs = total_result.scalar()

    # Success vs Failed
    success_result = await db.execute(select(func.count(Job.id)).where(Job.status == "done"))
    success_count = success_result.scalar()
    
    failed_result = await db.execute(select(func.count(Job.id)).where(Job.status == "failed"))
    failed_count = failed_result.scalar()

    # Average duration
    avg_dur_result = await db.execute(select(func.avg(Job.duration_seconds)).where(Job.status == "done"))
    avg_duration = avg_dur_result.scalar() or 0

    # Type breakdown
    img_result = await db.execute(select(func.count(Job.id)).where(Job.type == "image"))
    img_count = img_result.scalar()
    
    vid_result = await db.execute(select(func.count(Job.id)).where(Job.type == "video"))
    vid_count = vid_result.scalar()

    # Recent activity (last 24h)
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    recent_result = await db.execute(select(func.count(Job.id)).where(Job.created_at >= yesterday))
    recent_count = recent_result.scalar()

    # Error summary
    error_summary_result = await db.execute(
        select(Job.error_message, func.count(Job.id))
        .where(Job.status == "failed")
        .group_by(Job.error_message)
        .limit(5)
    )
    errors = [{"msg": r[0][:50] + "..." if r[0] else "Unknown", "count": r[1]} for r in error_summary_result.all()]

    # Active jobs
    active_result = await db.execute(select(func.count(Job.id)).where(Job.status.in_(["queued", "processing"])))
    active_count = active_result.scalar()

    # Video-specific stats
    video_total_result = await db.execute(select(func.count(Job.id)).where(Job.type == "video"))
    video_total = video_total_result.scalar() or 0
    
    video_success_result = await db.execute(select(func.count(Job.id)).where(Job.type == "video", Job.status == "done"))
    video_success = video_success_result.scalar() or 0
    
    video_avg_dur_result = await db.execute(select(func.avg(Job.duration_seconds)).where(Job.type == "video", Job.status == "done"))
    video_avg_duration = video_avg_dur_result.scalar() or 0

    # Weekly activity
    from datetime import date
    weekly_stats = await db.execute(
        select(func.date(Job.created_at).label("date"), Job.type, func.count(Job.id))
        .where(Job.created_at >= datetime.now() - timedelta(days=7))
        .group_by(func.date(Job.created_at), Job.type)
        .order_by(func.date(Job.created_at))
    )
    
    weekly_activity = {}
    for r in weekly_stats.all():
        d_str = r[0].strftime("%m/%d")
        if d_str not in weekly_activity:
            weekly_activity[d_str] = {"image": 0, "video": 0}
        weekly_activity[d_str][r[1]] = r[2]

    return {
        "total": total_jobs,
        "success": success_count,
        "failed": failed_count,
        "active": active_count,
        "recent_24h": recent_count,
        "avg_duration": round(avg_duration, 2),
        "video_metrics": {
            "total": video_total,
            "success_rate": round(video_success / video_total * 100) if video_total > 0 else 0,
            "avg_duration": round(video_avg_duration, 2)
        },
        "breakdown": {
            "image": img_count,
            "video": vid_count
        },
        "weekly_activity": weekly_activity,
        "errors": errors
    }

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

@router.post("/generate_video", response_model=GenerateResponse)
@router.post("/generate_video_from_image", response_model=GenerateResponse)
async def generate_video_from_image(
    request: GenerateVideoFromImageRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    job_id = f"vid_{uuid.uuid4().hex[:8]}"
    new_job = Job(
        id=job_id, prompt=request.prompt or "Video generation", seed=request.seed, status="queued", type="video"
    )
    db.add(new_job)
    await db.commit()
    await queue_video_generation_from_image(job_id, request, background_tasks)
    return GenerateResponse(success=True, job_id=job_id, message="Tugas generate video dimasukkan ke antrian.")

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
