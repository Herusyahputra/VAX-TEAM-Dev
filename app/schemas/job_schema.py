from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema untuk Request Create Job
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500, description="Deskripsi video yang ingin dibuat")
    negative_prompt: str = Field(default="worst quality, blurry, low resolution", description="Hal yang tidak diinginkan")
    width: int = Field(default=320, ge=64, le=512)
    height: int = Field(default=256, ge=64, le=512)
    num_frames: int = Field(default=25, ge=8, le=1500, description="Jumlah frame (8-1500)")
    num_inference_steps: int = Field(default=20, ge=4, le=50)
    guidance_scale: float = Field(default=3.0, ge=1.0, le=10.0)
    seed: int = Field(default=-1, description="Seed (-1 = random)")

class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=500)
    seed: int = Field(default=-1)

class GenerateVideoFromImageRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 encoded image string")
    seed: int = Field(default=-1)
    duration: int = Field(default=5, ge=2, le=10)

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
