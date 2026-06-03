# Primeros pasos

Este recorrido de cinco minutos te lleva de un directorio vacío a un proyecto
Bookwright validado. Cada comando aquí coincide con el CLI publicado.

## Instalación

Bookwright se desarrolla con [`uv`](https://docs.astral.sh/uv/). Para usar el
CLI ya empaquetado, instala el *wheel* en un entorno aislado:

```bash
uv build
pipx install ./dist/bookwright_cli-*.whl   # o: uv tool install ./dist/*.whl
bookwright version
```

Para trabajar sobre el código del toolkit, sincroniza el entorno del proyecto:

```bash
uv sync
uv run bookwright --help
```

## Quickstart en 5 minutos

### 1. Crea el proyecto

```bash
bookwright init mi-novela --integration claude
cd mi-novela
```

Esto genera la estructura de directorios (`bible/`, `outline/`, `manuscript/`),
el `manifest.toml`, y materializa los *Agent Skills* de Bookwright en
`.claude/skills/`.

### 2. Edita los documentos canónicos

Abre `bible/constitution.md` y declara la voz narrativa; añade fichas de
personaje bajo `bible/characters/<slug>.md` con *frontmatter* `name`, y registra
eventos en `bible/timeline.md`. Todo es texto plano: edítalo en tu editor
favorito.

### 3. Construye el grafo

```bash
bookwright graph build
```

Lee la biblia, construye el grafo GOLEM y lo serializa en `bible/graph.ttl`.

### 4. Consulta el grafo

```bash
bookwright graph query "SELECT ?c WHERE { ?c a golem:G1_Character }" --json
```

Devuelve un único documento JSON en stdout (apto para agentes).

### 5. Valida la continuidad

```bash
bookwright validate
```

Sale con código 0 cuando no hay violaciones de severidad `error`; las
advertencias heurísticas (`warning`) son informativas y no bloquean.

## Siguiente paso

- Conoce cada comando en [Comandos](commands/init.md).
- Entiende los validadores en [Validación](validation.md).
- Cambia de integración con [`bookwright integration use`](commands/integration-use.md).
