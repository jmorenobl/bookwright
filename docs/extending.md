# Extender Bookwright

Bookwright se extiende por tres vías, todas alineadas con la arquitectura de
plugins (Principio V). Esta página resume el cómo; el detalle vive en
`CONTRIBUTING.md`.

## Crear una nueva integración

Una integración materializa los comandos como *Agent Skills* en el directorio
que el agente espera.

1. Crea `src/bookwright/integrations/<key>/__init__.py` con una subclase de
   `SkillsIntegration` que defina `key`, `config` y `default_skills_dir`.
2. Sobrescribe `resolve_skills_dir()` solo si el directorio depende de opciones.
3. Regístrala añadiendo una línea `_register(<Tu>Integration)` en
   `integrations/__init__.py` (`_register_builtins`). No se edita `base.py`.

`setup()` ya está implementado en la clase base: materializa un `SKILL.md` por
comando fuente y lo pasa por el linter agentskills.io. Cambia la integración
activa de un proyecto con
[`bookwright integration use`](commands/integration-use.md).

## Crear un validador personalizado

1. Módulo bajo `.bookwright/validators/` con una clase que exponga `name`,
   `severity_default` y `validate(project, indexer) -> list[Violation]`.
2. Determinista y sin escritura en disco.
3. Declara su `name` en `[validators] custom` del `manifest.toml`.

Ver [Validación](validation.md) para el contrato completo del validador.

## Crear un vocabulario

Los vocabularios narrativos (p. ej. funciones de Propp, actantes de Greimas) se
distribuyen como Turtle bajo `.bookwright/vocabularies/` y se activan por nombre
en `manifest.toml`:

```toml
[vocabularies]
active = ["propp", "greimas"]
```

Un vocabulario es un grafo RDF cuyas clases y predicados extienden el modelo
GOLEM; se carga junto al grafo del proyecto para consultas SPARQL más ricas.
