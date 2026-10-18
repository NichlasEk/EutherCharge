from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "fwtool.py"


class FirmwareToolTests(unittest.TestCase):
    def run_tool(self, *args: object) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), *(str(arg) for arg in args)],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_compare_identical_and_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.bin"
            second = root / "second.bin"
            third = root / "third.bin"
            first.write_bytes(b"same")
            second.write_bytes(b"same")
            third.write_bytes(b"sand")

            result = self.run_tool("compare", first, second)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("byte-identical", result.stdout)

            result = self.run_tool("compare", first, third)
            self.assertEqual(result.returncode, 1)
            self.assertIn("0x2", result.stderr)

    def test_patch_is_guarded_and_manifested(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            output = root / "output.bin"
            source.write_bytes(bytes.fromhex("001122334455"))

            result = self.run_tool("patch", source, output, "--patch", "0x2:2233:aabb")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes(), bytes.fromhex("0011aabb4455"))
            manifest = json.loads(Path(str(output) + ".manifest.json").read_text())
            self.assertEqual(manifest["patches"][0]["offset"], 2)
            self.assertNotEqual(manifest["source"]["sha256"], manifest["output"]["sha256"])

            rejected = self.run_tool(
                "patch", source, root / "bad.bin", "--patch", "0x2:ffff:aabb"
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("guard failed", rejected.stderr)

    def test_inspect_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "image.bin"
            image.write_bytes(b"\xff\xffHELLO-WORLD\x00")
            result = self.run_tool("inspect", image, "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["size_bytes"], 14)
            self.assertEqual(report["edge_runs"]["leading_ff"], 2)
            self.assertEqual(report["strings"][0]["text"], "HELLO-WORLD")

    def test_identify_candidate(self) -> None:
        result = self.run_tool("identify", "9d:00:46")
        self.assertEqual(result.returncode, 1)
        result = self.run_tool("identify", "9d0046")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PM25LQ032C", result.stdout)

        measured = self.run_tool("identify", "1c3016")
        self.assertEqual(measured.returncode, 0, measured.stderr)
        self.assertIn("Eon EN25Q32(A/B)", measured.stdout)


if __name__ == "__main__":
    unittest.main()
