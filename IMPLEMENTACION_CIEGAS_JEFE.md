# Implementación de Ciegas Jefe

## Archivos incluidos

- `systems/bosses.py`: reemplaza el módulo actual de bosses y conserva `El Gancho`, `La Muralla` y `La Aguja`, añadiendo `El Psíquico`, `El Pilar` y las cuatro variantes de palo.
- `states/store_state.py`: integra el boss real en la pantalla de selección, muestra nombre/descripción/objetivo y mantiene el mismo boss durante todo el Ante.
- `states/play_state.py`: aplica validaciones antes de jugar y efectos después de jugar, además del registro de cartas jugadas para `El Pilar`.
- `tests/test_bosses.py`: pruebas unitarias de las reglas principales.

## No se modifica

`entities/jokers.py` y la entidad `Joker` no forman parte de esta implementación.

## Reglas implementadas

1. **La Cabeza** — no permite cartas de corazones.
2. **La Ventana** — no permite cartas de diamantes.
3. **El Trébol** — no permite cartas de tréboles.
4. **El Aguijón** — no permite cartas de picas.
5. **La Muralla** — objetivo de fichas mucho mayor.
6. **El Psíquico** — máximo 4 cartas por mano jugada.
7. **El Gancho** — después de jugar una mano, elimina 2 cartas aleatorias de las restantes y repone la mano.
8. **El Pilar** — bloquea las cartas que fueron jugadas durante la ciega inmediatamente anterior.
9. **La Aguja** — conserva la regla existente de una sola mano.

## Integración

La selección del boss se guarda en `context["active_boss"]`. El boss se genera una vez por Ante y se reutiliza para la Ciega Pequeña, la Ciega Grande y finalmente la Ciega Jefe de ese Ante.

Antes de jugar una mano, `PlayState` llama a `BossBlind.validate_play(...)`. Después de una mano válida, llama a `BossBlind.after_hand_played(...)`.

El texto de la regla aparece al seleccionar la Ciega Jefe y vuelve a aparecer en el primer estado de juego mediante el mensaje de `PlayState`.

Las cartas realmente jugadas durante cada ciega se guardan en `context["previous_blind_played_card_codes"]`, permitiendo implementar correctamente `El Pilar` sin conservar objetos `CardEntity` entre ciegas.

## Integración manual

1. Sustituir los tres archivos de código incluidos respetando sus rutas.
2. No modificar `entities/entities.py`, `entities/jokers.py` ni otras entidades de Joker.
3. Ejecutar las pruebas con `pytest tests/test_bosses.py`.
4. Ejecutar el juego y entrar en la pantalla de selección de ciegas para verificar que la tercera tarjeta muestra el nombre, objetivo y descripción del boss real.
