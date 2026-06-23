import json
from pathlib import Path

def patch_notebook():
    notebook_path = Path("VAX_Model_Kaggle.ipynb")
    if not notebook_path.exists():
        print("❌ Error: File VAX_Model_Kaggle.ipynb tidak ditemukan di folder ini.")
        return

    with open(notebook_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── Monkeypatch untuk CELL 1, 3, 5 ──────────────────────────
    monkeypatch_code = (
        "# ── HF MONKEYPATCH ──\n"
        "import huggingface_hub\n"
        "try:\n"
        "    from huggingface_hub import cached_download\n"
        "except ImportError:\n"
        "    import huggingface_hub.file_download\n"
        "    huggingface_hub.cached_download = huggingface_hub.hf_hub_download\n"
        "    huggingface_hub.file_download.cached_download = huggingface_hub.hf_hub_download\n"
        "try:\n"
        "    from huggingface_hub.utils import HfFolder\n"
        "except ImportError:\n"
        "    try:\n"
        "        from huggingface_hub import HfFolder\n"
        "    except ImportError:\n"
        "        class HfFolder:\n"
        "            @classmethod\n"
        "            def get_token(cls): import os; return os.environ.get('HF_TOKEN')\n"
        "            @classmethod\n"
        "            def save_token(cls, token): pass\n"
        "            @classmethod\n"
        "            def delete_token(cls): pass\n"
        "    import huggingface_hub.utils\n"
        "    huggingface_hub.utils.HfFolder = HfFolder\n"
        "    huggingface_hub.HfFolder = HfFolder\n"
        "import huggingface_hub.constants\n"
        "if not hasattr(huggingface_hub.constants, 'HF_HUB_ENABLE_HF_TRANSFER'):\n"
        "    huggingface_hub.constants.HF_HUB_ENABLE_HF_TRANSFER = False\n"
        "# ───────────────────\n"
    )

    patched_count = 0

    for cell in data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue

        source = cell.get("source", "")
        if isinstance(source, list):
            source_str = "".join(source)
        else:
            source_str = source

        changed = False

        # ── 1. Hapus patch lama jika ada, ganti dengan yang baru ──
        if "# ── HF MONKEYPATCH ──" in source_str:
            parts = source_str.split("# ───────────────────\n")
            if len(parts) > 1:
                source_str = parts[1].lstrip("\n")

        # ── 2. Tempel monkeypatch di awal cell utama ──────────────
        if any(imp in source_str for imp in ["import cv2", "import uvicorn", "import subprocess, sys"]):
            source_str = monkeypatch_code + "\n" + source_str
            changed = True

        # ── 3. Fix callback lama → callback_on_step_end (CELL 4) ──
        old_cb_sd = "callback=lambda s, t, kw: _show_progress(job_id, s, steps, 'SD1.5')"
        new_cb_sd = "callback_on_step_end=lambda pipe, i, t, kw: (_show_progress(job_id, i, steps, 'SD1.5'), kw)[1]"
        if old_cb_sd in source_str:
            source_str = source_str.replace(old_cb_sd, new_cb_sd)
            changed = True

        old_cb_svd = "callback=lambda s, t, kw: _show_progress(job_id, s, 20, 'SVD')"
        new_cb_svd = "callback_on_step_end=lambda pipe, i, t, kw: (_show_progress(job_id, i, 20, 'SVD'), kw)[1]"
        if old_cb_svd in source_str:
            source_str = source_str.replace(old_cb_svd, new_cb_svd)
            changed = True

        old_cb_cog = "callback=lambda s, t, kw: _show_progress(job_id, s, 25, 'CogVideo')"
        new_cb_cog = "callback_on_step_end=lambda pipe, i, t, kw: (_show_progress(job_id, i, 25, 'CogVideo'), kw)[1]"
        if old_cb_cog in source_str:
            source_str = source_str.replace(old_cb_cog, new_cb_cog)
            changed = True

        # ── 4. Fix req.dict() → req.model_dump() (Pydantic V2) ──
        if "req.dict()" in source_str:
            source_str = source_str.replace(
                "background_tasks.add_task(run_sd15, job_id, req.dict())",
                "background_tasks.add_task(run_sd15, job_id, req.model_dump())"
            )
            changed = True

        # ── 5. Fix SVD: hapus enable_vae_slicing() & enable_vae_tiling() ──
        # StableVideoDiffusionPipeline versi baru tidak punya method ini
        if "StableVideoDiffusionPipeline" in source_str:
            old_svd_block = (
                "gen_pipe = gen_pipe.to('cuda')\n"
                "            gen_pipe.enable_attention_slicing()\n"
                "            gen_pipe.enable_vae_slicing()\n"
                "            gen_pipe.enable_vae_tiling()\n"
                "            gen_pipe.enable_sequential_cpu_offload()"
            )
            new_svd_block = (
                "gen_pipe = gen_pipe.to('cuda')\n"
                "            gen_pipe.enable_attention_slicing()\n"
                "            gen_pipe.enable_sequential_cpu_offload()"
            )
            if old_svd_block in source_str:
                source_str = source_str.replace(old_svd_block, new_svd_block)
                changed = True

        # ── 6. Fix CogVideoX OOM: aggressive memory management ──────
        if "CogVideoXImageToVideoPipeline" in source_str:

            # Ganti model_cpu_offload → sequential_cpu_offload (hemat VRAM per-layer)
            for old_offload in [
                "gen_pipe.enable_model_cpu_offload()",
                "gen_pipe.enable_sequential_cpu_offload()",
            ]:
                if old_offload in source_str:
                    source_str = source_str.replace(
                        old_offload,
                        "gen_pipe.enable_sequential_cpu_offload()\n"
                        "            gen_pipe.unet.enable_forward_chunking(chunk_size=1) if hasattr(gen_pipe, 'unet') else None"
                    )
                    changed = True
                    break

            # Pastikan VAE slicing & tiling aktif
            if "gen_pipe.vae.enable_tiling()" not in source_str:
                source_str = source_str.replace(
                    "gen_pipe.enable_sequential_cpu_offload()",
                    "gen_pipe.enable_sequential_cpu_offload()\n"
                    "            gen_pipe.vae.enable_tiling()\n"
                    "            gen_pipe.vae.enable_slicing()"
                )
                changed = True

            # Kurangi num_frames CogVideoX seminimal mungkin: 5 frames
            for old_f in [
                "n_frames = min(req.get('num_frames', 13), 13)",
                "n_frames = min(req.get('num_frames', 9), 9)",
            ]:
                if old_f in source_str:
                    source_str = source_str.replace(
                        old_f,
                        "n_frames = min(req.get('num_frames', 5), 5)"
                    )
                    changed = True
                    break

            # Kurangi inference steps CogVideoX: 15 steps
            for old_steps in [
                "num_inference_steps=25, num_frames=n_frames,",
                "num_inference_steps=20, num_frames=n_frames,",
            ]:
                if old_steps in source_str:
                    source_str = source_str.replace(
                        old_steps,
                        "num_inference_steps=15, num_frames=n_frames,"
                    )
                    changed = True
                    break

            # Tambahkan torch.cuda.empty_cache() sebelum inference CogVideoX
            old_inference_cog = "with torch.inference_mode():\n            frames = gen_pipe(\n                prompt=req.get('prompt'"
            new_inference_cog = (
                "torch.cuda.empty_cache()\n"
                "        torch.cuda.synchronize()\n"
                "        with torch.inference_mode():\n"
                "            frames = gen_pipe(\n"
                "                prompt=req.get('prompt'"
            )
            if old_inference_cog in source_str and "torch.cuda.empty_cache()\n        torch.cuda.synchronize()" not in source_str:
                source_str = source_str.replace(old_inference_cog, new_inference_cog)
                changed = True

        if changed:
            cell["source"] = source_str
            patched_count += 1

    if patched_count > 0:
        with open(notebook_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print(f"✅ Berhasil memperbarui patch VAX_Model_Kaggle.ipynb! ({patched_count} cell diperbarui)")
        print("   - [HF MONKEYPATCH]   cached_download, HfFolder, HF_HUB_ENABLE_HF_TRANSFER")
        print("   - [CELL 4 FIXED]     callback= → callback_on_step_end= (SD1.5, SVD, CogVideoX)")
        print("   - [SVD FIXED]        Hapus enable_vae_slicing/tiling yang tidak ada di versi baru")
        print("   - [COG OOM FIXED]    sequential_cpu_offload + 5 frames + 15 steps + cache clear")
        print("   - [PYDANTIC FIXED]   req.dict() → req.model_dump()")
    else:
        print("ℹ️ Tidak ada cell yang perlu di-patch.")

if __name__ == "__main__":
    patch_notebook()
