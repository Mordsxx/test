from pathlib import Path
from fractions import Fraction
import shutil, subprocess, os
from .mp4_parser import parse_boxes, CONTAINERS

def _scale_uint(buf, pos, width, factor, label):
    old = int.from_bytes(buf[pos:pos+width], "big")
    new = old * factor.numerator
    if new % factor.denominator:
        new = (new + factor.denominator//2) // factor.denominator
    if new >= 1 << (8*width):
        raise ValueError(f"{label} overflows its MP4 field; refusing to patch.")
    buf[pos:pos+width] = int(new).to_bytes(width, "big")

def _scale_signed(buf, pos, width, factor, label):
    old = int.from_bytes(buf[pos:pos+width], "big", signed=True)
    new = old * factor.numerator
    if new % factor.denominator:
        new = (new + factor.denominator//2) // factor.denominator
    lo, hi = -(1 << (8*width-1)), (1 << (8*width-1))-1
    if not lo <= new <= hi: raise ValueError(f"{label} overflows its MP4 field.")
    buf[pos:pos+width] = int(new).to_bytes(width, "big", signed=True)

def _patch_box(buf, box, factor):
    p = box.start + box.header
    kind = box.kind
    if kind in CONTAINERS:
        for child in parse_boxes(buf, p, box.end):
            _patch_box(buf, child, factor)
        return
    if kind in (b"mvhd", b"mdhd", b"tkhd"):
        version = buf[p]
        if version == 0:
            duration_pos = p + (20 if kind == b"tkhd" else 16)
            _scale_uint(buf, duration_pos, 4, factor, kind.decode()+" duration")
        elif version == 1:
            duration_pos = p + (28 if kind == b"tkhd" else 24)
            _scale_uint(buf, duration_pos, 8, factor, kind.decode()+" duration")
        else:
            raise ValueError(f"Unsupported {kind.decode()} version {version}")
    elif kind == b"stts":
        count = int.from_bytes(buf[p+4:p+8], "big")
        cursor = p+8
        if cursor + count*8 > box.end: raise ValueError("Malformed stts table")
        for _ in range(count):
            _scale_uint(buf, cursor+4, 4, factor, "stts sample_delta")
            cursor += 8
    elif kind == b"ctts":
        version = buf[p]
        count = int.from_bytes(buf[p+4:p+8], "big")
        cursor = p+8
        if cursor + count*8 > box.end: raise ValueError("Malformed ctts table")
        for _ in range(count):
            if version == 0: _scale_uint(buf, cursor+4, 4, factor, "ctts offset")
            elif version == 1: _scale_signed(buf, cursor+4, 4, factor, "ctts offset")
            else: raise ValueError("Unsupported ctts version")
            cursor += 8
    elif kind == b"elst":
        version = buf[p]
        count = int.from_bytes(buf[p+4:p+8], "big")
        cursor = p+8
        for _ in range(count):
            if version == 0:
                _scale_uint(buf, cursor, 4, factor, "elst segment_duration")
                _scale_signed(buf, cursor+4, 4, factor, "elst media_time")
                cursor += 12
            elif version == 1:
                _scale_uint(buf, cursor, 8, factor, "elst segment_duration")
                _scale_signed(buf, cursor+8, 8, factor, "elst media_time")
                cursor += 20
            else: raise ValueError("Unsupported elst version")
        if cursor > box.end: raise ValueError("Malformed elst table")

def _scan_top_level(path):
    boxes = []
    size = path.stat().st_size
    with path.open("rb") as f:
        pos = 0
        while pos < size:
            f.seek(pos)
            header = f.read(8)
            if len(header) != 8: raise ValueError("Truncated top-level MP4 box.")
            box_size = int.from_bytes(header[:4], "big")
            kind = header[4:8]
            header_size = 8
            if box_size == 1:
                ext = f.read(8)
                if len(ext) != 8: raise ValueError("Truncated extended MP4 box.")
                box_size = int.from_bytes(ext, "big")
                header_size = 16
            elif box_size == 0:
                box_size = size - pos
            if box_size < header_size or pos + box_size > size:
                raise ValueError(f"Invalid top-level {kind!r} box size.")
            boxes.append((kind, pos, box_size, header_size))
            pos += box_size
    return boxes

def _copy_range(src, dst, start, length, chunk=8*1024*1024):
    src.seek(start)
    remaining = length
    while remaining:
        data = src.read(min(chunk, remaining))
        if not data: raise IOError("Unexpected end of input while copying MP4.")
        dst.write(data)
        remaining -= len(data)

def patch_mp4_timing(input_path, output_path, multiplier=2):
    factor = Fraction(multiplier, 1)
    if multiplier < 2: raise ValueError("Slowdown multiplier must be at least 2.")
    src, dst = Path(input_path), Path(output_path)
    if src.resolve() == dst.resolve(): raise ValueError("Output must not overwrite the original file.")
    top = _scan_top_level(src)
    if any(kind == b"moof" for kind, *_ in top):
        raise ValueError("Fragmented MP4 is not supported by this patch engine.")
    moov_info = next((item for item in top if item[0] == b"moov"), None)
    if not moov_info: raise ValueError("No moov box found in this MP4.")
    _, moov_offset, moov_size, _ = moov_info
    with src.open("rb") as f:
        f.seek(moov_offset)
        moov_data = bytearray(f.read(moov_size))
    # Reject fragmented movie metadata.
    moov_boxes = parse_boxes(moov_data, 0, len(moov_data))
    if any(b.kind == b"mvex" for b in moov_boxes):
        raise ValueError("Fragmented MP4 (mvex) is not supported.")
    for child in moov_boxes:
        _patch_box(moov_data, child, factor)
    dst.parent.mkdir(parents=True, exist_ok=True)
    temp = dst.with_suffix(dst.suffix + ".tmp")
    try:
        with src.open("rb") as fin, temp.open("wb") as fout:
            _copy_range(fin, fout, 0, moov_offset)
            fout.write(moov_data)
            tail_start = moov_offset + moov_size
            _copy_range(fin, fout, tail_start, src.stat().st_size - tail_start)
        os.replace(temp, dst)
        _validate_with_ffprobe(dst)
    except Exception:
        try: temp.unlink()
        except OSError: pass
        try: dst.unlink()
        except OSError: pass
        raise
    return dst

def _validate_with_ffprobe(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe: return
    cmd = [ffprobe, "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,duration,avg_frame_rate,nb_frames", "-of", "default=noprint_wrappers=1", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("FFprobe rejected the patched MP4.")
