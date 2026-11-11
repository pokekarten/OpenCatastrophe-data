# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
"""Deterministic, entirely offline checks for the three bounded DLR WMS previews."""
from __future__ import annotations

import hashlib
import struct
import unittest
import zlib

from scripts.probe_dlr_wsf_wms_preview_v0 import (
    LAYER_BY_SOURCE, NoRedirect, WSFPreviewBlocked, frozen_url, inspect_png,
)

def chunk(kind: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + kind + payload +
            struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff))


def synthetic_png(width: int = 32, height: int = 32, inflated: bytes | None = None) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels = inflated if inflated is not None else (
        (b"\x00" + b"\x40\x80\xc0" * width) * height
    )
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


class BoundedWSFPreviewTests(unittest.TestCase):
    def test_exact_source_allowlist_and_no_caller_selected_url(self):
        self.assertEqual(set(LAYER_BY_SOURCE), {
            "dlr.wsf.2019",
            "dlr.eoc.wsf-tracker.2016-2026",
            "dlr.wsf.evolution.1985-2015",
            "dlr.wsf.3d.v02.building-area",
            "dlr.wsf.3d.v02.building-volume",
            "dlr.wsf.3d.v02.building-fraction",
            "dlr.wsf.3d.v02.building-height",
        })
        for source, layer in LAYER_BY_SOURCE.items():
            target = frozen_url(source)
            self.assertTrue(target.startswith("https://geoservice.dlr.de/eoc/land/wms?"))
            self.assertIn("LAYERS=" + layer, target)
            self.assertIn("WIDTH=32", target)
            self.assertIn("HEIGHT=32", target)
            self.assertIn("11.52%2C48.10%2C11.60%2C48.18", target)
        for untrusted in ("dlr.wsf.2019?BBOX=0,0,1,1", "../etc/passwd", "",
                          "https://example.com/wms"):
            with self.assertRaises(WSFPreviewBlocked):
                frozen_url(untrusted)

    def test_four_3d_layers_are_explicit_and_no_caller_substitution(self):
        names = {k: v for k, v in LAYER_BY_SOURCE.items()
                 if k.startswith("dlr.wsf.3d.v02.")}
        self.assertEqual(set(names.values()), {
            "WSF3D_V02_BUILDINGAREA",
            "WSF3D_V02_BUILDINGVOLUME",
            "WSF3D_V02_BUILDINGFRACTION",
            "WSF3D_V02_BUILDINGHEIGHT",
        })
        for name, layer in names.items():
            self.assertIn("LAYERS=" + layer, frozen_url(name))
        for name in ("dlr.wsf.3d.v02", "dlr.wsf.3d.v02.other-layer"):
            with self.assertRaises(WSFPreviewBlocked):
                frozen_url(name)

    def test_accepts_small_complete_png_and_cryptographic_receipt(self):
        raw = synthetic_png()
        receipt = inspect_png(raw, "image/png; charset=binary")
        self.assertEqual((receipt["width"], receipt["height"]), (32, 32))
        self.assertEqual(receipt["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertFalse(receipt["native_raster_values_verified"])
        self.assertFalse(receipt["model_input_approved"])
        self.assertTrue(receipt["rendered_preview_only"])

    def test_rejects_service_exception_media_and_corruption(self):
        raw = synthetic_png()
        for bad, media in [
            (b"<ServiceExceptionReport>denied</ServiceExceptionReport>", "text/xml"),
            (raw, "application/xml"),
            (raw[:-6], "image/png"),
            (raw + b"outside", "image/png"),
            (raw[:46] + b"\x00" + raw[47:], "image/png"),
            (synthetic_png(width=31), "image/png"),
        ]:
            with self.subTest(media=media, size=len(bad)):
                with self.assertRaises(WSFPreviewBlocked):
                    inspect_png(bad, media)

    def test_rejects_png_bomb_and_oversized_transport(self):
        with self.assertRaises(WSFPreviewBlocked):
            inspect_png(synthetic_png(inflated=b"Z" * 80_000), "image/png")
        with self.assertRaises(WSFPreviewBlocked):
            inspect_png(b"x" * 16385, "image/png")

    def test_redirect_never_permitted(self):
        with self.assertRaises(WSFPreviewBlocked):
            NoRedirect().redirect_request(None, None, 302, "move", {}, "https://elsewhere/")

if __name__ == "__main__":
    unittest.main()
