#!/usr/bin/env python3
"""Exercise the production collision code with normal and mirrored geometry.

Requires Python 3 and a host C compiler (CC, default clang), no PSP SDK.
The loader's mirrored-vertex registration and collision functions are extracted
verbatim. This checks contact and normals, not the emulator's rendering.
"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


def function(source, signature):
    start = source.index(signature)
    end = source.index("{", start) + 1
    depth = 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def harness_source():
    collision = (ROOT / "src/racing/collision.c").read_text()
    gfx = (ROOT / "src/port/gfx/gfx_pc.c").read_text()
    structs = (ROOT / "include/common_structs.h").read_text()
    defines = (ROOT / "include/defines.h").read_text()
    code = r'''
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <assert.h>
#define TARGET_PSP 1
#define UNUSED
typedef int8_t s8; typedef int16_t s16; typedef int32_t s32;
typedef uint16_t u16; typedef uint32_t u32; typedef float f32; typedef double f64;
typedef f32 Vec3f[3];
typedef struct { struct { s16 ob[3]; u16 flag; s16 tc[2]; uint8_t cn[4]; } v; } Vtx;
'''
    for name in ("Collision", "CollisionTriangle"):
        end = structs.index("} " + name + ";") + len("} " + name + ";")
        start = structs.rfind("typedef struct {", 0, end)
        code += structs[start:end] + "\n"
    defines += (ROOT / "src/racing/collision.h").read_text()
    code += "\n".join(line for line in defines.splitlines()
                      if line.startswith(("#define FACING_", "#define COLLISION ", "#define NO_COLLISION ")))
    code += r'''
static const uint8_t *mirror_vtx_lo, *mirror_vtx_hi;
static uint64_t mirror_slots;
static CollisionTriangle gCollisionMesh[8];
static int gCollisionMeshCount, gIsMirrorMode;
static int D_8015F59C, D_8015F5A0, D_8015F5A4, D_8015F6FA, D_8015F6FC;
static s16 gCourseMinX, gCourseMinY, gCourseMinZ, gCourseMaxX, gCourseMaxY, gCourseMaxZ;
static Vtx *vtxBuffer[64];
'''
    code += function(gfx, "void port_mirrored_vertices(") + "\n"
    code += function(gfx, "int port_is_mirrored_vertex(") + "\n"
    code += collision[collision.index("#define MAX3"):collision.index("void add_collision_triangle(")]
    for signature in (
        "void add_collision_triangle(", "void set_vtx_from_triangle(",
        "void set_vtx_from_tri2(", "void set_vtx_from_quadrangle(",
        "s32 check_collision_zx(", "s32 is_colliding_with_drivable_surface(",
        "s32 is_colliding_with_wall_x(", "s32 is_colliding_with_wall_z(",
    ):
        code += function(collision, signature) + "\n"
    code += r'''
int main(int argc, char **argv) {
    assert(argc == 4);
    int shape = atoi(argv[1]), primitive = atoi(argv[2]), scenario = atoi(argv[3]);
    /* Flat road, slope, wall facing +X, wall facing +Z; each quad winds outward. */
    const s16 shapes[4][4][3] = {
        {{0,0,0}, {0,0,80}, {80,0,80}, {80,0,0}},
        {{0,0,0}, {0,10,80}, {80,30,80}, {80,20,0}},
        {{0,0,0}, {0,80,0}, {0,80,80}, {0,0,80}},
        {{0,0,0}, {80,0,0}, {80,80,0}, {0,80,0}},
    };
    float normals[4][3] = {{0,1,0}, {-0.25f,1,-0.125f}, {1,0,0}, {0,0,1}};
    Vtx vertices[4] = {0}, unrelated[4] = {0};
    int mirrored = scenario == 1;
    gIsMirrorMode = scenario == 1 || scenario == 2;
    for (int i = 0; i < 4; ++i) {
        for (int axis = 0; axis < 3; ++axis)
            vertices[i].v.ob[axis] = shapes[shape][i][axis] * (mirrored && axis == 0 ? -1 : 1);
        vtxBuffer[i] = &vertices[i];
    }
    if (scenario == 1) {
        port_mirrored_vertices(vertices, sizeof(vertices));
    } else if (scenario == 2) {
        /* Mirror mode must not flip geometry outside the mirrored course block. */
        port_mirrored_vertices(unrelated, sizeof(unrelated));
    } else {
        /* Loading a normal course must clear the previous mirrored block. */
        port_mirrored_vertices(vertices, sizeof(vertices));
        port_mirrored_vertices(NULL, 0);
    }
    if (primitive == 0) set_vtx_from_triangle(0x00000204, 2, 7);
    if (primitive == 1) set_vtx_from_tri2(0x00000204, 0x00000406, 2, 7);
    if (primitive == 2) set_vtx_from_quadrangle(0x06000204, 2, 7);
    assert(gCollisionMeshCount == (primitive == 0 ? 1 : 2));
    float length = sqrtf(normals[shape][0]*normals[shape][0] +
                         normals[shape][1]*normals[shape][1] +
                         normals[shape][2]*normals[shape][2]);
    for (int i = 0; i < gCollisionMeshCount; ++i) {
        CollisionTriangle *t = &gCollisionMesh[i];
        assert(fabsf(t->normalX - normals[shape][0] / length * (mirrored ? -1 : 1)) < 0.0001f);
        assert(fabsf(t->normalY - normals[shape][1] / length) < 0.0001f);
        assert(fabsf(t->normalZ - normals[shape][2] / length) < 0.0001f);
        assert(t->surfaceType == 2 && (t->flags & 0xff) == 7);
        /* Test a point above/in front of each triangle, moving toward its face. */
        float p[3], old[3], n[3] = {t->normalX, t->normalY, t->normalZ};
        for (int axis = 0; axis < 3; ++axis) {
            float centre = (t->vtx1->v.ob[axis] + t->vtx2->v.ob[axis] + t->vtx3->v.ob[axis]) / 3.0f;
            p[axis] = centre + n[axis] * 4;
            old[axis] = centre + n[axis] * 6;
        }
        Collision contact = {0};
        contact.surfaceDistance[0] = contact.surfaceDistance[1] = contact.surfaceDistance[2] = 1000;
        if (shape < 2) {
            assert(check_collision_zx(&contact, 5, p[0], p[1], p[2], i) == 1);
            assert(is_colliding_with_drivable_surface(&contact, 5, p[0], p[1], p[2], i, old[0], old[1], old[2]) == 1);
            assert(fabsf(contact.surfaceDistance[2] + 1) < 0.0001f);
        } else if (shape == 2) {
            assert(is_colliding_with_wall_x(&contact, 5, p[0], p[1], p[2], i, old[0], old[1], old[2]) == 1);
        } else {
            assert(is_colliding_with_wall_z(&contact, 5, p[0], p[1], p[2], i, old[0], old[1], old[2]) == 1);
        }
    }
    port_mirrored_vertices(vertices, sizeof(vertices));
    assert(port_is_mirrored_vertex(vertices));
    assert(port_is_mirrored_vertex(vertices + 3));
    assert(!port_is_mirrored_vertex(vertices + 4));
    assert(!port_is_mirrored_vertex((void *)((uintptr_t)vertices - 1)));
    assert(!port_is_mirrored_vertex(NULL));
    port_mirrored_vertices(NULL, 0);
    assert(!port_is_mirrored_vertex(vertices));
    return 0;
}
'''
    return code


class MirrorCollisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="mk64-mirror-collision-")
        cls.addClassCleanup(cls.tmp.cleanup)
        source = Path(cls.tmp.name) / "collision.c"
        source.write_text(harness_source())
        cls.binary = Path(cls.tmp.name) / "collision"
        subprocess.run([os.environ.get("CC", "clang"), "-std=c99", "-O2",
                        str(source), "-lm", "-o", str(cls.binary)], check=True)

    def check_shape(self, shape):
        for primitive, name in enumerate(("TRI1", "TRI2", "QUAD")):
            for scenario, mode in enumerate(("normal after mirror", "mirrored", "unrelated geometry")):
                with self.subTest(primitive=name, mode=mode):
                    result = subprocess.run([str(self.binary), str(shape), str(primitive), str(scenario)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)

    def test_flat_road(self):
        self.check_shape(0)

    def test_slope(self):
        self.check_shape(1)

    def test_wall_x(self):
        self.check_shape(2)

    def test_wall_z(self):
        self.check_shape(3)


if __name__ == "__main__":
    unittest.main()
