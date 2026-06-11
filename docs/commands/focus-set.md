# `bookwright focus set`

Crea o actualiza el **hilo conductor autorado** del proyecto: el bloque opcional
`[focus]` del `manifest.toml`. Sella `updated_at` con la fecha de hoy y preserva
byte a byte el resto del manifiesto (comentarios y orden incluidos). Es estado
*autorado* en texto plano (Principio I).

## Uso

```bash
bookwright focus set --target "arco de Berlín" --notes "cerrar la timeline del cap-04"
bookwright focus set --target "arco de París"            # mantiene las notes existentes
bookwright focus set --target "arco de París" --notes "" # borra las notes
bookwright focus set --target "cap-04" --json
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--target` | Obligatoria. Texto corto no vacío con lo que se está trabajando ahora; se almacena tal cual (sin recortar). Vacío o solo espacios ⇒ error `focus_target_empty` y manifiesto intacto. |
| `--notes` | Opcional. Omitida ⇒ conserva las notes existentes (o `""` al crear); `--notes "X"` ⇒ las fija; `--notes ""` ⇒ las borra. |
| `--json` | Emite el resultado como un único documento JSON en stdout: `{"status":"ok","focus":{…}}`. |

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Bloque creado o actualizado. |
| 2 | No es un proyecto, manifiesto inválido, o `--target` vacío. El campo `code` del sobre distingue el tipo. |
