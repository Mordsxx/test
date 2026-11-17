import json, subprocess, shutil
from pathlib import Path

def _ffprobe():
    p = shutil.which("ffprobe")
    if not p:
        raise RuntimeError("ffprobe was not found. Install FFmpeg and add its bin folder to PATH.")
    return p

def analyze_video(path):
    cmd = [_ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    fps = video.get("avg_frame_rate") or video.get("r_frame_rate") or "Unknown"
    if isinstance(fps, str) and "/" in fps:
        a,b = fps.split("/",1)
        try: fps = round(float(a)/float(b), 3)
        except Exception: pass
    duration = video.get("duration") or data.get("format", {}).get("duration", "Unknown")
    try: duration = round(float(duration), 3)
    except Exception: pass
    return {
        "resolution": f"{video.get('width','?')}x{video.get('height','?')}",
        "fps": fps,
        "duration": duration,
        "video_codec": video.get("codec_name", "Unknown"),
        "audio_codec": audio.get("codec_name", "None"),
        "frames": video.get("nb_frames", "Unknown"),
        "video_stream": video,
        "audio_stream": audio
    }
