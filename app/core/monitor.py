import os
import time
import threading
import psutil
import shutil

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False

class TerminalMonitor:
    def __init__(self, interval=2):
        self.interval = interval
        self.running = False
        self.thread = None
        
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
            except Exception:
                self.gpu_count = 0
        else:
            self.gpu_count = 0

    def get_gpu_stats(self):
        stats = []
        if self.gpu_count > 0:
            try:
                for i in range(self.gpu_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes): name = name.decode('utf-8')
                    
                    stats.append({
                        "name": name,
                        "used": info.used // 1024**2,
                        "total": info.total // 1024**2,
                        "util": util.gpu
                    })
            except Exception:
                pass
        return stats

    def print_stats(self):
        while self.running:
            # Clear line (ANSI)
            print("\r", end="")
            
            # CPU & RAM
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            
            gpu_str = ""
            gpus = self.get_gpu_stats()
            if gpus:
                for g in gpus:
                    gpu_str += f" | GPU: {g['util']}% ({g['used']}MB/{g['total']}MB)"
            else:
                gpu_str = " | GPU: N/A"

            # Print status line
            # Gunakan warna hijau untuk status
            print(f"\033[92m[STATS] CPU: {cpu}% | RAM: {ram}%{gpu_str}\033[0m", end="", flush=True)
            
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.print_stats, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass

monitor = TerminalMonitor()
