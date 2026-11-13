"""Identifies binary files and checks the structure of the common formats.

A binary is described for the reviewers instead of shown to them, since an
image can carry instructions an agent would read. The checks find what
XZ-style payloads rely on: data after the end of an image, chunks that
nothing displays, pixel data larger than the image, and archives or
executables passed off as data.
"""

from __future__ import annotations

import io
import math
import re
import struct
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# (kind, magic, offset); longest magic first where they share a prefix.
MAGIC: Tuple[Tuple[str, bytes, int], ...] = (
    ("png", b"\x89PNG\r\n\x1a\n", 0),
    ("gif", b"GIF87a", 0),
    ("gif", b"GIF89a", 0),
    ("jpeg", b"\xff\xd8\xff", 0),
    ("webp", b"WEBP", 8),
    ("bmp", b"BM", 0),
    ("ico", b"\x00\x00\x01\x00", 0),
    ("pdf", b"%PDF-", 0),
    ("zip", b"PK\x03\x04", 0),
    ("zip", b"PK\x05\x06", 0),
    ("gzip", b"\x1f\x8b", 0),
    ("xz", b"\xfd7zXZ\x00", 0),
    ("bzip2", b"BZh", 0),
    ("zstd", b"\x28\xb5\x2f\xfd", 0),
    ("7z", b"7z\xbc\xaf\x27\x1c", 0),
    ("lz4", b"\x04\x22\x4d\x18", 0),
    ("rar", b"Rar!\x1a\x07", 0),
    ("tar", b"ustar", 257),
    ("cpio", b"070701", 0),
    ("cpio", b"070707", 0),
    ("ar", b"!<arch>\n", 0),
    ("rpm", b"\xed\xab\xee\xdb", 0),
    ("squashfs", b"hsqs", 0),
    ("elf", b"\x7fELF", 0),
    ("macho", b"\xfe\xed\xfa\xce", 0),
    ("macho", b"\xfe\xed\xfa\xcf", 0),
    ("macho", b"\xce\xfa\xed\xfe", 0),
    ("macho", b"\xcf\xfa\xed\xfe", 0),
    ("macho-fat-or-class", b"\xca\xfe\xba\xbe", 0),
    ("pe", b"MZ", 0),
    ("wasm", b"\x00asm", 0),
    ("dex", b"dex\n", 0),
    ("sqlite", b"SQLite format 3\x00", 0),
    ("woff", b"wOFF", 0),
    ("woff2", b"wOF2", 0),
    ("font", b"\x00\x01\x00\x00", 0),
    ("font", b"OTTO", 0),
    ("font", b"true", 0),
    ("font-collection", b"ttcf", 0),
    ("lzma", b"\x5d\x00\x00", 0),
)

# The kinds each extension should hold.
EXTENSIONS = {
    "png": {"png"}, "apng": {"png"}, "gif": {"gif"}, "jpg": {"jpeg"},
    "jpeg": {"jpeg"}, "webp": {"webp"}, "bmp": {"bmp"}, "ico": {"ico", "png"},
    "pdf": {"pdf"}, "zip": {"zip"}, "jar": {"zip"}, "whl": {"zip"},
    "apk": {"zip"}, "docx": {"zip"}, "xlsx": {"zip"}, "odt": {"zip"},
    "gz": {"gzip"}, "tgz": {"gzip"}, "xz": {"xz"}, "txz": {"xz"},
    "bz2": {"bzip2"}, "zst": {"zstd"}, "7z": {"7z"}, "lz4": {"lz4"},
    "rar": {"rar"}, "tar": {"tar"}, "cpio": {"cpio"}, "a": {"ar"},
    "deb": {"ar"}, "rpm": {"rpm"}, "ttf": {"font"}, "otf": {"font"},
    "ttc": {"font-collection"}, "woff": {"woff"}, "woff2": {"woff2"},
    "wasm": {"wasm"}, "class": {"macho-fat-or-class"}, "dex": {"dex"},
    "sqlite": {"sqlite"}, "db": {"sqlite"}, "lzma": {"lzma"},
    "so": {"elf"}, "o": {"elf", "macho"}, "dylib": {"macho"},
    "exe": {"pe"}, "dll": {"pe"},
}

IMAGES = {"png", "gif", "jpeg", "webp", "bmp", "ico"}
FONTS = {"font", "font-collection", "woff", "woff2"}
# Kinds whose contents can't be reviewed: code, archives and compressed data.
OPAQUE = {"elf", "macho", "macho-fat-or-class", "pe", "wasm", "dex", "ar",
          "rpm", "zip", "gzip", "xz", "bzip2", "zstd", "7z", "lz4", "rar",
          "tar", "cpio", "squashfs", "lzma", "sqlite", "pdf"}
