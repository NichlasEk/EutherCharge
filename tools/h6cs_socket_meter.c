/* SPDX-License-Identifier: GPL-3.0-or-later
 * Empty-socket diagnostic adapted from minipro tl866a_hardware_check.
 * Fixed pins only; no chip commands, firmware changes or arbitrary voltages.
 */
#include <stdio.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include <libusb.h>
#include "minipro.h"
#include "usb.h"
static volatile sig_atomic_t stop;
static void on_signal(int sig) { (void)sig; stop = 1; }
static int send_command(minipro_handle_t *h, uint8_t *data, size_t size,
                        const char *stage) {
    fprintf(stderr, "SEND %s: opcode=%02X bytes=%zu\n", stage, data[0], size);
    int rc = msg_send(h->usb_handle, data, size);
    fprintf(stderr, "%s: %s (USB transfer only)\n", stage, rc ? "FAILED" : "sent");
    return rc;
}
static int read_status(minipro_handle_t *h, uint8_t reply[64]) {
    int received = 0;
    memset(reply, 0, 64);
    int rc = libusb_bulk_transfer(h->usb_handle, 0x81, reply, 64, &received, 1000);
    /* Seven header bytes and all forty ZIF states are required. */
    if (rc || received < 47) {
        fprintf(stderr, "Status receive failed: USB=%d bytes=%d (need >=47)\n", rc, received);
        return 1;
    }
    return 0;
}
static int select_voltage(minipro_handle_t *h, uint8_t data[9], const char *stage) {
    if (send_command(h, data, 9, stage)) return 1;
    /* Public stock firmware: D6 queues a seven-byte response. Leaving it
     * unread can block the next response and prevent further OUT processing.
     * Read a full endpoint packet, then validate actual response length. */
    uint8_t reply[64] = {0};
    int received = 0;
    int rc = libusb_bulk_transfer(h->usb_handle, 0x81, reply, sizeof reply,
                                  &received, 1000);
    fprintf(stderr, "D6 reply: USB=%d bytes=%d opcode=%02X status=%02X\n",
            rc, received, reply[0], reply[1]);
    if (rc || received != 7 || reply[0] != 0xD6 || reply[1] != 0) {
        fprintf(stderr, "D6 reply invalid or reports a fault; stopping.\n");
        return 1;
    }
    return 0;
}
int main(int argc, char **argv) {
    /* D6 is reverse-engineered, not a calibrated voltage API.
     * https://gist.github.com/radiomanV/69ef14c704325bfa58339f2ae73a900f
     * Code 0 is only a candidate for the lowest VCC setting; measure it.
     */
    int cycle = argc == 3 && !strcmp(argv[2], "--voltage-cycle");
    int no_poll = argc == 3 && !strcmp(argv[2], "--vcc-code-0-no-poll");
    int after = no_poll || (argc == 3 && !strcmp(argv[2], "--vcc-code-0-after-routing"));
    int vcc0 = cycle || after || (argc == 3 && !strcmp(argv[2], "--vcc-code-0"));
    if ((argc != 2 && !vcc0) || strcmp(argv[1], "--empty-socket")) {
        puts("No USB access. Usage: socket_meter --empty-socket [--vcc-code-0 | --vcc-code-0-after-routing | --vcc-code-0-no-poll | --voltage-cycle]\n"
             "ZIF 1=VCC, ZIF 40=VPP, ZIF 16=GND. Timer attempts shutdown; NOT a guaranteed cutoff.\n"
             "Default: measured 4.47V / 9.8V. --vcc-code-0: experimental VCC only, VPP disabled.");
        return 2;
    }
    signal(SIGINT, on_signal); signal(SIGTERM, on_signal);
    signal(SIGHUP, on_signal); signal(SIGALRM, on_signal);
    minipro_handle_t *h = minipro_open(0);
    if (!h) { fprintf(stderr, "Could not open programmer; no pin commands sent.\n"); return 1; }
    if (h->version != MP_TL866A || strcmp(h->firmware_str,"03.2.86") ||
        h->status != MP_STATUS_NORMAL) {
        fprintf(stderr,"Unsupported programmer/firmware or non-normal mode; no pin commands sent.\n");
        minipro_close(h); return 1;
    }
    uint8_t reset[10] = {0xD0}, end[4] = {0x04};
    /* Eight latches: VPP40, VCC1 and GND16 only. Values from minipro map. */
    uint8_t latch[25] = {0xD1,0,0,0,0,0,0,8,3,
                        0,0, 1,0x10, 2,0x7F, 3,0xFF,
                        4,0xFF, 5,0, 6,0, 7,0x40};
    uint8_t query[18] = {0xD2}, reply[64];
    int rc = 1;
    /* Firmware selection and socket routing are separate operations. */
    uint8_t select[9] = {0xD6,0,0,0,0,0,0,1,0};
    if (vcc0) { latch[8] = 2; latch[12] = 0; }
    alarm(cycle ? 10 : no_poll ? 45 : 120);
    if (send_command(h,reset,sizeof reset,"initial reset")) goto cleanup;
    if (stop) goto cleanup;
    if (cycle) {
        /* Only previously exercised settings. VPP remains disconnected.
         * D1 baseline followed by D6 code0, twice; no D2 polling. */
        for (int step = 0; step < 4; ++step) {
            if (stop) goto cleanup;
            int failed = step % 2
                ? select_voltage(h,select,"cycle D6 code0")
                : send_command(h,latch,sizeof latch,"cycle D1 baseline");
            if (failed) goto cleanup;
            for (int tick = 0; tick < 10 && !stop; ++tick) usleep(100000);
        }
        if (!stop) rc = 0;
        goto cleanup;
    }
    if (vcc0 && !after && select_voltage(h,select,"D6 before routing")) goto cleanup;
    if (stop) goto cleanup;
    if (send_command(h,latch,sizeof latch,"D1 routing")) goto cleanup;
    if (stop) goto cleanup;
    if (after && select_voltage(h,select,"D6 after routing")) goto cleanup;
    puts(no_poll ? "ACTIVE: ZIF1 VCC code 0, ZIF16 GND, VPP disconnected. NO status/overcurrent polling. Shutdown attempted after 45s."
         : vcc0 ? "ACTIVE: ZIF1 VCC code 0 (voltage UNVERIFIED), ZIF16 GND, VPP disconnected. Shutdown attempted after 120s."
              : "ACTIVE: ZIF1 VCC, ZIF40 VPP, ZIF16 GND. Shutdown attempted after 120s.");
    fflush(stdout);
    while (!stop) {
        /* Empty-socket experiment only: isolate D6 from subsequent D2 traffic. */
        if (no_poll) { usleep(100000); continue; }
        if (msg_send(h->usb_handle,query,sizeof query) ||
            read_status(h,reply)) goto cleanup;
        if (reply[1]) { fprintf(stderr,"Overcurrent: shutting down.\n"); goto cleanup; }
        usleep(100000);
    }
    rc = 0;
cleanup:
    alarm(0);
    int reset_failed = send_command(h,reset,sizeof reset,"shutdown reset");
    int end_failed = send_command(h,end,sizeof end,"shutdown end");
    if (reset_failed || end_failed) {
        fprintf(stderr,"Shutdown not confirmed: unplug USB.\n"); rc=1;
    } else puts("SHUTDOWN COMMANDS SENT: socket voltage unknown; verify with meter.");
    minipro_close(h);
    return rc;
}
