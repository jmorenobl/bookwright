# Tutorial: tu primer libro

Este tutorial te lleva por el proceso **real** de escribir con Bookwright: de una
idea suelta a una escena redactada y revisada, trabajando como trabajarás de
verdad — **conversando con tu agente**. Vas a ver el ciclo entero, incluida la
investigación, y lo más importante: **cómo volver atrás y rehacer** cuando cambias
de idea, que es el 90 % de escribir un libro.

Escribiremos el arranque de un cuento corto, *La hija del farero*. Pequeño a
propósito: lo que importa es el *flujo*, no la extensión.

!!! abstract "La idea clave antes de empezar"
    Con Bookwright **solo usas la terminal una vez**: para crear el proyecto
    (`bookwright init`). A partir de ahí **todo ocurre en tu agente** —Claude Code
    o cualquiera compatible con [agentskills.io](https://agentskills.io)— invocando
    *skills* como `/bookwright-constitution`. Las skills leen y escriben tus
    archivos de texto plano, construyen el grafo y comprueban la continuidad por
    ti. No necesitas saber RDF, ni SPARQL, ni la CLI: necesitas saber qué pedirle a
    cada skill y en qué orden.

## Lo que necesitas

- Python 3.11 o superior, para instalar la CLI.
- Un agente compatible con agentskills.io (este tutorial usa **Claude Code**).
- Quince minutos.

## El recorrido

1. **[Prepara el proyecto](#instalacion)** — instala la CLI y crea el esqueleto (esta página).
2. **[Destila el canon](distill.md)** — la constitución y la biblia, con tu agente.
3. **[Investiga lo que das por cierto](research.md)** — fuentes y anclas para los hechos reales.
4. **[Estructura y redacta](write.md)** — outline, escenas y la prosa de la primera escena.
5. **[Revisa y vuelve atrás](revise.md)** — comprueba la continuidad, cambia de idea y rehazlo.

---

## Instalación

El paquete en PyPI es `bookwright-cli`; el comando que instala es `bookwright`.

=== "uv (recomendado)"

    ```bash
    uv tool install bookwright-cli
    bookwright version
    ```

=== "pipx"

    ```bash
    pipx install bookwright-cli
    bookwright version
    ```

=== "Probar sin instalar"

    ```bash
    uvx --from bookwright-cli bookwright version
    ```

## Crea el proyecto

Este es **el único comando de terminal** que ejecutarás en todo el tutorial:

```bash
bookwright init la-hija-del-farero --integration claude
cd la-hija-del-farero
```

Genera, en un paso, el esqueleto del libro y —porque pasaste `--integration
claude`— materializa las skills de Bookwright en `.claude/skills/`, listas para que
tu agente las invoque:

```text
la-hija-del-farero/
├── manifest.toml          # configuración del proyecto (idioma, validadores, …)
├── bible/                 # el canon: constitución, personajes, settings, cronología
├── outline/               # estructura: arcos, capítulos, escenas, unidades narrativas
├── manuscript/            # tu prosa
└── .claude/skills/        # las 12 Agent Skills, listas para tu agente
```

!!! tip "¿Otro agente?"
    `--integration generic` materializa las skills en `.agents/skills/`, para
    cualquier agente compatible con agentskills.io. Puedes cambiar después sin
    re-inicializar con [`bookwright integration use`](../commands/integration-use.md).

## Abre el proyecto en tu agente

Abre la carpeta `la-hija-del-farero/` en Claude Code (o tu agente). A partir de
aquí no vuelves a la terminal: hablas con el agente y le pides las skills. Para
comprobar que las ve, escríbele:

```text
¿qué skills de bookwright tienes disponibles?
```

Debería listarte `/bookwright-constitution`, `/bookwright-bible`,
`/bookwright-research` y las demás. Si es así, estás listo para destilar tu
historia.

<div class="result" markdown>
**Siguiente:** [Destila el canon →](distill.md)
</div>
