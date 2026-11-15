# SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import tempfile
import unittest
from research_runners.validate_downloaded_wind_sources import validate

class IntegrityTest(unittest.TestCase):
    def test_changed_original_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'original').write_bytes(b'changed')
            (p/'receipt.json').write_text(json.dumps([{'status':'downloaded','file':'original','bytes':7,'sha256':'0'*64}]))
            (p/'xws-receipt.json').write_text('[]')
            with self.assertRaisesRegex(ValueError,'integrity'):validate(p)
    def test_failed_download_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'receipt.json').write_text('[{"status":"failed"}]')
            with self.assertRaisesRegex(ValueError,'Failed'):validate(p)
