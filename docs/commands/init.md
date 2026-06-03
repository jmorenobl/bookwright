# `bookwright init`

Crea un nuevo proyecto Bookwright: estructura de directorios, `manifest.toml` y
los *Agent Skills* de la integración elegida.

## Uso

```bash
bookwright init mi-novela --integration claude
bookwright init --here                     # inicializa en el directorio actual
```

## Argumentos

| Argumento | Descripción |
|-----------|-------------|
| `PROJECT_NAME` | Nombre del directorio del nuevo proyecto (mutuamente excluyente con `--here`). |

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--here` | Inicializa en el directorio actual en lugar de crear uno nuevo. |
| `--force` | Sobrescribe colisiones de nombres bajo la raíz del proyecto. |
| `--no-git` | Omite el `git init` + commit automático. |
| `--integration` | Clave de integración del agente (por defecto: `claude`). |
| `--integration-options` | Opciones POSIX entre comillas reenviadas a la integración (p. ej. `"--skills-dir .cursor/skills"`). |
| `--json` | Emite un único documento JSON en stdout. |

## Notas

`init` se niega a reinicializar un proyecto ya existente (detecta `.bookwright/`),
incluso con `--force`. Para cambiar de integración en un proyecto existente, usa
[`bookwright integration use`](integration-use.md).
