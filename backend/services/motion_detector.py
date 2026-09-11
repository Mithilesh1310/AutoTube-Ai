import os
import subprocess
import shutil
import logging
from typing import Dict, Any, List
from PIL import Image, ImageChops, ImageStat
import imageio_ffmpeg
from backend.config import settings

logger = logging.getLogger(__name__)

class MotionDetector:
    """
    Motion Detection Validation Service:
    Independently inspects generated video MP4 clips frame-by-frame.
    Calculates motion score, frozen frame percentage, and duplicate frame ratio.
    Ensures FULL_ANIMATION contains genuine temporal movement and rejects static images disguised as MP4.
    """
    def __init__(self):
        try:
            self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            self.ffmpeg_exe = shutil.which("ffmpeg") or "ffmpeg"

    def analyze_video_motion(self, video_path: str, sample_frames: int = 15) -> Dict[str, Any]:
        """
        Extracts sample frames from MP4 clip and computes pixel difference variance.
        Returns: motion_score, frozen_frame_pct, duplicate_frame_ratio, is_genuine_animation.
        """
        if not os.path.exists(video_path) or os.path.getsize(video_path) < 5000:
            return {
                "motion_score": 0.0,
                "scene_motion_score": 0.0,
                "dynamic_pixel_ratio": 0.0,
                "zero_motion_detected": True,
                "frozen_frame_pct": 100.0,
                "duplicate_frame_ratio": 1.0,
                "is_genuine_animation": False,
                "error": "File missing or empty"
            }

        temp_dir = os.path.join(os.path.dirname(video_path), "motion_temp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            # Extract sample frames using FFmpeg
            cmd = [
                self.ffmpeg_exe,
                "-y",
                "-i", video_path,
                "-vf", "fps=3",
                os.path.join(temp_dir, "frame_%03d.png")
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            extracted_files = sorted([
                os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".png")
            ])

            if len(extracted_files) < 2:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return {
                    "motion_score": 0.0,
                    "scene_motion_score": 0.0,
                    "dynamic_pixel_ratio": 0.0,
                    "zero_motion_detected": True,
                    "frozen_frame_pct": 100.0,
                    "duplicate_frame_ratio": 1.0,
                    "is_genuine_animation": False,
                    "error": "Insufficient frames extracted"
                }

            # Compare adjacent frame differences
            diff_scores = []
            dynamic_pixel_ratios = []
            scene_motion_scores = []
            duplicate_count = 0

            import numpy as np

            for i in range(len(extracted_files) - 1):
                with Image.open(extracted_files[i]) as img1, Image.open(extracted_files[i+1]) as img2:
                    img1_rgb = img1.convert("RGB").resize((128, 128))
                    img2_rgb = img2.convert("RGB").resize((128, 128))
                    
                    diff = ImageChops.difference(img1_rgb, img2_rgb)
                    stat = ImageStat.Stat(diff)
                    diff_val = sum(stat.mean) / 3.0
                    diff_scores.append(diff_val)

                    arr1 = np.array(img1_rgb, dtype=np.float32)
                    arr2 = np.array(img2_rgb, dtype=np.float32)
                    pixel_diff = np.abs(arr1 - arr2).mean(axis=-1)
                    changed_pixels = np.count_nonzero(pixel_diff > 6.0)
                    dyn_ratio = changed_pixels / pixel_diff.size
                    dynamic_pixel_ratios.append(dyn_ratio)
                    
                    norm_motion = float(pixel_diff.mean() / 100.0)
                    scene_motion_scores.append(norm_motion)

                    if diff_val < 0.5: # Virtually identical frames
                        duplicate_count += 1

            shutil.rmtree(temp_dir, ignore_errors=True)

            avg_motion = sum(diff_scores) / len(diff_scores) if diff_scores else 0.0
            frozen_pct = (duplicate_count / len(diff_scores)) * 100.0 if diff_scores else 100.0
            duplicate_ratio = duplicate_count / len(diff_scores) if diff_scores else 1.0
            avg_dyn_ratio = sum(dynamic_pixel_ratios) / len(dynamic_pixel_ratios) if dynamic_pixel_ratios else 0.0
            avg_scene_motion = sum(scene_motion_scores) / len(scene_motion_scores) if scene_motion_scores else 0.0
            zero_motion = (avg_dyn_ratio < 0.05 or avg_scene_motion < 0.02 or frozen_pct >= 60.0)

            # Genuine animation requires minimum average motion and dynamic pixel thresholds
            is_genuine = (avg_scene_motion > 0.05 and avg_dyn_ratio > 0.08 and not zero_motion)

            logger.info(
                f"[MotionDetector] Analyzed '{os.path.basename(video_path)}': "
                f"Scene Motion = {avg_scene_motion:.3f}, Dyn Pixels = {avg_dyn_ratio:.3f}, "
                f"Zero Motion = {zero_motion}, Genuine = {is_genuine}"
            )

            return {
                "motion_score": round(avg_motion, 3),
                "scene_motion_score": round(avg_scene_motion, 4),
                "dynamic_pixel_ratio": round(avg_dyn_ratio, 4),
                "zero_motion_detected": zero_motion,
                "frozen_frame_pct": round(frozen_pct, 1),
                "duplicate_frame_ratio": round(duplicate_ratio, 3),
                "is_genuine_animation": is_genuine
            }

        except Exception as e:
            logger.error(f"[MotionDetector] Frame extraction error: {e}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return {
                "motion_score": 0.0,
                "scene_motion_score": 0.0,
                "dynamic_pixel_ratio": 0.0,
                "zero_motion_detected": True,
                "frozen_frame_pct": 100.0,
                "duplicate_frame_ratio": 1.0,
                "is_genuine_animation": False,
                "error": str(e)
            }

motion_detector = MotionDetector()