# Signatures worth finding anywhere inside another file: long enough not to
# turn up by chance.
EMBEDDED = (("elf", b"\x7fELF\x02\x01\x01"), ("elf", b"\x7fELF\x01\x01\x01"),
            ("xz", b"\xfd7zXZ\x00"), ("7z", b"7z\xbc\xaf\x27\x1c"),
            ("zip", b"PK\x03\x04\x14\x00"), ("png", b"\x89PNG\r\n\x1a\n"),
            ("pdf", b"%PDF-1."), ("pe", b"PE\x00\x00\x4c\x01"),
            ("pe", b"PE\x00\x00\x64\x86"), ("shebang", b"#!/bin/"),
            ("shebang", b"#!/usr/bin/"))
SUSPICIOUS_STRINGS = re.compile(
    rb"/bin/sh|/bin/bash|\beval\b|\bexec\b|base64|\bcurl\b|\bwget\b|"
    rb"LD_PRELOAD|/dev/tcp|\bsystem\(|\bpopen\b|chmod \+x|\bmkfifo\b|"
    rb"\bnc -|/etc/passwd|/etc/shadow|authorized_keys|\bsshd\b")


def identify(data: bytes) -> Optional[str]:
    for kind, magic, offset in MAGIC:
        if data[offset:offset + len(magic)] == magic:
            if kind == "pe" and not _is_pe(data):
                continue
            if kind == "webp" and data[:4] != b"RIFF":
                continue
            return kind
    return None


def _is_pe(data: bytes) -> bool:
    if len(data) < 0x40:
        return False
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    return data[offset:offset + 4] == b"PE\x00\x00"


@dataclass
class Description:
    kind: Optional[str]
    structure: List[str] = field(default_factory=list)
    # Problems that make the file suspicious on their own.
    anomalies: List[str] = field(default_factory=list)
    # Facts a reviewer should weigh, such as text chunks.
    notes: List[str] = field(default_factory=list)


def describe(data: bytes, extension: str) -> Description:
    kind = identify(data)
    result = Description(kind)
    expected = EXTENSIONS.get(extension.lower())
    if expected is not None and kind not in expected:
        result.anomalies.append(
            f"the extension .{extension} should hold {'/'.join(sorted(expected))}"
            f" data, but the file is {kind or 'of no known kind'}")
    checker = {"png": _png, "gif": _gif, "jpeg": _jpeg, "zip": _zip,
               "font": _font}.get(kind or "")
    end = len(data)
    if checker is not None:
        try:
            end = checker(data, result)
        except (struct.error, IndexError, ValueError, zlib.error,
                zipfile.BadZipFile) as error:
            result.anomalies.append(f"malformed {kind}: {error}")
    if end < len(data):
        result.anomalies.append(
            f"{len(data) - end} bytes after the end of the {kind} data, at "
            f"offset {end}")
    for name, magic in EMBEDDED:
        start = data.find(magic, 1)
        if start > 0:
            result.anomalies.append(
                f"a {name} signature inside the file at offset {start}")
    strings = suspicious_strings(data)
    if strings:
        result.anomalies.append(
            "strings that look like commands: " + ", ".join(strings[:5]))
    result.notes.append(f"entropy {entropy(data):.2f} bits per byte")
    return result


def printable_strings(data: bytes, shortest: int = 6) -> List[str]:
    """Runs of printable ASCII, as the strings command finds them."""
    pattern = rb"[\x20-\x7e]{%d,}" % shortest
    return [match.group().decode("ascii")
            for match in re.finditer(pattern, data)]


def suspicious_strings(data: bytes) -> List[str]:
    return [found[:60] for found in printable_strings(data)
            if SUSPICIOUS_STRINGS.search(found.encode("ascii"))]


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    total = len(data)
    return -sum(c / total * math.log2(c / total) for c in counts if c)


PNG_KNOWN = {b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"cHRM", b"gAMA",
             b"iCCP", b"sBIT", b"sRGB", b"cICP", b"mDCV", b"cLLI", b"tEXt",
             b"zTXt", b"iTXt", b"bKGD", b"hIST", b"pHYs", b"sPLT", b"eXIf",
             b"tIME", b"acTL", b"fcTL", b"fdAT"}
PNG_TEXT = {b"tEXt", b"zTXt", b"iTXt"}
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _png(data: bytes, result: Description) -> int:
    offset = 8
    idat = bytearray()
    width = height = depth = colour = interlace = 0
    text_bytes = 0
    seen_end = False
    while offset + 8 <= len(data):
        length, kind = struct.unpack_from(">I4s", data, offset)
        body = data[offset + 8:offset + 8 + length]
        if len(body) < length:
            raise ValueError(f"chunk {kind!r} runs past the end of the file")
        crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            result.anomalies.append(f"chunk {kind!r} has a bad CRC")
        result.structure.append(f"chunk {kind.decode('latin-1')} {length} bytes")
        if kind == b"IHDR":
            width, height, depth, colour, _, _, interlace = struct.unpack(
                ">IIBBBBB", body[:13])
        elif kind == b"IDAT":
            idat += body
        elif kind in PNG_TEXT:
            text_bytes += length
        elif kind not in PNG_KNOWN:
            result.anomalies.append(
                f"chunk {kind!r} of {length} bytes is not a standard chunk")
        offset += 12 + length
        if kind == b"IEND":
            seen_end = True
            break
    if not seen_end:
        result.anomalies.append("no IEND chunk")
    if text_bytes > 1024:
        result.anomalies.append(f"{text_bytes} bytes of text chunks")
    elif text_bytes:
        result.notes.append(f"{text_bytes} bytes of text chunks")
    if width and height and colour in CHANNELS:
        expected = _png_raw_size(width, height, depth * CHANNELS[colour],
                                 interlace)
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(bytes(idat), expected + 1)
        if len(raw) != expected:
            result.anomalies.append(
                f"pixel data is {'more' if len(raw) > expected else 'less'} "
                f"than a {width}x{height} image needs ({expected} bytes)")
        elif decompressor.unused_data or decompressor.unconsumed_tail:
            result.anomalies.append("data after the end of the pixel stream")
        result.structure.insert(0, f"{width}x{height}, {depth}-bit, colour "
                                   f"type {colour}, interlace {interlace}")
    return offset


