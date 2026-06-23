# VAX Studio DEV v1.2

A web-based generative AI platform for producing images and videos from text/image input, using a hybrid architecture: local server (FastAPI) + cloud GPU engine (Google Colab / Kaggle via Ngrok).

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [Prerequisites](#prerequisites)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Running the Server](#running-the-server)
8. [Connecting the Cloud Engine](#connecting-the-cloud-engine)
9. [Using the Features](#using-the-features)
10. [Project Structure](#project-structure)
11. [API Reference](#api-reference)
12. [Troubleshooting](#troubleshooting)

---

## System Overview

VAX Studio runs on two main components:

| Component | Location | Role |
|---|---|---|
| **VAX Local Server** | Your PC (port 8000) | Manages job queue, stores results, serves the frontend |
| **VAX Engine (Colab/Kaggle)** | Cloud GPU (T4/P100) | Runs heavy AI models (CogVideoX-5B, FLUX, SVD) |

Workflow: Browser → Local Server → Cloud Engine → Results saved locally.

---

## Architecture

```
VAX DEV v1.2
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── core/
│   │   ├── config.py        # All settings loaded from .env
│   │   ├── database.py      # Async MySQL connection
│   │   └── monitor.py       # Live CPU/RAM/GPU stats in terminal
│   ├── controller/
│   │   ├── job_controller.py   # Endpoints: /jobs/*
│   │   └── model_controller.py # Endpoints: /model/*
│   ├── services/
│   │   └── ai_service.py    # Communication logic to Colab/Kaggle
│   ├── model/
│   │   ├── job_model.py     # Job database table schema
│   │   ├── job_schema.py    # Pydantic request/response schemas
│   │   └── outputs/         # Generated images & videos saved here
│   └── view/                # Frontend HTML/CSS/JS
│       ├── index.html       # Landing page
│       ├── text2image.html  # Text-to-Image generator
│       ├── image2video.html # Image-to-Video generator
│       ├── studio.html      # Studio Flow (multi-asset mode)
│       ├── colab.html       # Cloud Engine settings
│       ├── report.html      # Analytics & job history
│       └── workflow.html    # Workflow guide
├── models/                  # Local model cache (optional)
├── colab_engine_v3.1.py     # Engine script to run on Colab/Kaggle
├── .env                     # Environment configuration
├── requirements.txt         # Python dependencies
├── setup.bat                # Automated installation script
└── start_server.bat         # Server startup script
```

---

## Key Features

- **Text to Image** — Generate images from a text prompt using diffusion models (FLUX, etc.) via Colab GPU.
- **Image to Video** — Animate an image into a cinematic video using CogVideoX-5B or Stable Video Diffusion (SVD).
- **Studio Flow** — Advanced production mode: combine multiple images, video references, and audio in one job.
- **Colab Engine Manager** — Connect and monitor the cloud GPU (Ngrok URL) directly from the browser.
- **Job Queue System** — MySQL-backed job queue with real-time progress polling and status updates.
- **Analytics Report** — Full statistics: total jobs, success rate, average duration, and weekly activity chart.
- **Terminal Monitor** — Live CPU, RAM, and local GPU stats printed in the server terminal.

---

## Prerequisites

Make sure the following are installed on your machine:

- **Python** 3.10 or 3.11
- **MySQL** 8.0+ running locally (XAMPP or Laragon works fine)
- **Git** (optional, for cloning the repository)
- Internet connection (to connect to Colab/Kaggle)
- A free **ngrok** account if you run the engine yourself on Colab

---

## Installation

### Step 1 — Clone or Extract the Project

```bash
# From Git
git clone <repo-url> "VAX DEV v.1.2"
cd "VAX DEV v.1.2"

# Or simply extract the ZIP to a folder of your choice
```

### Step 2 — Create the MySQL Database

Open your MySQL client (phpMyAdmin, HeidiSQL, or terminal) and run:

```sql
CREATE DATABASE vax_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Step 3 — Run the Automated Setup

Double-click `setup.bat`. This script will:

1. Create a Python virtual environment (`.venv`)
2. Install PyTorch with CUDA 12.1 support
3. Install all dependencies listed in `requirements.txt`

This process requires an internet connection and will download approximately 2.5 GB.

**Manual installation (alternative):**

```bash
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate

# Install PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install remaining dependencies
pip install -r requirements.txt
```

---

## Configuration

Edit the `.env` file in the project root before starting the server:

```env
# HuggingFace token (required to download models)
# Get yours at: https://huggingface.co/settings/tokens
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# VRAM optimization — adjust based on your GPU
# For 4GB VRAM:
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Server settings
HOST=0.0.0.0
PORT=8000

# Ngrok URL from your active Google Colab or Kaggle session
# Must be updated every time a new Colab/Kaggle session starts
COLAB_API_URL=https://xxxx-xxxx.ngrok-free.app

# MySQL connection string
# Format: mysql+aiomysql://user:password@host:port/database
DB_URL=mysql+aiomysql://root:@localhost:3306/vax_dev

# Default video generation settings
DEFAULT_WIDTH=320
DEFAULT_HEIGHT=240
DEFAULT_NUM_FRAMES=25
DEFAULT_FPS=24
DEFAULT_STEPS=20
MAX_QUEUE_SIZE=3
```

> **Important:** `COLAB_API_URL` must be updated each time a new Colab/Kaggle session starts, because the Ngrok URL changes every session.

---

## Running the Server

### Option 1 — Automated Script (Recommended)

Double-click `start_server.bat`.

The server will start at `http://localhost:8000`.

### Option 2 — Manual via Terminal

```bash
# Activate virtual environment
.venv\Scripts\activate

# Optional: set VRAM optimization
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Start the server
python -m app.main
```

### Accessing the Application

Once the server is running, open your browser and navigate to:

| URL | Description |
|---|---|
| `http://localhost:8000/app/index.html` | VAX Studio main page |
| `http://localhost:8000/docs` | Interactive API documentation (Swagger UI) |
| `http://localhost:8000/model/status` | Check engine connection status |

---

## Connecting the Cloud Engine

VAX Studio offloads all heavy AI processing to a cloud GPU. Follow these steps at the start of each session.

### Step 1 — Start the Engine on Google Colab or Kaggle

1. Open [Google Colab](https://colab.research.google.com) or [Kaggle Notebooks](https://www.kaggle.com/code).
2. Set the runtime to **GPU** (T4 on Colab, or P100/T4 on Kaggle).
3. Upload and run `colab_engine_v3.1.py` from the project root, or paste its contents into a notebook cell.
4. Wait until you see the following output:
   ```
   ONLINE
   URL: https://xxxx-xxxx.ngrok-free.app
   ```

### Step 2 — Connect to VAX Studio

**Method A — Via the Colab Engine page (recommended):**

1. Open `http://localhost:8000/app/colab.html` in your browser.
2. Paste the Ngrok URL into the input field.
3. Click **Connect**.
4. The status indicator will turn green (Engine Connected) if successful.

**Method B — Via .env file:**

1. Open the `.env` file.
2. Update `COLAB_API_URL` with the new Ngrok URL.
3. Restart the server.

**Method C — Via API call:**

```bash
curl -X POST http://localhost:8000/model/set-colab-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://xxxx-xxxx.ngrok-free.app"}'
```

---

## Using the Features

### Text to Image

1. Open `http://localhost:8000/app/text2image.html`.
2. Write a descriptive prompt (English prompts give the best results).
3. Adjust optional parameters: size, inference steps, guidance scale, seed.
4. Click **Generate**. Real-time progress will be displayed.
5. The output image (PNG) can be downloaded directly from the page.

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| Width | 1024 | Image width in pixels (256–2048) |
| Height | 576 | Image height in pixels (256–2048) |
| Inference Steps | 100 | Higher = more detail, but slower |
| Guidance Scale | 8.0 | How strictly the model follows the prompt |
| Seed | -1 | -1 = random. Set a fixed number to reproduce results |

### Image to Video

1. Open `http://localhost:8000/app/image2video.html`.
2. Upload a source image (PNG or JPG).
3. Select a model: **CogVideoX** (higher quality, slower) or **SVD** (faster).
4. Write a motion prompt (for CogVideoX).
5. Click **Generate Video**.
6. The output video (MP4) can be played and downloaded directly.

**CogVideoX Parameters:**

| Parameter | Default | Description |
|---|---|---|
| Num Frames | 17 | Number of video frames (5–33) |
| Guidance Scale | 6.0 | Prompt adherence intensity |
| Inference Steps | 50 | Quality vs. speed tradeoff |

**SVD Parameters:**

| Parameter | Default | Description |
|---|---|---|
| Num Frames | 25 | Number of video frames (1–50) |
| Motion Bucket ID | 127 | Motion intensity (1–255) |
| Noise Aug Strength | 0.02 | Output variation amount |
| FPS | 6 | Output frames per second |

### Studio Flow

1. Open `http://localhost:8000/app/studio.html`.
2. Upload a primary image and optionally additional images, a video reference, or audio.
3. Write a production prompt describing the desired output.
4. Click **Generate**. Studio Flow sends all assets to the engine in one request.

### Viewing Reports and History

Open `http://localhost:8000/app/report.html` to view:

- Total jobs, success rate, and average duration.
- Weekly activity chart.
- Full job history with individual status details.
- List of all saved video files with size and timestamp.

---

## Project Structure

```
VAX DEV v.1.2/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── monitor.py
│   ├── controller/
│   │   ├── job_controller.py
│   │   └── model_controller.py
│   ├── services/
│   │   └── ai_service.py
│   ├── model/
│   │   ├── job_model.py
│   │   ├── job_schema.py
│   │   ├── text_to_image.py
│   │   ├── image_to_video.py
│   │   ├── setup_environment.py   # Script to run on Colab
│   │   └── outputs/               # All generated files are saved here
│   └── view/
│       ├── index.html
│       ├── text2image.html
│       ├── image2video.html
│       ├── studio.html
│       ├── colab.html
│       ├── report.html
│       ├── workflow.html
│       ├── app.js
│       ├── style.css
│       ├── layout.css
│       ├── navbar.css
│       └── footer.css
├── models/                        # HuggingFace model cache
├── colab_engine_v3.1.py           # Engine script for Colab/Kaggle
├── .env                           # Configuration (do NOT commit to Git)
├── requirements.txt
├── setup.bat
├── start_server.bat
├── check_db.py                    # Database connection diagnostic
└── migrate_add_svg_url.py         # Database migration script
```

---

## API Reference

Base URL: `http://localhost:8000`

### Jobs

| Method | Endpoint | Description |
|---|---|---|
| POST | `/jobs/generate_image` | Submit an image generation job |
| POST | `/jobs/generate_video` | Submit a video generation job |
| GET | `/jobs/status/{job_id}` | Get status and progress of a job |
| GET | `/jobs/history` | List all past jobs |
| GET | `/jobs/videos` | List all saved video files |
| DELETE | `/jobs/videos/{filename}` | Delete a video file |
| GET | `/jobs/stats` | Full statistics across all jobs |

### Model / Engine

| Method | Endpoint | Description |
|---|---|---|
| GET | `/model/status` | Check connection to Colab/Kaggle engine |
| POST | `/model/set-colab-url` | Update the Ngrok engine URL |

### Example: Generate Image Request

```json
POST /jobs/generate_image
{
  "prompt": "a futuristic city at night with neon lights, cinematic, 4K",
  "negative_prompt": "blurry, low quality, distorted",
  "width": 1024,
  "height": 576,
  "num_inference_steps": 100,
  "guidance_scale": 8.0,
  "seed": -1
}
```

### Example: Response

```json
{
  "success": true,
  "job_id": "img_a1b2c3d4",
  "message": "Image generation job added to queue."
}
```

### Example: Check Job Status

```
GET /jobs/status/img_a1b2c3d4
```

```json
{
  "job_id": "img_a1b2c3d4",
  "status": "done",
  "type": "image",
  "image_url": "/outputs/img_a1b2c3d4.png",
  "progress": 100,
  "duration_seconds": 45.3
}
```

Possible status values: `queued`, `processing`, `done`, `failed`.

---

## Troubleshooting

### Server fails to start

- Make sure MySQL is running and the `vax_dev` database has been created.
- Verify that `DB_URL` in `.env` matches your MySQL credentials.
- Run `python check_db.py` to diagnose the database connection.

### Engine not connecting (status shows red)

- Check that your Colab/Kaggle session is still active (not timed out due to inactivity).
- Copy the latest Ngrok URL from the Colab output and update it via the Colab Engine page.
- Remember: the Ngrok URL changes every time a new Colab session starts.
- Make sure no firewall is blocking outbound connections to `*.ngrok-free.app`.

### Job is stuck at "processing"

- Verify the Colab session has not disconnected.
- Open the Report page to see the detailed error message for that job.
- Reconnect the engine and submit a new job.

### VRAM out of memory error in Colab

- Make sure the Colab runtime is set to GPU, not CPU.
- Restart the Colab runtime and re-run the engine script.
- Reduce the output resolution or number of frames in the generation settings.

### Port 8000 already in use

Edit `.env` and change `PORT` to another value (e.g., `8001`), then restart the server.

---

## License

Developed by VAX AI Laboratory. For research and development use.
