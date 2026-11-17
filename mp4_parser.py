from dataclasses import dataclass

CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}

@dataclass
class Box:
    kind: bytes
    start: int
    header: int
    size: int
    end: int

def parse_boxes(buf, start=0, end=None):
    if end is None: end = len(buf)
    boxes = []
    pos = start
    while pos < end:
        if end - pos < 8: raise ValueError(f"Invalid MP4 box header at offset {pos}")
        size = int.from_bytes(buf[pos:pos+4], "big")
        kind = bytes(buf[pos+4:pos+8])
        header = 8
        if size == 1:
            if end-pos < 16: raise ValueError("Truncated 64-bit MP4 box")
            size = int.from_bytes(buf[pos+8:pos+16], "big"); header = 16
        elif size == 0:
            size = end-pos
        if size < header or pos+size > end:
            raise ValueError(f"Invalid {kind!r} box size at offset {pos}")
        boxes.append(Box(kind, pos, header, size, pos+size))
        pos += size
    if pos != end: raise ValueError("MP4 box boundaries do not align")
    return boxes

def walk(buf, start, end, parent=b""):
    for box in parse_boxes(buf, start, end):
        yield box
        if box.kind in CONTAINERS:
            yield from walk(buf, box.start+box.header, box.end, box.kind)
