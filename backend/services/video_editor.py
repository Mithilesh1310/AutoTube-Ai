import os
import shutil
import subprocess
import logging
from typing import List, Dict, Any, Optional
import imageio_ffmpeg
from backend.config import settings

logger = logging.getLogger(__name__)

class FFmpegVideoEditor:
    def __init__(self):
        try:
            self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            self.ffmpeg_exe = shutil.which("ffmpeg") or "ffmpeg"
        logger.info(f"FFmpeg executable path: {self.ffmpeg_exe}")

    def generate_srt_subtitles(self, scenes: List[Dict[str, Any]], srt_path: str):
        """Generates Devanagari Hindi SRT subtitle file synchronized with scene audio durations."""
        os.makedirs(os.path.dirname(srt_path), exist_ok=True)
        
        current_time = 0.0
        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, scene in enumerate(scenes, 1):
                dur = scene.get("duration_seconds", 5.0)
                dialogue = scene.get("dialogue", "").strip()
                if not dialogue:
                    current_time += dur
                    continue

                start_h = int(current_time // 3600)
                start_m = int((current_time % 3600) // 60)
                start_s = int(current_time % 60)
                start_ms = int((current_time - int(current_time)) * 1000)

                end_time = current_time + dur
                end_h = int(end_time // 3600)
                end_m = int((end_time % 3600) // 60)
                end_s = int(end_time % 60)
                end_ms = int((end_time - int(end_time)) * 1000)

                f.write(f"{idx}\n")
                f.write(f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> {end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}\n")
                f.write(f"{dialogue}\n\n")

                current_time += dur

        logger.info(f"[VideoEditor] Generated Hindi SRT subtitles -> {srt_path}")

    async def assemble_video(
        self,
        job_id: str,
        scenes: List[Dict[str, Any]],
        images_dict: Dict[int, str],
        audios_dict: Dict[int, str],
        output_video_path: str,
        is_vertical: bool = False,
        animation_clips_dict: Optional[Dict[int, str]] = None
    ) -> str:
        """Assembles either animated video clips or scene images (Ken Burns), Hindi voice tracks, subtitles, and outputs MP4."""
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        work_dir = f"./storage/renders/{job_id}/segments"
        os.makedirs(work_dir, exist_ok=True)

        width = 1080 if is_vertical else 1920
        height = 1920 if is_vertical else 1080
        fps = 25

        segment_paths = []
        anim_clips = animation_clips_dict or {}

        for scene in scenes:
            num = scene.get("scene_number", 1)
            audio_path = audios_dict.get(num)
            dur = scene.get("duration_seconds", 5.0)
            anim_clip = anim_clips.get(num)
            img_path = images_dict.get(num)

            segment_out = os.path.join(work_dir, f"segment_{num}.mp4")

            # 1. Render Animated Video Clip Segment if available (FULL_ANIMATION mode)
            if anim_clip and os.path.exists(anim_clip):
                vf_scale = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
                cmd = [self.ffmpeg_exe, "-y", "-i", anim_clip]
                if audio_path and os.path.exists(audio_path):
                    cmd.extend(["-i", audio_path, "-vf", vf_scale, "-c:v", "libx264", "-c:a", "aac", "-shortest", segment_out])
                else:
                    cmd.extend(["-vf", vf_scale, "-c:v", "libx264", segment_out])

            # 2. Otherwise render Image Motion Ken Burns Segment (IMAGE_MOTION mode)
            elif img_path and os.path.exists(img_path):
                total_frames = int(dur * fps)
                # High-fidelity smooth Ken Burns zoom with explicit fps matching target canvas
                vf_filter = (
                    f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                    f"zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s={width}x{height}:fps={fps}"
                )
                cmd = [self.ffmpeg_exe, "-y", "-loop", "1", "-t", str(dur), "-i", img_path]

                high_bitrate_flags = [
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "18",
                    "-b:v", "6000k",
                    "-maxrate", "8000k",
                    "-bufsize", "12000k",
                    "-pix_fmt", "yuv420p"
                ]

                if audio_path and os.path.exists(audio_path):
                    cmd.extend(["-i", audio_path, "-vf", vf_filter] + high_bitrate_flags + ["-c:a", "aac", "-b:a", "192k", "-shortest", segment_out])
                else:
                    cmd.extend(["-vf", vf_filter] + high_bitrate_flags + [segment_out])
            else:
                logger.warning(f"No asset found for scene {num}. Skipping segment.")
                continue

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0 and os.path.exists(segment_out):
                segment_paths.append(segment_out)
            else:
                logger.error(f"FFmpeg segment error for scene {num}: {result.stderr.decode('utf-8', errors='ignore')}")

        if not segment_paths:
            raise RuntimeError("No video segments rendered successfully.")

        # Concatenate all segment MP4 files
        concat_list_path = os.path.join(work_dir, "concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for seg in segment_paths:
                f.write(f"file '{os.path.abspath(seg)}'\n")

        temp_concatenated = os.path.join(work_dir, "concatenated.mp4")
        concat_cmd = [
            self.ffmpeg_exe, "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", temp_concatenated
        ]
        subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        shutil.copy2(temp_concatenated, output_video_path)
        logger.info(f"[VideoEditor] Final MP4 Video rendered successfully -> {output_video_path}")
        return output_video_path

video_editor_service = FFmpegVideoEditor()
