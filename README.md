# VAX Studio DEV v1.2

A web-based generative AI platform for producing images and videos from text/image input, using a hybrid architecture: **local server (FastAPI)** + **cloud GPU engine (Kaggle / Google Colab via Ngrok)**.

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
13. [Tech Stack](#tech-stack)
14. [Contributors](#contributors)

---

## System Overview

VAX Studio runs on two main components:

| Component | Location | Role |
|---|---|---|
| **VAX Local Server** | Your PC (port 8000) | Manages job queue, stores results, serves the frontend |
| **VAX Engine (Kaggle/Colab)** | Cloud GPU (T4/P100) | Runs heavy AI models (CogVideoX-5B, FLUX, SVD, InsightFace) |

**Workflow:**
```
Browser → Local FastAPI Server → Ngrok → Kaggle/Colab GPU Engine → Results saved locally
```

---

## Architecture

```
VAX DEV v1.2/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── core/
│   │   ├── config.py              # All settings loaded from .env
│   │   ├── database.py            # Async MySQL connection (aiomysql)
│   │   └── monitor.py             # Live CPU/RAM/GPU stats in terminal
│   ├── controller/
│   │   ├── job_controller.py      # Endpoints: /jobs/*
│   │   └── model_controller.py   # Endpoints: /model/*
│   ├── services/
│   │   └── ai_service.py          # Communication logic to Kaggle/Colab engine
│   ├── model/
│   │   ├── job_model.py           # Job database table schema (SQLAlchemy)
│   │   ├── job_schema.py          # Pydantic request/response schemas
│   │   ├── text_to_image.py       # Text-to-image helper
│   │   ├── image_to_video.py      # Image-to-video helper
│   │   ├── setup_environment.py   # Environment setup script for Colab/Kaggle
│   │   ├── check_db.py            # Auto-check & create database on startup
│   │   ├── migrate_add_svg_url.py # Migration: add svg_url column to jobs table
│   │   └── outputs/               # All generated files are saved here
│   └── view/                      # Frontend HTML/CSS/JS
│       ├── index.html             # Dashboard / landing page
│       ├── text2image.html        # Text-to-Image generator
│       ├── image2video.html       # Image-to-Video generator
│       ├── studio.html            # Studio Flow (multi-asset production mode)
│       ├── colab.html             # Cloud Engine settings
│       ├── report.html            # Analytics & job history
│       ├── workflow.html          # Workflow guide
│       ├── app.js                 # Main frontend logic
│       ├── style.css              # Main stylesheet
│       ├── layout.css             # Layout & grid system
│       ├── navbar.css             # Navigation bar styles
│       └── footer.css             # Footer styles
├── models/                        # HuggingFace model cache (optional local)
├── VAX_Model_Kaggle.ipynb         # Kaggle notebook — AI engine
├── patch_notebook.py              # Auto-patcher for Kaggle notebook compatibility
├── update_colab_url.ps1           # PowerShell: update Ngrok URL in .env
├── .env                           # Configuration (DO NOT commit to Git)
├── requirements.txt               # Python dependencies
├── setup.bat                      # Automated installation script (Windows)
└── start_server.bat               # Server startup script (Windows)
```

---

## Key Features

| Feature | Description |
|---|---|
| 🖼️ **Text to Image** | Generate images from a text prompt via Kaggle/Colab GPU (FLUX, SD 1.5) |
| 🎬 **Image to Video** | Animate an image into a cinematic video (CogVideoX-5B or SVD-XT) |
| 🎭 **Face Swap (Photo)** | Swap faces in photos using InsightFace + GFPGAN enhancement |
| 🎥 **Face Swap (Video)** | Swap faces in videos frame-by-frame |
| 🎨 **Studio Flow** | Advanced production mode: combine images, video references, and audio in one job |
| 📊 **Analytics Report** | Job statistics, success rate, average duration, and weekly activity chart |
| 📡 **Colab Engine Manager** | Connect and monitor cloud GPU directly from the browser |
| 🗄️ **Job Queue (MySQL)** | MySQL-backed job queue with real-time progress polling |
| 💻 **Terminal Monitor** | Live CPU, RAM, and local GPU stats printed in the server terminal |

---

## Prerequisites

Make sure the following are installed on your machine:

- **Python** 3.10 or 3.11
- **MySQL** 8.0+ running locally (XAMPP, Laragon, or MySQL Installer)
- **Git** (optional, for cloning the repository)
- Internet connection (to connect to Kaggle/Colab)
- A **Kaggle** account (to run `VAX_Model_Kaggle.ipynb`)
- A free **ngrok** auth token from [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)

---

## Installation

### Step 1 — Clone or Extract the Project

```bash
# From Git
git clone https://github.com/RamadanMufian/VAX-TEAM-Dev.git "VAX DEV v.1.2"
cd "VAX DEV v.1.2"

# Or simply extract the ZIP to a folder of your choice
```

### Step 2 — Create the MySQL Database

Open your MySQL client (phpMyAdmin, HeidiSQL, or terminal) and run:

```sql
CREATE DATABASE vax_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or use the auto-setup script:

```bash
python app/model/check_db.py
```

### Step 3 — Run the Automated Setup

Double-click `setup.bat`. This script will:

1. Create a Python virtual environment (`.venv`)
2. Install PyTorch with CUDA 12.1 support
3. Install all dependencies listed in `requirements.txt`

> This process requires an internet connection and will download approximately 2.5 GB.

**Manual installation (alternative):**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

### Step 4 — Run Database Migration

```bash
python app/model/migrate_add_svg_url.py
```

---

## Configuration

Edit the `.env` file in the project root before starting the server:

```env
# HuggingFace token (required to download models)
# Get yours at: https://huggingface.co/settings/tokens
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# VRAM optimization — adjust based on your GPU
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# Server settings
HOST=0.0.0.0
PORT=8000

# Ngrok URL from your active Kaggle/Colab session
# Must be updated every time a new Kaggle/Colab session starts
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

> ⚠️ **Important:** `COLAB_API_URL` must be updated every time a new Kaggle/Colab session starts, because the Ngrok URL changes every session.

---

## Running the Server

### Option 1 — Automated Script (Recommended)

Double-click `start_server.bat`.

The server will start at `http://localhost:8000`.

### Option 2 — Manual via Terminal

```bash
.venv\Scripts\activate
python -m app.main
```

### Accessing the Application

| URL | Description |
|---|---|
| `http://localhost:8000/app/index.html` | VAX Studio main dashboard |
| `http://localhost:8000/app/text2image.html` | Text-to-Image generator |
| `http://localhost:8000/app/image2video.html` | Image-to-Video generator |
| `http://localhost:8000/app/studio.html` | Studio Flow |
| `http://localhost:8000/app/colab.html` | Cloud Engine settings |
| `http://localhost:8000/app/report.html` | Analytics & job history |
| `http://localhost:8000/docs` | Swagger UI — interactive API docs |

---

## Connecting the Cloud Engine

VAX Studio offloads all heavy AI processing to a cloud GPU. Follow these steps at the start of each session.

### Step 1 — Start the Engine on Kaggle

1. Open [Kaggle Notebooks](https://www.kaggle.com/code) and create a new notebook.
2. Enable GPU: **Settings → Accelerator → GPU T4 x2**.
3. Upload and run `VAX_Model_Kaggle.ipynb`, executing each cell in order:
   - **Cell 1** — Install all dependencies
   - **Cell 2** — Set up directories & download face swap models
   - **Cell 3** — Load face swap models & core functions
   - **Cell 4** — Load AI Video Generator functions (SD, SVD, CogVideoX)
   - **Cell 5** — Start the FastAPI server + Ngrok tunnel

4. In **Cell 5**, fill in your `NGROK_TOKEN` from [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken).

5. After Cell 5 runs, you will see output like:
   ```
   🚀  VAX MODEL API — ONLINE
   📡  Public URL : https://xxxx-xxxx.ngrok-free.app
   📖  Swagger UI : https://xxxx-xxxx.ngrok-free.app/docs
   ```

### Step 2 — Connect to VAX Studio

**Method A — Via the Colab Engine page (recommended):**

1. Open `http://localhost:8000/app/colab.html`.
2. Paste the Ngrok URL into the input field.
3. Click **Connect**. The status indicator will turn green if successful.

**Method B — Via .env file:**

1. Open the `.env` file.
2. Update `COLAB_API_URL` with the new Ngrok URL.
3. Restart the server.

**Method C — Via PowerShell (fastest):**

```powershell
.\update_colab_url.ps1 -Url "https://xxxx-xxxx.ngrok-free.app"
```

**Method D — Via API call:**

```bash
curl -X POST http://localhost:8000/model/set-colab-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://xxxx-xxxx.ngrok-free.app"}'
```

---

## Using the Features

### 🖼️ Text to Image

1. Open `http://localhost:8000/app/text2image.html`.
2. Write a descriptive prompt (English prompts give the best results).
3. Adjust optional parameters: size, inference steps, guidance scale, seed.
4. Click **Generate**. Real-time progress will be displayed.
5. The output image (PNG) can be downloaded directly from the page.

### 🎬 Image to Video

1. Open `http://localhost:8000/app/image2video.html`.
2. Upload a source image (PNG or JPG).
3. Select a model: **CogVideoX** (higher quality, slower) or **SVD** (faster).
4. Write a motion prompt (for CogVideoX).
5. Click **Generate Video**. The output video (MP4) can be played and downloaded.

### 🎭 Face Swap

1. Open Studio Flow at `http://localhost:8000/app/studio.html`.
2. Upload a **source image** (the new face) and a **target** (the photo or video to swap into).
3. Select Face Swap mode.
4. Click **Generate**. The Kaggle engine will process and return the result.

### 📊 Analytics & Job History

Open `http://localhost:8000/app/report.html` to view:

- Total jobs, success rate, and average duration.
- Weekly activity chart.
- Full job history with individual status details.
- List of all saved video files with size and timestamp.

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
| GET | `/model/status` | Check connection to Kaggle/Colab engine |
| POST | `/model/set-colab-url` | Update the Ngrok engine URL |

### Example: Generate Image Request

```json
POST /jobs/generate_image
{
  "prompt": "a futuristic city at night, neon lights, cinematic, 4K",
  "negative_prompt": "blurry, low quality, distorted",
  "width": 1024,
  "height": 576,
  "num_inference_steps": 20,
  "guidance_scale": 7.5,
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

Possible status values: `queued` → `processing` → `done` / `failed`.

---

## Troubleshooting

### Server fails to start

- Make sure MySQL is running and the `vax_dev` database has been created.
- Verify that `DB_URL` in `.env` matches your MySQL credentials.
- Run `python app/model/check_db.py` to diagnose the database connection.

### Engine not connecting (status shows red)

- Check that your Kaggle session is still active (not timed out).
- Copy the latest Ngrok URL from the Kaggle output and update it via the Colab Engine page.
- Remember: the Ngrok URL changes every time a new Kaggle session starts.
- Make sure no firewall is blocking outbound connections to `*.ngrok-free.app`.

### Job is stuck at "processing"

- Check that the Kaggle session has not disconnected.
- Open the Report page to see the detailed error message for that job.
- Reconnect the engine and submit a new job.

### VRAM out of memory error on Kaggle

- Make sure the Kaggle runtime is set to GPU T4, not CPU.
- Restart the Kaggle kernel and re-run all cells from the beginning.
- Reduce the output resolution or number of frames in the generation settings.

### Port 8000 already in use

Edit `.env` and change `PORT` to another value (e.g., `8001`), then restart the server.

### "LF will be replaced by CRLF" warning during git add

This is normal on Windows and can be safely ignored. Git automatically adjusts line endings.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI, Python 3.10/3.11, SQLAlchemy (async), aiomysql |
| **Database** | MySQL 8.0+ |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript |
| **AI Models** | InsightFace, GFPGAN, Stable Diffusion v1.5, SVD-XT, CogVideoX-5B |
| **Cloud GPU** | Kaggle Notebooks (Tesla T4), Google Colab |
| **Tunnel** | Ngrok |
| **Deep Learning** | PyTorch (CUDA 12.1), Diffusers, Transformers, ONNX Runtime |

---

## Contributors

Developed by the **VAX AI Team**.

- [@RamadanMufian](https://github.com/RamadanMufian)
- [@Herusyahputra](https://github.com/Herusyahputra)

Upstream repository: [Herusyahputra/VAX-TEAM-Dev](https://github.com/Herusyahputra/VAX-TEAM-Dev)

---

*For research and development purposes. VAX AI Laboratory © 2026.*
