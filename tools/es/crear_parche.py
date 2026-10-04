#!/usr/bin/env python3
"""Crea patch.ips (traduccion al espanol) para psp_mk64_portable.

Uso:
  python3 crear_parche.py "Mario Kart 64 (USA).z64" "Mario Kart 64 (ESP).z64" patch.ips

La ROM ESP se obtiene aplicando a la ROM USA el parche xdelta de su autor:
  xdelta3 -d -s "Mario Kart 64 (USA).z64" parche.xdelta "Mario Kart 64 (ESP).z64"

Este script no contiene datos del juego: solo compara los dos archivos que le
das y hace dos ajustes para que funcionen en el port:
  - las texturas de menu (TKMK00) que en espanol ocupan mas que la original se
    dejan en su version original (el port no tiene sitio para ellas);
  - el cartel redondo "64" vuelve a su color original (azul).
"""
import hashlib, re, sys

USA_SHA1 = "579c48e211ae952530ffc8738709f078d5dd215e"
ESP_SHA1 = "93c63590767b5ac7c7ca6c5b1657a10c8332720b"
CARTEL_64 = 0x642A88

def fin_mio0(d, o):
    size = int.from_bytes(d[o+4:o+8], "big")
    co = int.from_bytes(d[o+8:o+12], "big"); uo = int.from_bytes(d[o+12:o+16], "big")
    bi = 0; cp = o + co; up = o + uo; sal = 0
    while sal < size:
        flag = (d[o + 16 + (bi >> 3)] >> (7 - (bi & 7))) & 1; bi += 1
        if flag: up += 1; sal += 1
        else:
            a = d[cp]; cp += 2; sal += (a >> 4) + 3
    return up

def crear_ips(base, new):
    n = len(base); regs = []; i = 0
    while i < n:
        if base[i:i+4096] == new[i:i+4096]: i += 4096; continue
        if base[i] == new[i]: i += 1; continue
        s = last = i; j = i + 1
        while j < n and j - last <= 8:
            if base[j] != new[j]: last = j
            j += 1
        regs.append((s, last + 1)); i = last + 1
    out = bytearray(b"PATCH")
    for s, e in regs:
        while s < e:
            st = s - 1 if s == 0x454F46 else s
            l = min(e - st, 65535)
            out += st.to_bytes(3, "big") + l.to_bytes(2, "big") + bytes(new[st:st+l])
            s = st + l
    return bytes(out + b"EOF")

def main():
    if len(sys.argv) != 4:
        print(__doc__); sys.exit(1)
    usa = open(sys.argv[1], "rb").read()
    esp = bytearray(open(sys.argv[2], "rb").read())
    if hashlib.sha1(usa).hexdigest() != USA_SHA1:
        sys.exit("ERROR: la ROM USA no es la esperada: Mario Kart 64 (U) [!] en formato .z64")
    if hashlib.sha1(esp).hexdigest() != ESP_SHA1:
        print("AVISO: la ROM ESP no es la version 1.1 conocida; se intenta igual")
    if len(esp) != len(usa):
        sys.exit("ERROR: las dos ROM deben medir lo mismo")
    tk = [m.start() for m in re.finditer(b"TKMK00", usa)]
    mio = [m.start() for m in re.finditer(b"MIO0", usa)]
    marcas = sorted(tk + mio)
    n = 0
    for o in tk:
        k = marcas.index(o)
        fin = min(marcas[k + 1] if k + 1 < len(marcas) else len(usa), o + 0x1000)
        if usa[o:fin] != esp[o:fin] and len(bytes(esp[o:fin]).rstrip(b"\0")) > len(usa[o:fin].rstrip(b"\0")):
            esp[o:fin] = usa[o:fin]; n += 1
    sig = mio[mio.index(CARTEL_64) + 1]
    fin = min(sig, (max(fin_mio0(usa, CARTEL_64), fin_mio0(esp, CARTEL_64)) + 15) & ~15)
    esp[CARTEL_64:fin] = usa[CARTEL_64:fin]
    p = crear_ips(usa, esp)
    open(sys.argv[3], "wb").write(p)
    print("Listo: %s (%d bytes). Texturas de menu que quedan en original: %d" % (sys.argv[3], len(p), n))

main()
