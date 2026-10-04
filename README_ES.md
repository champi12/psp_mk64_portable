# Mario Kart 64 para PSP, en español

Versión del port [beckerd/psp_mk64_portable](https://github.com/beckerd/psp_mk64_portable)
que acepta la traducción al español de Mario Kart 64 (versión 1.1 del parche).

**No incluye ninguna parte del juego.** Necesitas tu propia ROM y el parche de traducción.

## Qué necesitas
- Tu ROM: `Mario Kart 64 (U) [!].z64` (SHA-1 `579c48e211ae952530ffc8738709f078d5dd215e`).
- El parche de traducción al español (`.xdelta`, versión 1.1) de su autor.
- Python 3 en tu PC, solo para crear el `patch.ips` una vez.

## Cómo se instala
1. Aplica el `.xdelta` a tu ROM USA para obtener la ROM en español (con xdelta UI o `xdelta3`).
2. Crea el parche para el port:
   `python3 tools/es/crear_parche.py "Mario Kart 64 (USA).z64" "Mario Kart 64 (ESP).z64" patch.ips`
3. En la tarjeta de memoria crea `PSP/GAME/MK64Portable/` y pon dentro:
   - `EBOOT.PBP` (de la sección Releases),
   - tu ROM **USA original** (no la traducida),
   - `patch.ips`.
4. La primera vez que arranca, el port aplica el parche en memoria (la ROM no se
   modifica) y prepara los datos. Tarda unos segundos; después ya no.

Sin `patch.ips` el juego funciona, pero las imágenes saldrán en inglés y algunos
textos con "z" en lugar de "ñ".

## Cambios respecto al port original
- Soporte para un parche `.ips` junto a la ROM.
- Arreglo en la lectura de la paleta del cartel de meta (se rompía con ROM parcheadas).
- Textos del código traducidos (pausa, copas, circuitos, puntos, créditos, menú ad hoc, avisos).
- "VUELTA 1/3" separado para que quepa la palabra.

## Créditos
- Port para PSP: beckerd.
- Traducción al español de Mario Kart 64 (parche 1.1): su autor original.
- Adaptación al port: Joan Jiménez (champi12).
