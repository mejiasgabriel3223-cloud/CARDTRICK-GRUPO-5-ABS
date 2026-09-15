# Resumen de cambios recientes

Este documento recoge los cambios realizados desde el último pull y explica cómo funciona cada ajuste agregado.

## 1) Fondo configurable para el menú y para la partida

Se añadió soporte para cambiar el fondo desde el JSON de configuración sin tener que tocar código.

- En [menu/menu_config.json](menu/menu_config.json) ahora existen estas claves dentro de `recursos`:
  - `fondo_menu`: imagen del fondo del menú principal.
  - `fondo_juego`: imagen del fondo del modo de juego.
  - `fondo`: clave compatibilidad para mantener configuraciones antiguas.

Ejemplo:

```json
{
  "recursos": {
    "fondo_menu": "assets/fondo_menu.png",
    "fondo_juego": "assets/fondo_menu.png"
  }
}
```

Cómo funciona:

- [menu/gestor_config.py](menu/gestor_config.py) resuelve la ruta correctamente y soporta rutas relativas o absolutas.
- [menu/estado_menu.py](menu/estado_menu.py) usa `GestorConfig.obtener_fondo_menu()` para cargar el fondo del menú.
- [states/play_state.py](states/play_state.py) usa `GestorConfig.obtener_fondo_juego()` para cargar el fondo del modo de juego.
- Si la imagen no existe, el sistema cae a un fondo sólido por defecto.

## 2) Botones de skin "blanco / negro" centrados en la configuración

En la pantalla de configuración, los dos botones para cambiar la skin ya no quedan desalineados a la izquierda.

- El ajuste se realizó en [menu/pantallas_menu.py](menu/pantallas_menu.py) y en [states/menu_state.py](states/menu_state.py).
- Los botones quedan centrados horizontalmente y separados entre sí para una mejor composición visual.

¿Cómo se usa?

- El botón "Skin negra" activa el estilo oscuro.
- El botón "Skin blanca" activa el estilo claro.
- La selección se persiste en el JSON de configuración y se carga en la siguiente ejecución.

## 3) Barra de progreso con formato de puntaje y meta

La barra de progreso quedó ubicada en la parte derecha de la interfaz y ahora muestra la información en formato compacto.

- En [Renderer.py](Renderer.py) la barra sigue representando el avance visual de la ronda.
- El texto incluye el formato: `PROGRESO`, `PUNTAJE ACTUAL: X / META: Y`.
- Esto mantiene la barra visible pero sin saturar la parte central de la pantalla.

## 4) Distribución compacta del juego

Se ajustó la composición de la mesa para dejar más espacio visual y una disposición más ordenada.

- Los jokers quedaron más bajos y más compactos.
- La mano de cartas se elevó ligeramente.
- Los botones para ordenar la mano quedaron justo debajo de la mano, en una posición más natural.
- Esto quedó definido en [Renderer.py](Renderer.py) y [states/play_state.py](states/play_state.py).

## 5) Soporte de configuración persistente en JSON

La configuración del juego sigue centralizada en un archivo JSON, y ahora incluye más campos útiles para la personalización del fondo y la skin.

- [menu/menu_config.json](menu/menu_config.json) es el archivo principal de configuración.
- [menu/gestor_config.py](menu/gestor_config.py) hace la lectura/escritura y la resolución de rutas.
- Si se cambia la skin o el fondo desde código, al guardar la configuración queda persistida para la siguiente ejecución.

## 6) Estructura funcional actual

Los cambios principales quedan distribuidos así:

- [menu/gestor_config.py](menu/gestor_config.py): carga, guarda y resuelve la configuración.
- [menu/menu_config.json](menu/menu_config.json): configuración activa del menú y la apariencia.
- [menu/estado_menu.py](menu/estado_menu.py): fondo y estado del menú principal.
- [menu/pantallas_menu.py](menu/pantallas_menu.py): pantalla de configuración y UX del menú.
- [states/play_state.py](states/play_state.py): fondo del juego y lógica del estado de partida.
- [Renderer.py](Renderer.py): dibujado de la mesa, HUD y barra de progreso.

## 7) Cómo personalizarlo ahora

Para cambiar el fondo del menú o del juego, editá el JSON:

```json
"recursos": {
  "fondo_menu": "assets/fondo_menu.png",
  "fondo_juego": "assets/fondo_menu.png"
}
```

Y para cambiar la skin del mazo de cartas:

```json
"card_skin": "dark"
```

o

```json
"card_skin": "light"
```

## 8) Verificación

La lógica quedó validada con la suite del proyecto ejecutada mediante:

```bash
py -m unittest tests.test_store_play_logic
```

Resultado verificado: 7 tests ejecutados, todos OK.
