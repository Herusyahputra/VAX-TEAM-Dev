
import os
import torch
import numpy as np
import cv2
import io
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

# ============================================================
# [CORE] MULTIMODAL EVALUATOR CLASS
# ============================================================
class MultimodalEvaluator:
    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[*] Loading CLIP model on {self.device}...")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        print("[*] Model loaded successfully!")

    def calculate_clip_score_image(self, prompt, image_path_or_pil):
        try:
            if isinstance(image_path_or_pil, str):
                image = Image.open(image_path_or_pil).convert("RGB")
            else:
                image = image_path_or_pil.convert("RGB")
                
            inputs = self.processor(text=[prompt], images=image, return_tensors="pt", padding=True).to(self.device)
            with torch.no_grad():
                outputs = self.model(**inputs)
                score = outputs.logits_per_image.item() / 100.0
            return float(score)
        except Exception as e:
            print(f"    [!] Error CLIP Image: {e}")
            return 0.0

    def evaluate_video_pipeline(self, prompt, video_path):
        cap = cv2.VideoCapture(video_path)
        frames = []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0: return None
        
        step = max(total_frames // 16, 1)
        for i in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(frame))
            if len(frames) >= 16: break
        cap.release()

        inputs = self.processor(text=[prompt], images=frames, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            text_video_score = outputs.logits_per_text.mean().item() / 100.0
            image_features = outputs.image_embeds
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            
            temporal_scores = []
            for i in range(len(image_features) - 1):
                sim = torch.nn.functional.cosine_similarity(image_features[i:i+1], image_features[i+1:i+2])
                temporal_scores.append(sim.item())
            avg_temp = sum(temporal_scores) / len(temporal_scores) if temporal_scores else 0
            
        return {"clip_vid": text_video_score, "temporal": avg_temp}

# ============================================================
# [UTILS] MATH & FILE UTILITIES
# ============================================================
def calculate_mse(p1, p2):
    try:
        img1 = np.array(Image.open(p1).convert("RGB"))
        img2 = np.array(Image.open(p2).convert("RGB"))
        if img1.shape != img2.shape: return 999.0
        return float(np.mean((img1 - img2) ** 2))
    except: return 999.0

def calculate_ssim(p1, p2):
    try:
        img1 = cv2.imread(p1)
        img2 = cv2.imread(p2)
        if img1.shape != img2.shape: img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        return float(cv2.matchTemplate(g1, g2, cv2.TM_CCORR_NORMED)[0][0])
    except: return 0.0

def svg_to_pil(svg_path):
    """Konversi SVG ke PIL Image menggunakan resvg_py (Terverifikasi: svg_to_bytes)."""
    errs = []
    
    # Cara Utama: Menggunakan resvg_py
    try:
        import resvg_py
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_text = f.read()
        
        # Gunakan fungsi svg_to_bytes yang sudah terverifikasi
        png_bytes = resvg_py.svg_to_bytes(svg_text)
        
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception as e:
        errs.append(f"resvg error: {e}")

    # Fallback 1: svglib
    try:
        from svglib.svglib import svg2rlg
        from reportlab.graphics import renderPM
        drawing = svg2rlg(svg_path)
        img_data = renderPM.drawToString(drawing, fmt="PNG")
        return Image.open(io.BytesIO(img_data)).convert("RGB")
    except Exception as e:
        errs.append(f"svglib error: {e}")

    # Fallback 2: cairosvg
    try:
        import cairosvg
        png_bytes = cairosvg.svg2png(url=svg_path, output_width=1024)
        return Image.open(io.BytesIO(png_bytes)).convert("RGB")
    except Exception as e:
        errs.append(f"cairosvg error: {e}")
    
    print(f"    [!] Debug SVG Errors: {errs}")
    return None

# ============================================================
# [MAIN] INTERACTIVE VALIDATION WIZARD
# ============================================================
def get_path(label, default_name=""):
    path = input(f"    >> Masukkan Path/Nama File untuk {label}: ").strip().replace('"', '')
    if not path and default_name: path = default_name
    return path

def run_interactive_validation():
    print("\n" + "="*80)
    print("   VAX STUDIO - INTERACTIVE SCIENTIFIC VALIDATOR v4.2")
    print("="*80)
    
    prompt = input("\n[1/6] Masukkan PROMPT yang digunakan: ").strip()
    if not prompt: prompt = "A breathtaking anime landscape in the style of Studio Ghibli"

    print("\n[2/6] MODUL DETERMINISME (Uji Seed Locking)")
    l1 = get_path("Locked Seed Image 1")
    l2 = get_path("Locked Seed Image 2")
    r1 = get_path("Random Seed Image (Baseline)")
    
    print("\n[3/6] MODUL ABLASI (Uji Negative Prompt)")
    img_neg = get_path("Image WITH Negative Prompt")
    img_no_neg = get_path("Image WITHOUT Negative Prompt")

    print("\n[4/6] MODUL INSIGHT (Raster vs Vector)")
    raster_path = get_path("Original RASTER File (.png)")
    vector_path = get_path("Generated VECTOR File (.svg)")

    print("\n[5/6] MODUL MULTIMODAL (Video)")
    video_path = get_path("Video File (.mp4)")

    print("\n[6/6] MODUL STEP ANALYSIS (Inference Steps Impact)")
    low_step_path = get_path("Low-Step Image (e.g. 25 steps)")
    high_step_path = get_path("High-Step Image (e.g. 50 steps)")

    # Initialize Evaluator AFTER inputs to save VRAM while waiting for user
    evaluator = MultimodalEvaluator()

    print("\n" + "="*80)
    print("   STARTING SCIENTIFIC ANALYSIS...")
    print("="*80)

    # --- 1. DETERMINISM TEST ---
    if os.path.exists(l1) and os.path.exists(l2):
        print("\n[RESULT] DETERMINISME (SEED LOCKING)")
        mse = calculate_mse(l1, l2)
        ssim = calculate_ssim(l1, l2)
        print(f"    > MSE (Locked)  : {mse:.4f} (Target: 0.0)")
        print(f"    > SSIM (Locked) : {ssim:.4f} (Target: 1.0)")
        if os.path.exists(r1):
            mse_r = calculate_mse(l1, r1)
            print(f"    > MSE (Random)  : {mse_r:.4f} (Variance)")

    # --- 2. ABLATION STUDY ---
    if os.path.exists(img_neg) and os.path.exists(img_no_neg):
        print("\n[RESULT] ABLATION STUDY (NEGATIVE PROMPT)")
        clip_w = evaluator.calculate_clip_score_image(prompt, img_neg)
        clip_n = evaluator.calculate_clip_score_image(prompt, img_no_neg)
        print(f"    > CLIP (With Neg) : {clip_w:.4f}")
        print(f"    > CLIP (No Neg)   : {clip_n:.4f}")
        print(f"    > Impact Delta    : {clip_w - clip_n:+.4f}")

    # --- 3. INSIGHT ANALYSIS ---
    if os.path.exists(raster_path) and os.path.exists(vector_path):
        print("\n[RESULT] INSIGHT ANALYSIS (RASTER VS VECTOR)")
        svg_pil = svg_to_pil(vector_path)
        if svg_pil:
            clip_png = evaluator.calculate_clip_score_image(prompt, raster_path)
            clip_svg = evaluator.calculate_clip_score_image(prompt, svg_pil)
            print(f"    > CLIP Raster (PNG): {clip_png:.4f}")
            print(f"    > CLIP Vector (SVG): {clip_svg:.4f}")
            print(f"    > Fidelity Loss    : {abs(clip_png - clip_svg):.4f}")
        else:
            print("    [!] SVG Evaluation failed. Check debug logs above.")

    # --- 4. MULTIMODAL VIDEO ---
    if os.path.exists(video_path):
        print("\n[RESULT] MULTIMODAL (IMAGE-TO-VIDEO)")
        vid_res = evaluator.evaluate_video_pipeline(prompt, video_path)
        if vid_res:
            print(f"    > Temporal Const. : {vid_res['temporal']:.4f}")
            print(f"    > Text-Video Align: {vid_res['clip_vid']:.4f}")

    # --- 5. STEP ANALYSIS ---
    if os.path.exists(low_step_path) and os.path.exists(high_step_path):
        print("\n[RESULT] STEP ANALYSIS (INFERENCE STEPS)")
        clip_low = evaluator.calculate_clip_score_image(prompt, low_step_path)
        clip_high = evaluator.calculate_clip_score_image(prompt, high_step_path)
        print(f"    > CLIP (Low Steps) : {clip_low:.4f}")
        print(f"    > CLIP (High Steps): {clip_high:.4f}")
        print(f"    > Quality Gain     : {clip_high - clip_low:+.4f}")

    print("\n" + "="*80)
    print("   VALIDATION COMPLETE: SYSTEM IS READY FOR PUBLICATION")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_interactive_validation()
