from pathlib import Path
import subprocess, shutil, tempfile, os, json
from core.video_analyzer import analyze_video
from engines.mp4_patch.mp4_patcher import patch_mp4_timing

def _ffmpeg():
    p = shutil.which("ffmpeg")
    if not p: raise RuntimeError("ffmpeg was not found. Install FFmpeg and add its bin folder to PATH.")
    return p

def run_patch(input_path, output_dir, factor):
    src = Path(input_path)
    out = Path(output_dir) / f"{src.stem}_Mords_{factor}x.mp4"
    if out.exists(): out = Path(output_dir) / f"{src.stem}_Mords_{factor}x_new.mp4"
    patch_mp4_timing(src, out, factor)
    return out

def run_interpolation(input_path, output_dir, multiplier, rife_exe):
    src = Path(input_path)
    ffmpeg = _ffmpeg()
    info = analyze_video(src)
    try: source_fps = float(info["fps"])
    except Exception: raise RuntimeError("Could not determine source FPS.")
    target_fps = source_fps * multiplier
    out = Path(output_dir) / f"{src.stem}_RIFE_{target_fps:g}fps.mp4"
    work = Path(tempfile.mkdtemp(prefix="mords_rife_"))
    frames_in, frames_out = work/"input", work/"output"
    frames_in.mkdir(); frames_out.mkdir()
    try:
        # Decode sequentially to lossless PNG frames.
        subprocess.run([ffmpeg, "-y", "-i", str(src), "-map", "0:v:0", "-vsync", "0",
                        str(frames_in/"%08d.png")], check=True, capture_output=True)
        # RIFE NCNN Vulkan CLI interpolates image sequences.
        cmd = [str(rife_exe), "-i", str(frames_in), "-o", str(frames_out), "-n", str(multiplier)]
        subprocess.run(cmd, check=True, capture_output=True)
        # Encode interpolated frames and remux original audio. Audio is stream-copied;
        # duration may need trimming/padding for unusual source timing.
        subprocess.run([ffmpeg, "-y", "-framerate", str(target_fps), "-i", str(frames_out/"%08d.png"),
                        "-i", str(src), "-map", "0:v:0", "-map", "1:a?", "-c:v", "libx264",
                        "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                        "-c:a", "copy", "-shortest", str(out)], check=True, capture_output=True)
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)
