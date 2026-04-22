from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, nullable=True)
    width = Column(Integer, default=320)
    height = Column(Integer, default=256)
    num_frames = Column(Integer, default=25)
    num_inference_steps = Column(Integer, default=20)
    guidance_scale = Column(Float, default=3.0)
    seed = Column(Integer, default=-1)
    
    status = Column(String(50), default="queued", index=True) # queued, processing, done, failed
    type = Column(String(20), default="video") # image, video
    image_url = Column(String(255), nullable=True)
    video_url = Column(String(255), nullable=True)
    filename = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    progress = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
