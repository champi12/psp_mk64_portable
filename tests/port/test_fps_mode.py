#!/usr/bin/env python3
"""Run the production PSP gesture and frame policy against a simulated pad/clock.

No PSP SDK required. Each case starts a fresh process and temporary save folder.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_mirror_collision import function

ROOT = Path(__file__).resolve().parents[2]


def harness_source():
    main = (ROOT / "src/main.c").read_text()
    controller = (ROOT / "src/port/psp/controller_psp.c").read_text()
    code = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <sys/stat.h>
typedef int8_t s8; typedef int32_t s32;
typedef uint16_t u16; typedef uint32_t u32;
typedef struct { u16 button; s8 stick_x, stick_y; unsigned char errno; } OSContPad;
typedef struct { u32 Buttons; unsigned char Lx, Ly; } SceCtrlData;
enum { PSP_CTRL_SELECT=1, PSP_CTRL_START=8, PSP_CTRL_UP=16,
 PSP_CTRL_RIGHT=32, PSP_CTRL_DOWN=64, PSP_CTRL_LEFT=128,
 PSP_CTRL_LTRIGGER=256, PSP_CTRL_RTRIGGER=512, PSP_CTRL_TRIANGLE=4096,
 PSP_CTRL_CIRCLE=8192, PSP_CTRL_CROSS=16384, PSP_CTRL_SQUARE=32768 };
enum { A_BUTTON=0x8000, B_BUTTON=0x4000, Z_TRIG=0x2000, START_BUTTON=0x1000,
 U_JPAD=0x800, D_JPAD=0x400, L_JPAD=0x200, R_JPAD=0x100,
 L_TRIG=0x20, R_TRIG=0x10, U_CBUTTONS=8, R_CBUTTONS=1 };
#define PSP_CTRL_MODE_ANALOG 1
#define STICK_DEADZONE 20
#define RACING 4
#define START_MENU_FROM_QUIT 7
#define SCREEN_MODE_1P 0
#define PORT_NET 1
#define PORT_LOG(...) ((void)0)
static int gPortShowFps, gGamestate=RACING, gActiveScreenMode=SCREEN_MODE_1P;
static int gIsGamePaused, gIsInQuitToMenuTransition, network;
static int notices, noticeClassic, noticeSaved;
static u32 clockNow;
static SceCtrlData raw = {0,128,128};
static const u32 BOTH = PSP_CTRL_START | PSP_CTRL_SELECT;
static int port_net_active(void) { return network; }
static const char* port_save_path(const char* name) { return name; }
static void port_gfx_show_fps_mode(s32 classic, s32 saved) {
 notices++; noticeClassic=classic; noticeSaved=saved;
}
static u32 sceKernelGetSystemTimeLow(void) { return clockNow; }
static void sceCtrlPeekBufferPositive(SceCtrlData* d, int n) { *d=raw; }
'''
    for name in ("sPortClassicMode", "sPortSplitHoldoff"):
        start = main.index("static s32 " + name)
        code += main[start:main.index(";", start) + 1] + "\n"
    for signature in ("void port_fps_mode_init(", "void port_toggle_fps_mode(",
                      "static s32 port_frame_can_split("):
        code += function(main, signature) + "\n"
    for signature in ("static s8 map_axis(", "void controller_psp_read("):
        code += function(controller, signature) + "\n"
    code += r'''
static void sample(u32 t, u32 buttons, u16 expected) {
 OSContPad pad={0}; clockNow=t; raw.Buttons=buttons; controller_psp_read(&pad);
 if (pad.button!=expected) fprintf(stderr,"time=%u buttons=%x got=%x expected=%x\n",t,buttons,pad.button,expected);
 assert(pad.button==expected); assert(pad.errno==0);
}
static void file_is(const char* expected) {
 char buf[32]={0}; FILE* f=fopen("fps_mode.txt","rb"); assert(f);
 size_t n=fread(buf,1,sizeof(buf)-1,f); fclose(f);
 assert(n==strlen(expected)); assert(strcmp(buf,expected)==0);
}
int main(int argc, char** argv) {
 assert(argc==2); const char* test=argv[1];
 port_fps_mode_init(); assert(port_frame_can_split());
 if (!strcmp(test,"threshold")) {
  sample(0,BOTH,0); sample(999999,BOTH,0); assert(notices==0);
  sample(1000000,BOTH,0); assert(notices==1 && noticeClassic && noticeSaved);
  assert(!port_frame_can_split()); file_is("classic\n");
  sample(9000000,BOTH,0); assert(notices==1 && !gPortShowFps);
  sample(9100000,0,0); sample(9200000,BOTH,0); sample(10200000,BOTH,0);
  assert(notices==2 && !noticeClassic && port_frame_can_split()); file_is("performance\n");
 } else if (!strcmp(test,"start_first") || !strcmp(test,"select_first")) {
  u32 first=!strcmp(test,"start_first") ? PSP_CTRL_START : PSP_CTRL_SELECT;
  u32 last=BOTH ^ first;
  sample(100,first,0); sample(100000,first,0); sample(200000,BOTH,0);
  sample(1200000,BOTH,0); assert(notices==1);
  sample(1300000,last,0); sample(6000000,last,0); // no pause, HUD, or FPS toggle
  sample(6100000,BOTH,0); sample(7500000,BOTH,0); assert(notices==1);
  sample(7600000,0,0); assert(!gPortShowFps);
  sample(7700000,PSP_CTRL_START,0); sample(7800000,0,START_BUTTON);
  sample(7900000,0,0);
 } else if (!strcmp(test,"interrupted")) {
  sample(10,BOTH,0); sample(500010,PSP_CTRL_START,0);
  sample(700010,BOTH,0); sample(1200010,BOTH,0); assert(notices==0);
  sample(1700010,BOTH,0); assert(notices==1);
  sample(1800010,0,0);
 } else if (!strcmp(test,"short_chord")) {
  sample(100,BOTH,0); sample(100100,0,0); assert(notices==0);
  sample(200100,PSP_CTRL_SELECT,0); sample(300100,0,R_CBUTTONS);
  sample(400100,0,0);
 } else if (!strcmp(test,"select_gestures")) {
  sample(0,PSP_CTRL_SELECT,0); sample(100000,0,R_CBUTTONS); sample(100001,0,0);
  sample(200000,PSP_CTRL_SELECT,0); sample(900000,0,0);
  sample(1000000,PSP_CTRL_SELECT,0); sample(3999999,PSP_CTRL_SELECT,0); assert(!gPortShowFps);
  sample(4000000,PSP_CTRL_SELECT,0); assert(gPortShowFps);
  sample(8000000,PSP_CTRL_SELECT,0); assert(gPortShowFps); sample(8100000,0,0);
  sample(8200000,BOTH,0); sample(9200000,BOTH,0); sample(9300000,0,0);
  assert(gPortShowFps && notices==1);
 } else if (!strcmp(test,"wrap")) {
  u32 start=UINT32_MAX-500000;
  sample(start,BOTH,0); sample(start+999999u,BOTH,0); assert(!notices);
  sample(start+1000000u,BOTH,0); assert(notices==1); sample(start+1100000u,0,0);
 } else if (!strcmp(test,"other_controls")) {
  sample(0,BOTH|PSP_CTRL_CROSS|PSP_CTRL_RTRIGGER,A_BUTTON|R_TRIG);
  sample(1000000,BOTH|PSP_CTRL_CROSS,A_BUTTON); assert(notices==1);
  sample(1100000,PSP_CTRL_SQUARE|PSP_CTRL_CIRCLE,B_BUTTON|Z_TRIG);
 } else if (!strcmp(test,"policy")) {
  network=1; assert(!port_frame_can_split()); network=0;
  for(int i=1;i<=3;i++) {gActiveScreenMode=i; assert(!port_frame_can_split());}
  gActiveScreenMode=SCREEN_MODE_1P;
  gGamestate=START_MENU_FROM_QUIT; assert(!port_frame_can_split()); gGamestate=RACING;
  gIsGamePaused=1; assert(!port_frame_can_split()); gIsGamePaused=0;
  gIsInQuitToMenuTransition=1; assert(!port_frame_can_split()); gIsInQuitToMenuTransition=0;
  sPortSplitHoldoff=100; assert(!port_frame_can_split());
  port_toggle_fps_mode(); assert(!port_frame_can_split());
  sPortSplitHoldoff=0; assert(!port_frame_can_split());
  port_toggle_fps_mode(); assert(port_frame_can_split());
  network=1; port_toggle_fps_mode(); port_toggle_fps_mode(); assert(!port_frame_can_split());
 } else if (!strcmp(test,"persistence")) {
  port_toggle_fps_mode(); port_fps_mode_init(); assert(!port_frame_can_split()); file_is("classic\n");
  port_toggle_fps_mode(); port_fps_mode_init(); assert(port_frame_can_split()); file_is("performance\n");
  FILE* f=fopen("fps_mode.txt","wb"); fputs("clas",f); fclose(f);
  port_fps_mode_init(); assert(port_frame_can_split());
 } else if (!strcmp(test,"save_failure")) {
  assert(mkdir("fps_mode.txt",0700)==0);
  port_toggle_fps_mode(); assert(noticeClassic && !noticeSaved);
  assert(!port_frame_can_split());
 } else assert(!"unknown case");
 return 0;
}
'''
    return code


class FpsModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = tempfile.TemporaryDirectory(prefix="mk64-fps-mode-")
        source = Path(cls.build.name) / "harness.c"
        source.write_text(harness_source())
        cls.binary = Path(cls.build.name) / "test"
        subprocess.run([os.environ.get("CC", "clang"), "-std=c99", "-Wall", "-Werror",
                        str(source), "-o", str(cls.binary)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.build.cleanup()

    def test_gestures_policy_and_saved_preference(self):
        for case in ("threshold", "start_first", "select_first", "interrupted",
                     "short_chord", "select_gestures", "wrap", "other_controls",
                     "policy", "persistence", "save_failure"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as save_dir:
                subprocess.run([str(self.binary), case], cwd=save_dir, check=True)


if __name__ == "__main__":
    unittest.main()
