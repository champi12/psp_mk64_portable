# Mario Kart 64 para PSP — Versión en español

> **Esta NO es la versión original.** Es una versión modificada
> y no oficial, preparada para jugar con la traducción al español.
>
> El proyecto original es
> [beckerd/psp_mk64_portable](https://github.com/beckerd/psp_mk64_portable),
> creado por **beckerd**. Su documentación original (en inglés) está en
> [README_ORIGINAL.md](README_ORIGINAL.md).

**Este proyecto no incluye ninguna parte del juego.**
Necesitas tu propia ROM de Mario Kart 64 (USA)
y el parche de traducción al español de su autor.

## Qué cambia respecto al original

- Acepta un parche `patch.ips` junto a la ROM y lo aplica
  automáticamente al arrancar.
- Corrige un fallo del port que rompía los colores del cartel
  "MARIO KART" de la meta cuando la ROM está parcheada.
- Textos del juego en español: menú de pausa, copas, circuitos,
  puntuaciones, créditos, avisos y menú de juego en red (ad hoc).
- "VUELTA 1/3" separado para que quepa la palabra.

## Qué necesitas

1. **Tu ROM de Mario Kart 64 (USA)** en formato `.z64`:
   `Mario Kart 64 (U) [!].z64`
   (SHA-1 `579c48e211ae952530ffc8738709f078d5dd215e`).
2. **El parche de traducción al español** (versión 1.1, archivo
   `.xdelta`) de su autor original. No se distribuye aquí.
3. **El EBOOT de esta versión**: descárgalo en la sección
   **Releases** (archivo `MK64Portable_es.zip`).
4. **Python 3** en tu PC, solo para crear el parche una vez:
   <https://www.python.org/downloads/>
   (en Windows marca *Add python.exe to PATH* al instalarlo).

## Instalación paso a paso

### 1. Crea la ROM en español

Aplica el `.xdelta` del autor a tu ROM USA con un programa de
parches xdelta (por ejemplo *xdelta UI* o *Delta Patcher* en Windows).
Obtendrás `Mario Kart 64 (ESP).z64`.
Esta ROM solo sirve para crear el parche: **no la copies a la PSP**.

### 2. Crea el archivo `patch.ips`

Descomprime `MK64Portable_es.zip`. Dentro está `crear_parche.py`.
Pon en esa misma carpeta tu ROM USA y la ROM ESP.
Abre una terminal en esa carpeta (en Windows: escribe `cmd` en la
barra de direcciones del explorador y pulsa Enter) y ejecuta:

    python crear_parche.py "Mario Kart 64 (USA).z64" "Mario Kart 64 (ESP).z64" patch.ips

Debe responder `Listo: patch.ips`.
Si `python` no funciona, prueba con `py` en su lugar.

### 3. Copia los archivos a la PSP

    PSP/
    └── GAME/
        └── MK64Portable/
            ├── EBOOT.PBP
            ├── Mario Kart 64 (USA).z64   <- tu ROM USA ORIGINAL
            └── patch.ips

- La ROM debe ser la **USA original**, no la traducida:
  el port aplica el parche por su cuenta.
- El parche debe llamarse `patch.ips`, o igual que la ROM pero
  terminado en `.ips` (por ejemplo `Mario Kart 64 (USA).ips`).

### 4. Primer arranque

La primera vez aparece la pantalla
*"First start: building the game data from your ROM"*.
El port aplica el parche **en memoria** (tu ROM no se modifica)
y guarda los datos en la carpeta `data`.
Tarda unos segundos; las siguientes veces arranca directamente.

## En el emulador PPSSPP

Igual que en la PSP: una carpeta con los mismos tres archivos,
y abre el `EBOOT.PBP` desde PPSSPP (*File → Load*).

## Problemas frecuentes

- **El juego sale en inglés:** falta `patch.ips` o tiene otro nombre.
  Cada vez que pongas o cambies el parche, **borra la carpeta `data`**
  para que los datos se vuelvan a preparar.
- **"No Mario Kart 64 ROM found":** la ROM no está en la misma
  carpeta que el `EBOOT.PBP`.
- **"not the US (NTSC) version":** tu ROM no es la versión USA.
- **El script dice que la ROM USA no es la esperada:** necesitas la
  versión `(U) [!]` en formato `.z64`.
- **Sale "z" donde debería haber "ñ":** estás jugando sin el parche.
  Los textos de esta versión usan la fuente con ñ que trae la traducción.

Fallos que ya tiene el port original (no son de la traducción):
en la tabla de récords de contrarreloj se superponen letras "B",
y en las repeticiones de contrarreloj la pausa selecciona sola
"REPETICION".

## Créditos

- **Port para PSP:** beckerd —
  <https://github.com/beckerd/psp_mk64_portable>
- **Traducción al español de Mario Kart 64 (parche 1.1):**
  su autor original.
- **Adaptación de la traducción a este port:** Joan Jiménez (champi12).

Mario Kart 64 es una marca de Nintendo. Este proyecto no está
afiliado a Nintendo y es para uso personal con una copia legal
del juego. La licencia es la del proyecto original.
