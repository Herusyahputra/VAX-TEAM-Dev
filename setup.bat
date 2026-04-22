@echo off
title Setup & Install Dependencies
color 0E

echo.
echo  ============================================================
echo   SETUP - Install Semua Dependencies
echo   RTX 3050 4GB - LTX Video Project
echo  ============================================================
echo.

:: Step 1: Buat venv
echo  [1/4] Membuat virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo         .venv sudah ada, skip.
) else (
    python -m venv .venv
    echo         .venv berhasil dibuat!
)
echo.

:: Aktifkan
call .venv\Scripts\activate.bat

:: Step 2: Install PyTorch CUDA
echo  [2/4] Install PyTorch dengan CUDA 12.1...
echo        (File ~2.5GB, butuh waktu...)
echo.
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.

:: Step 3: Install FastAPI & dependencies
echo  [3/4] Install dependencies dari requirements.txt...
pip install -r requirements.txt

echo.

:: Step 4: Cek GPU
echo  [4/4] Verifikasi GPU...
python test_gpu.py

echo.
echo  ============================================================
echo   SETUP SELESAI!
echo   
echo   Langkah berikutnya:
echo   1. Download model: double-click download_model.bat
echo   2. Jalankan server: double-click start_server.bat
echo  ============================================================
echo.
pause
