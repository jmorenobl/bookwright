# Primeros pasos

Este recorrido de cinco minutos te lleva de un directorio vacío a un proyecto
Bookwright validado. Cada comando aquí coincide con el CLI publicado.

## Instalación

El paquete en PyPI es `bookwright-cli`; el comando que instala es `bookwright`.

Desde PyPI (recomendado), con [`uv`](https://docs.astral.sh/uv/) o `pipx`:

```bash
uv tool install bookwright-cli   # con uv
pipx install bookwright-cli      # o con pipx
bookwright version
```

Directamente desde el repositorio (última versión de `main`):

```bash
uv tool install "git+https://github.com/jmorenobl/bookwright"
# o:  pipx install "git+https://github.com/jmorenobl/bookwright"
```

¿Solo quieres probarlo una vez, sin instalar nada?

```bash
uvx --from bookwright-cli bookwright version
```

Para trabajar sobre el código del toolkit, clona el repo y sincroniza el entorno:

```bash
git clone https://github.com/jmorenobl/bookwright && cd bookwright
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

### 2. Destila tu idea con las skills

Aquí está el corazón de Bookwright: **no rellenas los documentos a mano, invocas
skills que lo hacen por ti**. Vuelca tu idea en un Markdown libre (`idea.md`) y,
desde tu agente (Claude Code o compatible con agentskills.io), abre el proyecto e
invoca las skills en orden, pasándoles tu brief:

```
/bookwright-constitution lee idea.md y destila la constitución
/bookwright-bible          ← personajes, settings, cronología, relaciones
/bookwright-outline        ← arcos y estructura de actos/capítulos
/bookwright-scenes         ← desglose en escenas concretas
/bookwright-draft          ← redacta la prosa de una escena
```

Cada skill lee tu brief y el molde estampado por `init`, rellena lo que el
material sostiene y marca `[PENDING: ¿…?]` lo que falta —sin inventar canon. Para
ver qué quedó abierto, invoca `/bookwright-clarify`; para comprobar si un
artefacto está completo, `/bookwright-checklist`. El recorrido completo, con las
10 skills, está en [El flujo de autoría](authoring.md).

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

- Entiende el flujo completo de skills en [El flujo de autoría](authoring.md).
- Conoce cada comando del CLI en [Comandos](commands/init.md).
- Entiende los validadores en [Validación](validation.md).
- Cambia de integración con [`bookwright integration use`](commands/integration-use.md).
