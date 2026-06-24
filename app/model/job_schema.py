from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    negative_prompt: Optional[str] = Field(default="blurry, low quality, distorted, watermark, pixelated, ugly, deformed, bad anatomy, artifacts")
    width: int = Field(default=1024, ge=256, le=2048)
    height: int = Field(default=576, ge=256, le=2048)
    num_inference_steps: int = Field(default=100, ge=1, le=150)
    guidance_scale: float = Field(default=8.0, ge=1.0, le=30.0)
    seed: int = Field(default=-1)

class GenerateVideoFromImageRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image string")
    prompt: Optional[str] = Field(default="", max_length=500)
    model: Optional[str] = Field(default="cogvideox")
    # SVD params
    num_frames: Optional[int] = Field(default=25, ge=1, le=50)
    motion_bucket_id: Optional[int] = Field(default=127, ge=1, le=255)
    noise_aug_strength: Optional[float] = Field(default=0.02, ge=0.0, le=1.0)
    fps_svd: Optional[int] = Field(default=6)
    # CogVideoX params
    num_frames_cog: Optional[int] = Field(default=17, ge=5, le=33)
    guidance_scale_cog: Optional[float] = Field(default=6.0)
    num_inference_steps_cog: Optional[int] = Field(default=50)
    # Studio Flow / Multi-Asset
    images_extra: Optional[list[str]] = Field(default=[])
    video_ref: Optional[str] = Field(default=None)
    audio_ref: Optional[str] = Field(default=None)
    # Resolution & Shared
    width: Optional[int] = Field(default=480, ge=64, le=1024)
    height: Optional[int] = Field(default=272, ge=64, le=1024)
    seed: Optional[int] = Field(default=-1)
    duration: Optional[int] = Field(default=5)

# Schema untuk Response Create Job
class GenerateResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    message: Optional[str] = None

# Schema untuk detail status Job
class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    type: str = "video"
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    svg_url: Optional[str] = None
    filename: Optional[str] = None
    seed: Optional[int] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    progress: Optional[int] = 0
    created_at: Optional[datetime] = None
    model_loaded: Optional[bool] = None

    class Config:
        from_attributes = True

# Schema untuk list video
class VideoItem(BaseModel):
    filename: str
    url: str
    size_mb: float
    created_at: float