def _png_raw_size(width: int, height: int, bits: int, interlace: int) -> int:
    def rows(w: int, h: int) -> int:
        return 0 if not w or not h else h * (1 + (w * bits + 7) // 8)

    if not interlace:
        return rows(width, height)
    passes = ((0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4),
              (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2))
    return sum(rows((width - x + dx - 1) // dx, (height - y + dy - 1) // dy)
               for x, y, dx, dy in passes)


def _gif(data: bytes, result: Description) -> int:
    width, height, flags = struct.unpack_from("<HHB", data, 6)
    result.structure.append(f"{width}x{height}")
    offset = 13
    if flags & 0x80:
        offset += 3 * (2 << (flags & 7))

    def skip_blocks(position: int) -> Tuple[int, int]:
        total = 0
        while True:
            size = data[position]
            position += 1
            if size == 0:
                return position, total
            total += size
            position += size

    while offset < len(data):
        marker = data[offset]
        if marker == 0x3B:
            return offset + 1
        if marker == 0x21:
            label = data[offset + 1]
            offset, size = skip_blocks(offset + 2)
            if label == 0xFE:
                result.notes.append(f"comment extension, {size} bytes")
                if size > 256:
                    result.anomalies.append(f"a {size}-byte comment")
            elif label == 0xFF:
                result.notes.append(f"application extension, {size} bytes")
        elif marker == 0x2C:
            local = data[offset + 9]
            offset += 10
            if local & 0x80:
                offset += 3 * (2 << (local & 7))
            offset, _ = skip_blocks(offset + 1)
        else:
            raise ValueError(f"unknown block 0x{marker:02x} at {offset}")
    result.anomalies.append("no GIF trailer")
    return len(data)


def _jpeg(data: bytes, result: Description) -> int:
    offset = 2
    while offset + 2 <= len(data):
        if data[offset] != 0xFF:
            raise ValueError(f"expected a marker at {offset}")
        marker = data[offset + 1]
        if marker == 0xD9:
            return offset + 2
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            offset += 2
            continue
        length = struct.unpack_from(">H", data, offset + 2)[0]
        result.structure.append(f"segment FF{marker:02X} {length} bytes")
        if marker == 0xFE and length > 256:
            result.anomalies.append(f"a {length}-byte comment segment")
        if 0xE2 <= marker <= 0xEF and length > 65000:
            result.notes.append(f"a large APP{marker - 0xE0} segment")
        offset += 2 + length
        if marker == 0xDA:
            # Entropy-coded data runs to the next marker that isn't a stuffed
            # zero byte or a restart marker.
            while offset + 1 < len(data):
                if data[offset] == 0xFF and data[offset + 1] not in (
                        0x00, *range(0xD0, 0xD8)):
                    break
                offset += 1
    result.anomalies.append("no end-of-image marker")
    return len(data)


def _zip(data: bytes, result: Description) -> int:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist()[:50]:
            result.structure.append(
                f"member {info.filename!r} {info.file_size} bytes")
    end = data.rfind(b"PK\x05\x06")
    if end < 0:
        return len(data)
    comment = struct.unpack_from("<H", data, end + 20)[0]
    return end + 22 + comment


def _font(data: bytes, result: Description) -> int:
    count = struct.unpack_from(">H", data, 4)[0]
    end = 12 + 16 * count
    for index in range(count):
        tag, _, offset, length = struct.unpack_from(">4sIII", data,
                                                    12 + 16 * index)
        result.structure.append(f"table {tag.decode('latin-1')} {length} bytes")
        end = max(end, offset + length)
    # Tables are padded to four bytes.
    return min(len(data), (end + 3) & ~3)


def hexdump(data: bytes, start: int = 0) -> List[str]:
    lines = []
    for offset in range(0, len(data), 16):
        row = data[offset:offset + 16]
        text = "".join(chr(b) if 0x20 <= b < 0x7F else "." for b in row)
        lines.append(f"{start + offset:08x}  {row.hex(' '):<47}  {text}")
    return lines
