import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "h6cs_pdk", Path(__file__).resolve().parents[1] / "tools/h6cs_pdk.py")
pdk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pdk)


class Target(pdk.TraceBus):
    """Independent pin-level observer with predetermined sampled words."""
    def __init__(self, words):
        super().__init__()
        self.bits = iter(int(bit) for w in words for bit in f"{w:014b}")
        self.levels = {13: 0, 14: 0}
        self.clock_data = []
        self.sample_edges = []

    def drive(self, pin, value):
        super().drive(pin, value)
        self.levels[pin] = value
        if pin == 13 and value:
            self.clock_data.append(self.levels[14])

    def sample(self, pin):
        assert pin == 3 and self.levels[13] == 1
        self.sample_edges.append(len(self.clock_data))
        super().sample(pin)
        return next(self.bits)


def number(bits):
    return int("".join(map(str, bits)), 2)


class ProtocolTests(unittest.TestCase):
    def test_wire_frame_address_order_and_word_reconstruction(self):
        bus = Target([0x1234, 0x2A55])
        self.assertEqual(pdk.read_words(bus, "PMC131-S16A", 0x123, 2),
                         [0x1234, 0x2A55])
        self.assertEqual(number(bus.clock_data[:32]), 0x5A5A5A56)
        self.assertEqual(number(bus.clock_data[32:44]), 0x123)
        self.assertEqual(number(bus.clock_data[58:70]), 0x124)
        self.assertEqual(len(bus.clock_data), 32 + 2 * (12 + 14))
        self.assertEqual(bus.sample_edges, list(range(45, 59)) + list(range(71, 85)))
        self.assertEqual([e for e in bus.events if e[0] == "rail"],
                         [["rail", "vpp", 5000], ["rail", "vdd", 3000]])
        self.assertEqual(bus.events[-1], ["safe_off"])
        self.assertNotIn(["mode", 3, "output"], bus.events)

    def test_reject_before_any_io(self):
        for profile, start, count in [("YFC4604-S16A", 0, 1),
                                     ("PMS131-S16", -1, 1),
                                     ("PMS131-S16", 1535, 2),
                                     ("PMS131-S16", 0, 0)]:
            bus = Target([])
            with self.assertRaises(ValueError):
                pdk.read_words(bus, profile, start, count)
            self.assertEqual(bus.events, [])

    def test_cleanup_on_every_active_operation_failure(self):
        reference = pdk.TraceBus()
        pdk.read_words(reference, "PMS131-S16", count=1)
        # Inject failure after every non-cleanup operation, including rail enable.
        for fail_at in range(1, len(reference.events) - 1):
            class Failing(pdk.TraceBus):
                def __getattribute__(self, name):
                    method = super().__getattribute__(name)
                    if name not in ("mode", "drive", "rail", "delay_us", "sample"):
                        return method
                    def wrapped(*args):
                        result = method(*args)
                        if len(self.events) - 1 == fail_at:
                            raise OSError("injected bus failure")
                        return result
                    return wrapped
            bus = Failing()
            with self.assertRaises(OSError):
                pdk.read_words(bus, "PMS131-S16", count=1)
            self.assertEqual(bus.events[-1], ["safe_off"])

    def test_last_address_and_full_word_width(self):
        bus = Target([0x3FFF])
        self.assertEqual(pdk.read_words(bus, "PMS131-S16", 1535, 1), [0x3FFF])
        self.assertEqual(number(bus.clock_data[32:44]), 1535)


class DumpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.paths = [Path(self.tmp.name) / str(i) for i in range(3)]

    def populate(self, words):
        for p in self.paths:
            p.write_bytes(struct.pack("<1536H", *words))

    def test_identical_is_not_firmware_validation(self):
        self.populate(list(range(1536)))
        result = pdk.compare_dumps(self.paths)
        self.assertTrue(result["repeatable_nonuniform_capture"])
        self.assertFalse(result["firmware_validated"])
        self.paths[-1].write_bytes(bytes(3072))
        self.assertFalse(pdk.compare_dumps(self.paths)["byte_identical"])

    def test_uniform_and_upper_bits_and_length(self):
        self.populate([0x3FFF] * 1536)
        self.assertFalse(pdk.compare_dumps(self.paths)["repeatable_nonuniform_capture"])
        self.populate([0xFFFF] * 1536)
        with self.assertRaises(ValueError):
            pdk.compare_dumps(self.paths)
        self.paths[0].write_bytes(b"short")
        with self.assertRaises(ValueError):
            pdk.compare_dumps(self.paths)

    def test_aliases_and_too_few_reads(self):
        self.populate(list(range(1536)))
        with self.assertRaises(ValueError):
            pdk.compare_dumps([self.paths[0]] * 3)
        with self.assertRaises(ValueError):
            pdk.compare_dumps(self.paths[:2])


if __name__ == "__main__":
    unittest.main()
