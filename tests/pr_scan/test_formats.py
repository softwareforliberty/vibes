"""The binary format checks and the escaping."""

from __future__ import annotations

import os
import struct
import unittest

from support import chunk, png

from pr_scan import binfmt
from pr_scan.escape import ascii_only, visible
from pr_scan.rules.gitlevel import _path


def gif(trailer: bytes = b"") -> bytes:
    image = (b"\x2c" + struct.pack("<HHHHB", 0, 0, 1, 1, 0) + b"\x02"
             + b"\x02\x4c\x01\x00")
    return (b"GIF89a" + struct.pack("<HHBBB", 1, 1, 0x80, 0, 0) + b"\0" * 6
            + image + b"\x3b" + trailer)


def jpeg(trailer: bytes = b"") -> bytes:
    return (b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\0"
            + b"\0" * 9 + b"\xff\xda" + struct.pack(">H", 8) + b"\0" * 6
            + b"\x12\x34\xff\x00\x56" + b"\xff\xd9" + trailer)


class FormatsTest(unittest.TestCase):
    def test_clean_images_have_no_anomalies(self) -> None:
        for name, data, extension in (("png", png(), "png"),
                                      ("gif", gif(), "gif"),
                                      ("jpeg", jpeg(), "jpg")):
            with self.subTest(name):
                self.assertEqual(binfmt.describe(data, extension).anomalies,
                                 [])

    def test_trailing_data_is_found(self) -> None:
        for name, data, extension in (("png", png(extra=b"x" * 10), "png"),
                                      ("gif", gif(b"x" * 10), "gif"),
                                      ("jpeg", jpeg(b"x" * 10), "jpg")):
            with self.subTest(name):
                anomalies = binfmt.describe(data, extension).anomalies
                self.assertTrue(any("after the end" in a for a in anomalies),
                                anomalies)

    def test_bad_crc_and_text_chunks(self) -> None:
        broken = bytearray(png())
        broken[30] ^= 0xFF
        self.assertTrue(any("CRC" in a for a in binfmt.describe(
            bytes(broken), "png").anomalies))
        text = png(chunks=chunk(b"tEXt", b"Comment\0" + b"x" * 2000))
        self.assertTrue(any("text chunks" in a for a in binfmt.describe(
            text, "png").anomalies))

    def test_identify_and_extension_mismatch(self) -> None:
        self.assertEqual(binfmt.identify(b"\xfd7zXZ\x00rest"), "xz")
        self.assertEqual(binfmt.identify(b"\x7fELF\x02"), "elf")
        anomalies = binfmt.describe(b"\x7fELF\x02\x01\x01" + os.urandom(30),
                                    "png").anomalies
        self.assertTrue(any("extension .png" in a for a in anomalies))

    def test_escaping(self) -> None:
        self.assertEqual(visible("a‮b\nc"), "a\\u{202E}b\nc")
        self.assertEqual(visible("café"), "café")
        self.assertEqual(visible("\\u{41}"), "\\u{005C}u{41}")
        self.assertEqual(ascii_only("café\t"), "caf\\u{00E9}\\t")
        self.assertEqual(ascii_only("x" * 10, 6), "xxx...")

    def test_git_lookalike_paths(self) -> None:
        for path in (".GIT/config", ".git./x", "GIT~1/x", ".g‌it/x",
                     "-rf", "a/../b"):
            with self.subTest(path):
                self.assertTrue(list(_path(path)))
        self.assertFalse(list(_path("src/main.c")))


if __name__ == "__main__":
    unittest.main()
