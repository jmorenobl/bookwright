# `bookwright focus clear`

Elimina el bloque `[focus]` del `manifest.toml`, preservando el resto del
manifiesto (comentarios y orden incluidos). Sin bloque, es un no-op con éxito.

## Uso

```bash
bookwright focus clear
bookwright focus clear --json
```

```console
$ bookwright focus clear
focus cleared
$ bookwright focus clear --json
{"status":"ok","cleared":false}
```

El discriminador booleano `cleared` permite a un agente distinguir un borrado real
(`true`) de un no-op (`false`) sin una segunda lectura; ambos son `status:"ok"`,
salida 0.

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Emite el resultado como un único documento JSON en stdout: `{"status":"ok","cleared":<bool>}`. |

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Éxito — **incluido** el no-op cuando no había bloque `[focus]`. |
| 2 | No es un proyecto o el manifiesto es inválido. |
