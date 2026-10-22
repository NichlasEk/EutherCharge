"""Fault-injection tests with fake USB; never link libusb or access hardware."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SocketMeterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        (d / "minipro.h").write_text('''
#include <stdint.h>
#include <stddef.h>
#define MP_TL866A 1
#define MP_STATUS_NORMAL 1
typedef struct { int version, status; char *firmware_str; void *usb_handle; } minipro_handle_t;
minipro_handle_t *minipro_open(uint8_t);
void minipro_close(minipro_handle_t *);
''')
        (d / "usb.h").write_text("int msg_send(void *, uint8_t *, size_t);\n")
        (d / "libusb.h").write_text("int libusb_bulk_transfer(void *, unsigned char, unsigned char *, int, int *, unsigned int);\n")
        (d / "fake.c").write_text('''
#include "minipro.h"
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>
static int calls, last_opcode;
static int val(const char *name) { const char *s=getenv(name); return s ? atoi(s) : 0; }
minipro_handle_t *minipro_open(uint8_t v) {
    (void)v; puts("FAKE OPEN");
    static minipro_handle_t h={1,1,"03.2.86",NULL};
    if (val("BAD_MODE")) h.status=2;
    return &h;
}
void minipro_close(minipro_handle_t *h) { (void)h; puts("FAKE CLOSE"); }
int msg_send(void *h, uint8_t *b, size_t n) {
    (void)h; last_opcode=b[0]; printf("FAKE SEND %02X %zu\\n",b[0],n);
    return ++calls == val("FAIL_SEND");
}
int libusb_bulk_transfer(void *h, unsigned char ep, unsigned char *b,
                         int n, int *received, unsigned int timeout) {
    (void)h; (void)ep; (void)timeout; puts("FAKE READ"); memset(b,0,n);
    *received=val("SHORT_REPLY") ? 1 : last_opcode==0xD6 ? 7 : 47;
    if (last_opcode==0xD6) b[0]=val("BAD_OPCODE") ? 0 : 0xD6;
    if (val("OVERCURRENT")) b[1]=1;
    return val("FAIL_READ") ? -7 : 0;
}
int usleep(unsigned int n) { (void)n; if (!val("NO_ALARM")) raise(SIGALRM); return 0; }
''')
        cls.exe = d / "meter"
        subprocess.run(["gcc", "-std=gnu17", "-Wall", "-Wextra", "-Werror",
                        "-I", str(d), str(ROOT / "tools/h6cs_socket_meter.c"),
                        str(d / "fake.c"), "-o", str(cls.exe)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_meter(self, args, **env):
        return subprocess.run([str(self.exe), *args], capture_output=True,
                              text=True, timeout=3, env={**os.environ, **env})

    def test_invalid_arguments_never_open_usb(self):
        for args in ([], ["--wrong"], ["--empty-socket", "--wrong"]):
            p = self.run_meter(args)
            self.assertEqual(p.returncode, 2)
            self.assertNotIn("FAKE OPEN", p.stdout)

    def test_bootloader_never_gets_pin_commands(self):
        p = self.run_meter(["--empty-socket"], BAD_MODE="1")
        self.assertEqual(p.returncode, 1)
        self.assertNotIn("FAKE SEND", p.stdout)

    def test_short_or_failed_status_aborts_and_cleans_up(self):
        for env in ({"SHORT_REPLY": "1"}, {"FAIL_READ": "1"}, {"OVERCURRENT": "1"}):
            p = self.run_meter(["--empty-socket"], **env)
            self.assertEqual(p.returncode, 1)
            self.assertTrue(p.stdout.endswith("FAKE SEND 04 4\nSHUTDOWN COMMANDS SENT: socket voltage unknown; verify with meter.\nFAKE CLOSE\n"))

    def test_every_send_failure_is_reported_and_both_cleanup_commands_attempted(self):
        args = ["--empty-socket", "--vcc-code-0-no-poll"]
        for index in range(1, 6):
            p = self.run_meter(args, FAIL_SEND=str(index))
            self.assertEqual(p.returncode, 1)
            sends = [s for s in p.stdout.splitlines() if s.startswith("FAKE SEND")]
            self.assertEqual(sends[-2:], ["FAKE SEND D0 10", "FAKE SEND 04 4"])
            if index >= 4:
                self.assertIn("unplug USB", p.stderr)

    def test_no_poll_sequence_and_no_false_off_claim(self):
        p = self.run_meter(["--empty-socket", "--vcc-code-0-no-poll"])
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.count("FAKE READ"), 1)
        self.assertNotIn("OFF:", p.stdout)
        sends = [s for s in p.stdout.splitlines() if s.startswith("FAKE SEND")]
        self.assertEqual(sends, ["FAKE SEND D0 10", "FAKE SEND D1 25",
                                 "FAKE SEND D6 9", "FAKE SEND D0 10", "FAKE SEND 04 4"])

    def test_cycle_order_and_failure_cleanup(self):
        args = ["--empty-socket", "--voltage-cycle"]
        p = self.run_meter(args, NO_ALARM="1")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stdout.count("FAKE READ"), 2)
        sends = [s for s in p.stdout.splitlines() if s.startswith("FAKE SEND")]
        self.assertEqual(sends, ["FAKE SEND D0 10", "FAKE SEND D1 25",
                                 "FAKE SEND D6 9", "FAKE SEND D1 25",
                                 "FAKE SEND D6 9", "FAKE SEND D0 10", "FAKE SEND 04 4"])
        for index in range(1, 8):
            p = self.run_meter(args, NO_ALARM="1", FAIL_SEND=str(index))
            self.assertEqual(p.returncode, 1)
            sends = [s for s in p.stdout.splitlines() if s.startswith("FAKE SEND")]
            self.assertEqual(sends[-2:], ["FAKE SEND D0 10", "FAKE SEND 04 4"])

    def test_d6_reply_errors_abort_before_second_voltage_cycle(self):
        for env in ({"SHORT_REPLY": "1"}, {"FAIL_READ": "1"},
                    {"BAD_OPCODE": "1"}, {"OVERCURRENT": "1"}):
            p = self.run_meter(["--empty-socket", "--voltage-cycle"], NO_ALARM="1", **env)
            self.assertEqual(p.returncode, 1)
            self.assertEqual(p.stdout.count("FAKE SEND D6"), 1)
            sends = [s for s in p.stdout.splitlines() if s.startswith("FAKE SEND")]
            self.assertEqual(sends[-2:], ["FAKE SEND D0 10", "FAKE SEND 04 4"])


if __name__ == "__main__":
    unittest.main()
