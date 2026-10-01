/* Minimal IPS patch support: indexes the patch once, then overlays its
 * records on ROM data as it is read. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { uint32_t off, len, fpos; uint8_t rle, val; } IpsRec;

static IpsRec* sRecs;
static uint32_t sCount, sCap;
static FILE* sIps;

static int add_rec(uint32_t off, uint32_t len, uint32_t fpos, int rle, uint8_t val) {
    if (sCount == sCap) {
        uint32_t ncap = sCap ? sCap * 2 : 1024;
        IpsRec* n = (IpsRec*) realloc(sRecs, ncap * sizeof(IpsRec));
        if (n == NULL) return 0;
        sRecs = n;
        sCap = ncap;
    }
    sRecs[sCount].off = off;
    sRecs[sCount].len = len;
    sRecs[sCount].fpos = fpos;
    sRecs[sCount].rle = (uint8_t) rle;
    sRecs[sCount].val = val;
    sCount++;
    return 1;
}

static void ips_close(void) {
    if (sIps) fclose(sIps);
    free(sRecs);
    sIps = NULL;
    sRecs = NULL;
    sCount = 0;
    sCap = 0;
}

static int try_open(const char* path) {
    unsigned char b[5];
    FILE* f = fopen(path, "rb");
    if (f == NULL) return 0;
    if (fread(b, 1, 5, f) != 5 || memcmp(b, "PATCH", 5) != 0) { fclose(f); return 0; }
    sIps = f;
    for (;;) {
        uint32_t off, len;
        if (fread(b, 1, 3, f) != 3) break;
        if (memcmp(b, "EOF", 3) == 0) break;
        off = ((uint32_t) b[0] << 16) | ((uint32_t) b[1] << 8) | b[2];
        if (fread(b, 1, 2, f) != 2) goto bad;
        len = ((uint32_t) b[0] << 8) | b[1];
        if (len == 0) {
            if (fread(b, 1, 3, f) != 3) goto bad;
            len = ((uint32_t) b[0] << 8) | b[1];
            if (!add_rec(off, len, 0, 1, b[2])) goto bad;
        } else {
            long pos = ftell(f);
            if (pos < 0 || fseek(f, (long) len, SEEK_CUR) != 0) goto bad;
            if (!add_rec(off, len, (uint32_t) pos, 0, 0)) goto bad;
        }
    }
    return 1;
bad:
    ips_close();
    return 0;
}

/* Looks for "<rom name>.ips" or "patch.ips" next to the ROM. */
static int ips_open(const char* rom_path) {
    char p[300];
    char* slash;
    char* dot;
    ips_close();
    if (strlen(rom_path) > 280) return 0;
    snprintf(p, sizeof(p), "%s", rom_path);
    slash = strrchr(p, '/');
    dot = strrchr(p, '.');
    if (dot != NULL && (slash == NULL || dot > slash)) {
        strcpy(dot, ".ips");
        if (try_open(p)) return 1;
    }
    if (slash != NULL) strcpy(slash + 1, "patch.ips");
    else strcpy(p, "patch.ips");
    return try_open(p);
}

static int ips_active(void) { return sCount > 0; }

/* Call after reading ROM bytes [off, off+len) into dst (big-endian .z64 order). */
static void ips_overlay(uint32_t off, void* dst, uint32_t len) {
    uint8_t* buf = (uint8_t*) dst;
    uint32_t i;
    for (i = 0; i < sCount; i++) {
        const IpsRec* r = &sRecs[i];
        uint32_t s = r->off > off ? r->off : off;
        uint32_t e1 = r->off + r->len;
        uint32_t e2 = off + len;
        uint32_t e = e1 < e2 ? e1 : e2;
        if (s >= e) continue;
        if (r->rle) {
            memset(buf + (s - off), r->val, e - s);
        } else {
            fseek(sIps, (long) (r->fpos + (s - r->off)), SEEK_SET);
            if (fread(buf + (s - off), 1, e - s, sIps) != e - s) { /* truncated patch */ }
        }
    }
}
