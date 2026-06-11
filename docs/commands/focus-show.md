# `bookwright focus show`

Solo lectura. Muestra el **hilo conductor autorado** actual (el bloque `[focus]`
del `manifest.toml`) de forma legible en stdout, o como un único documento JSON.
Si no hay bloque, lo informa con elegancia por stderr y sale con código 0 — la
ausencia de foco no es un error.

## Uso

```bash
bookwright focus show
bookwright focus show --json
```

Presente:

```console
$ bookwright focus show
target:     arco de Berlín
notes:      cerrar la timeline del cap-04
updated_at: 2026-06-11
```

```console
$ bookwright focus show --json
{"status":"ok","focus":{"target":"arco de Berlín","notes":"cerrar la timeline del cap-04","updated_at":"2026-06-11"}}
```

Ausente: `no focus defined` por stderr (humano), o `{"status":"ok","focus":null}`
con `--json`. En ambos casos, salida 0.

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Emite el estado del foco como un único documento JSON en stdout: `{"status":"ok","focus":{…}}` o `{"status":"ok","focus":null}`. |

## Códigos de salida

| Código | Significado |
|--------|-------------|
| 0 | Éxito — **incluido** cuando no hay bloque `[focus]`. |
| 2 | No es un proyecto o el manifiesto es inválido. |
