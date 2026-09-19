# Patch 2 — Tienda visual + secuencia de ciegas + victoria

Este parche se aplica **encima del parche anterior** y conserva sus cambios de controles, posición de cartas, dificultad 300/+200, integración de los 32 Jokers, panel de Jokers, drag & drop y resolución de assets.

## Cambios de esta versión

### Tienda de Jokers
- Los Jokers ofrecidos en la tienda se muestran únicamente como su imagen.
- Ya no se dibuja el recuadro/tarjeta alrededor de la oferta.
- La imagen se carga a su **tamaño original del PNG**, sin `smoothscale` a 96x90 ni deformación a cuadrado.
- El área clicable coincide con el tamaño real de la imagen.
- Al pasar el mouse por encima aparece un tooltip con:
  - nombre;
  - rareza;
  - descripción/efecto;
  - precio de compra;
  - precio de venta.
- Los Jokers ya adquiridos siguen pudiendo seleccionarse para venderlos.

### Assets de ciegas
- Solo las **Ciegas Jefe** reciben un asset visual.
- Ciega pequeña y Ciega grande no cargan ni muestran assets de ciega.

### Flujo de ciegas
El juego ya no permite escoger libremente entre Pequeña, Grande y Jefe.

La secuencia es estricta:

`Pequeña -> Grande -> Jefe -> Pequeña -> Grande -> Jefe -> ...`

- La primera Pequeña se inicia automáticamente.
- Tras superar una Pequeña, la siguiente pantalla solo presenta la Grande.
- Tras superar una Grande, solo presenta la Ciega Jefe.
- Tras superar un Jefe, empieza un nuevo Ante con otra Pequeña.
- Las Pequeñas y Grandes tienen botón `SALTAR CIEGA`.
- Saltar una Pequeña lleva a la Grande.
- Saltar una Grande lleva al Jefe.
- El Jefe no tiene botón de salto y es obligatorio.
- El sistema conserva el jefe elegido para cada Ante y evita repetirlo según la lógica existente de `systems/bosses.py`.

### Victoria
- Se cuenta el número de Ciegas Jefe derrotadas.
- Al derrotar la tercera Ciega Jefe no se abre otra tienda.
- El juego cambia directamente a una nueva `VictoryState`.
- La pantalla muestra:
  - `¡HAS GANADO!`
  - nombre del jugador;
  - puntuación acumulada de toda la partida;
  - número de jefes derrotados.

## Archivos nuevos/modificados

```text
main.py
Renderer.py
entities/__init__.py
entities/jokers.py
entities/jokers_base.py
states/play_state.py
states/store_state.py
states/victory_state.py
systems/antes.py
systems/assets.py
systems/joker_catalog.py
menu/menu_config.json
tests/test_new_features.py
```

## Implementación

Extraer el contenido del ZIP sobre la raíz del repositorio actual y reemplazar los archivos con el mismo nombre.

No se hace ningún `git push` ni se modifica el repositorio remoto.

## Comprobación

Se realizó comprobación de compilación sintáctica de todos los `.py` del parche con `py_compile`.

La ejecución gráfica completa no se pudo realizar en este entorno porque la instalación local disponible aquí no tiene `pygame`; por tanto, la validación final de interacción debe hacerse en la misma máquina donde ya estás ejecutando el juego.

## V3 - Layout de tienda y ficha de Ciega Jefe

- La tienda ahora usa dos paneles visuales: `DISPONIBLES` y `EN MANO`.
- Las ofertas de Joker se muestran sobre el panel de disponibles sin tarjeta/recuadro individual.
- Los assets de oferta se escalan para ser visualmente más grandes, conservando su proporción.
- `REROLL` queda junto al panel de disponibles.
- Los Jokers en mano tienen cinco espacios visibles y conservan selección para venta.
- El tooltip se muestra tanto para una oferta disponible como para un Joker en mano.
- La ficha de Ciega Jefe durante la partida muestra asset, nombre, objetivo y efecto.

### Validación

- `compileall` y parseo AST: correcto.
- La suite de pruebas no pudo ejecutarse en este entorno porque no está instalada la dependencia `pygame`; debe ejecutarse en el entorno habitual del proyecto.

## V4 - Tienda visual + guía de manos de póker

### Cambios
- Los Jokers de ofertas bajan ligeramente dentro del panel de disponibles para no cubrir los textos superiores.
- Se elimina el subtítulo descriptivo del panel EN MANO; queda el contador visual de slots.
- La tienda recibe un fondo/decoración procedural en la paleta azul oscura, teal, púrpura y dorado, sin depender de nuevos archivos de imagen.
- La pantalla de selección/salto de ciega recibe un fondo/decoración propia y mayor diferenciación visual para ciegas normales y jefe.
- El panel derecho de PLAY incluye el botón MANOS DE PÓKER.
- El botón abre una guía modal con las 9 manos de póker ordenadas por puntaje base descendente, mostrando base, multiplicador y un ejemplo con los assets reales de las cartas.
- La guía se cierra con ESC o haciendo clic fuera del modal.

### Archivos modificados en V4
- Renderer.py
- states/store_state.py
- states/play_state.py
