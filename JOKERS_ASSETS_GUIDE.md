# Guía de asignación de assets para jokers

Este documento define la distribución visual de los jokers del juego y asegura que cada comodín tenga un asset consistente, modular y escalable.

## Regla principal

- Cada joker tiene una familia visual asignada.
- Cada familia apunta a una colección concreta de assets dentro de la carpeta `assets(beta)/jokers`.
- El joker `BrendaMadagascarJoker` tiene una excepción: debe usar el asset especial.
- La resolución de assets se hace de forma centralizada en `systems/assets.py`, para evitar mezclar lógica gráfica con lógica del juego.

---

## Asset especial

- `BrendaMadagascarJoker` → `joker-Especial.png`

Ruta:

- `assets(beta)/jokers/joker-Especial.png`

Este asset queda reservado para el joker más especial del conjunto.

---

## Familias de assets

### 1) `especial`

- `BrendaMadagascarJoker`

Asset usado:

- `joker-Especial.png`

---

### 2) `alado`

Jokers:

- `CorazonesPLUS`
- `DiamantesPLUS`
- `TrebolesPLUS`
- `EspadasPLUS`
- `RealezaJoker`
- `Ruleta`
- `BolaDeNieveJoker`
- `AsEnLaMangaJoker`

Assets disponibles:

- `joker-alado-amarillo.png`
- `joker-alado-azul.png`
- `joker-alado-morado.png`
- `joker-alado-negro.png`
- `joker-alado-rojo.png`

Uso recomendado:

- esta familia se usa para jokers de bonificación, brillo y fuerza visual.

---

### 3) `misterioso`

Jokers:

- `LetItRide`
- `AvariciaDesatada`
- `InversionistaJoker`
- `RecicladorJoker`
- `TarjetaDeCreditoJoker`

Assets disponibles:

- `joker-misterioso-amarillo.png`
- `joker-misterioso-azul.png`
- `joker-misterioso-negro.png`
- `joker-misterioso-rojo.png`
- `joker-misterioso-verde.png`

Uso recomendado:

- ideal para efectos económicos, raros o con bonus más complejos.

---

### 4) `observador`

Jokers:

- `MaestroDelParJoker`
- `OjoDeAguilaJoker`
- `GranDobleJoker`
- `TriadaJoker`
- `CaminanteJoker`
- `PokerMaestroJoker`
- `PrismaJoker`
- `CasaLlenaJoker`
- `CoronaImperialJoker`

Assets disponibles:

- `joker-observador.png`
- `joker-observador-azul.png`
- `joker-observador-gris.png`
- `joker-observador-naranja.png`
- `joker-observador-verde.png`

Uso recomendado:

- para jokers ligados a manos, condiciones y lectura del estado del juego.

---

### 5) `sonriente`

Jokers:

- `DonutJoker`
- `PalomitasJoker`
- `PimientoJoker`
- `VidrioFinoJoker`
- `RamenJoker`
- `HeladoJoker`

Assets disponibles:

- `joker-sonriente-amarillo.png`
- `joker-sonriente-azul.png`
- `joker-sonriente-negro.png`
- `joker-sonriente-rojo.png`
- `joker-sonriente-verde.png`

Uso recomendado:

- para jokers con usos limitados, de comida o visual más dinámico y alegre.

---

### 6) `truco`

Jokers:

- `ChipsterJoker`
- `FavoritoJoker`

Assets disponibles:

- `joker-truco-amarillo.png`
- `joker-truco-azul.png`
- `joker-truco-negro.png`
- `joker-truco-rojo.png`
- `joker-truco-verde.png`

Uso recomendado:

- para jokers que dan bonus directos o que tienen sensación de manipulación o estrategia.

---

### 7) `doble`

Jokers:

- `BolaDeNieveJoker`
- `RepeticionJoker`

Assets disponibles:

- `joker-doble.png`
- `joker-doble-cara-azul.png`
- `joker-doble-cara-rojo.png`

Uso recomendado:

- para efectos repetitivos y de crecimiento / duplicación.

---

### 8) `gorro`

Este grupo queda preparado para jokers ultra especiales o de rareza alta, de forma extensible para futuras adiciones.

Assets disponibles:

- `joker-del-gorro-rojo.png`
- `joker_del_gorro_azul.png`
- `joker_del_gorro_negro.png`
- `joker_del_gorro_verde.png`

---

## Política de implementación

La asignación debe mantenerse en `systems/assets.py` y no mezclarse con el efecto del joker.

La lógica recomendada es:

1. mapear cada `ClassName` a una familia visual
2. resolver el fichero según la familia
3. usar un fallback aleatorio si la familia no existe
4. no tocar la lógica de juego ni los efectos de los jokers

Esto mantiene el sistema:

- modular
- escalable
- fácil de depurar
- seguro ante fallos

---

## Resumen rápido

| Joker | Familia | Asset |
|---|---|---|
| `BrendaMadagascarJoker` | `especial` | `joker-Especial.png` |
| `CorazonesPLUS` | `alado` | `joker-alado-*` |
| `DiamantesPLUS` | `alado` | `joker-alado-*` |
| `TrebolesPLUS` | `alado` | `joker-alado-*` |
| `EspadasPLUS` | `alado` | `joker-alado-*` |
| `ChipsterJoker` | `truco` | `joker-truco-*` |
| `RealezaJoker` | `alado` | `joker-alado-*` |
| `DonutJoker` | `sonriente` | `joker-sonriente-*` |
| `PalomitasJoker` | `sonriente` | `joker-sonriente-*` |
| `Ruleta` | `alado` | `joker-alado-*` |
| `BolaDeNieveJoker` | `doble` | `joker-doble*` |
| `AsEnLaMangaJoker` | `alado` | `joker-alado-*` |
| `PimientoJoker` | `sonriente` | `joker-sonriente-*` |
| `VidrioFinoJoker` | `sonriente` | `joker-sonriente-*` |
| `RamenJoker` | `sonriente` | `joker-sonriente-*` |
| `HeladoJoker` | `sonriente` | `joker-sonriente-*` |
| `LetItRide` | `misterioso` | `joker-misterioso-*` |
| `AvariciaDesatada` | `misterioso` | `joker-misterioso-*` |
| `MaestroDelParJoker` | `observador` | `joker-observador-*` |
| `OjoDeAguilaJoker` | `observador` | `joker-observador-*` |
| `GranDobleJoker` | `observador` | `joker-observador-*` |
| `TriadaJoker` | `observador` | `joker-observador-*` |
| `CaminanteJoker` | `observador` | `joker-observador-*` |
| `PokerMaestroJoker` | `observador` | `joker-observador-*` |
| `PrismaJoker` | `observador` | `joker-observador-*` |
| `CasaLlenaJoker` | `observador` | `joker-observador-*` |
| `CoronaImperialJoker` | `observador` | `joker-observador-*` |
| `InversionistaJoker` | `misterioso` | `joker-misterioso-*` |
| `RecicladorJoker` | `misterioso` | `joker-misterioso-*` |
| `TarjetaDeCreditoJoker` | `misterioso` | `joker-misterioso-*` |
| `RepeticionJoker` | `doble` | `joker-doble*` |
| `FavoritoJoker` | `truco` | `joker-truco-*` |

---

## Nota final

Este documento sirve como referencia de diseño y como base para futuras ampliaciones. Si se añaden nuevos jokers, lo más seguro es:

- asignarles una familia visual
- añadirlos al mapa en `systems/assets.py`
- mantener el naming consistente con los assets ya existentes

Así el proyecto conserva estructura, claridad y facilidad de mantenimiento.
