# `bookwright integration use`

Cambia la integración de agente activa del proyecto. Re-materializa los *Agent
Skills* de la nueva integración bajo su directorio, actualiza el bloque
`[integration]` del `manifest.toml` y **deja intacto** cualquier directorio de
skills previo (no hay limpieza). La operación es atómica: un fallo deshace todo.

## Uso

```bash
bookwright integration use generic
bookwright integration use claude --json
```

## Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `KEY` | Clave de integración a la que cambiar (p. ej. `claude`, `generic`). |

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Emite el resultado como un único documento JSON en stdout. |

## Por qué es un comando propio

`bookwright init` se niega a reinicializar un proyecto existente (Principio de
protección: detecta `.bookwright/`, incluso con `--force`). Cambiar la
*integración* de un libro vivo es por tanto una operación con nombre propio, no
una bandera de `init`. Al cambiar de `claude` a `generic`, los skills nuevos
aparecen en `.agents/skills/` y los antiguos de `.claude/skills/` permanecen sin
tocar.

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Cambio aplicado. |
| 2 | Proyecto/manifiesto inválido o clave de integración desconocida. |
| 3 | Fallo de materialización/linter (cambio revertido). |
