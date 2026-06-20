# Deuda técnica conocida — Bookwright

> **Propósito:** registro plano y trackeado (Principio I) de la deuda técnica
> que un paso del ciclo SDD **detecta pero no limpia en el acto** porque hacerlo
> excedería el scope de la iteración en curso (Scope discipline: no se implementa
> ni se refactoriza por delante del plan). Esta deuda **no se descarta jamás**:
> queda aquí hasta que se resuelve en su propia iteración.
>
> **Qué NO va aquí:**
> - Deuda de la **misma clase** que toca la iteración en curso — esa se barre
>   *entera* en esa misma iteración (todas las instancias, aunque vivan fuera del
>   diff). Precedente: iteración 027 unificó *todos* los envelopes JSON, no solo
>   el citado. Si la clase ya se está tocando, no se difiere: se limpia.
> - Conceptos GOLEM modelados-pero-no-ingestados — esos tienen su propio
>   contrato en `src/bookwright/golem/deferrals.py` (y su test de paridad).
> - Trabajo deliberadamente **cancelado** (presets, Grafeo, multi-integración,
>   extension system) — eso vive en `bookwright-roadmap.md`, no es deuda.
>
> **Regla del ciclo (`bookwright-quality` workflow):** todo paso que encuentre
> deuda ajena al scope la **anexa aquí** (con ubicación, clase, motivo de
> diferimiento y versión sugerida) **y** la reporta en voz alta en su salida.
> Cuando una iteración limpia la deuda, **se borra su entrada** — git conserva
> el historial, igual que `deferrals.py` borra la entrada de un concepto al
> cablearlo (no se archiva en una sección "resuelta", eso solo duplicaría git).
> La única deuda que permanece registrada estando "cerrada" es la que decides
> **no arreglar nunca** (estado `aceptada`): se queda para que el workflow no la
> vuelva a detectar y re-anotar en cada pasada.

## Formato de entrada

```
### DEBT-NNN — <título corto>
- **Estado:** abierta | aceptada (no se arreglará — motivo)
- **Detectada en:** spec-NNN (<fecha>)
- **Ubicación:** <path:línea o módulo>
- **Clase de deuda:** <p. ej. envelope JSON duplicado, validador no cubierto, …>
- **Descripción:** <qué es y por qué es deuda>
- **Por qué se difiere:** <por qué limpiarla ahora rompería el scope de la iteración>
- **Resolución sugerida / versión objetivo:** <cómo limpiarla y cuándo>
```

---

## Deuda abierta

### DEBT-001 — Concepto `NarrativeRole` vestigial (modelado pero nunca ingestado)
- **Estado:** abierta
- **Detectada en:** spec-030 (2026-06-20)
- **Ubicación:** `src/bookwright/golem/modules/narrative.py:37` (clase
  `NarrativeRole`), registrada en `src/bookwright/golem/__init__.py` (`CONCEPTS`).
- **Clase de deuda:** concepto GOLEM modelado-pero-muerto que evade el registro de
  diferimiento.
- **Descripción:** el concepto de nivel superior `NarrativeRole` está en
  `CONCEPTS` pero ningún builder lo instancia: la única materialización de
  `golem:G11_Narrative_Role` la hace el nodo inlined `CharacterRole`
  (`golem/modules/feature.py`, que **no** está en `CONCEPTS`). Como ambos
  comparten el mismo `CLASS_IRI["NarrativeRole"]`, el test de paridad de ingestión
  ve la clase G11 materializada y por eso `NarrativeRole` **no** aparece en
  `DEFERRED_CONCEPTS` (`golem/deferrals.py`) pese a no tener ruta de ingestión
  propia. Es un concepto muerto que escapa al contrato de diferimiento.
- **Por qué se difiere:** la iteración 030 *tipa* entidades G10/G11 vía
  `E55_Type`; eliminar (o cablear) el concepto `NarrativeRole` es otra clase de
  deuda — toca el registro `CONCEPTS`, el conteo "thirteen concepts" de
  `deferrals.py` y su test de paridad — y limpiarla aquí sería refactorizar por
  delante del plan (Scope discipline).
- **Resolución sugerida / versión objetivo:** decidir en una iteración
  estructural posterior si el concepto se elimina de `CONCEPTS` (si
  `CharacterRole` es la única encarnación de G11 que se quiere) o si se le da una
  superficie de autoría propia; ajustar `deferrals.py`/paridad en consecuencia.
  Tocar el registro `CONCEPTS` es su propia clase de deuda estructural, fuera del
  alcance del cierre de v0.4 (iteración 032 no cablea G6/G3 ni reabre `CONCEPTS`).
  Target: demand-pulled — iteración estructural posterior, sin versión asignada.

---

### DEBT-002 — Sección "Scope & Release Discipline" de la constitución desfasada
- **Estado:** abierta
- **Detectada en:** spec-031 (2026-06-20)
- **Ubicación:** `.specify/memory/constitution.md` (sección *Scope & Release
  Discipline*, líneas ~218–226; constitución v1.4.0).
- **Clase de deuda:** deriva documental en un documento vinculante (la
  constitución se cita como Constitution Check gate en cada PR).
- **Descripción:** la sección dice "Active work is M5 / v0.3 — context
  orchestration" y lista **vector search** como diferido a **v0.4**. La realidad
  (CLAUDE.md + `bookwright-roadmap.md`): v0.3.x hardening cerrado, **v0.4 = capa
  narrativa Propp/Greimas** (esta milestone, iter 028–032), y vector search +
  export movidos a un **horizonte demand-pulled sin versión asignada**. La
  constitución contradice al roadmap en la línea de versiones y en el destino de
  vector search. No entra en conflicto con el contenido de la iteración 031 (un
  validador, no vector search), por eso no bloquea esta spec.
- **Por qué se difiere:** corregir la constitución exige el procedimiento formal
  de enmienda (bump de versión, Sync Impact Report, propagación a plantillas y a
  `bookwright-design.md` § 16 si aplica) — es su propio cambio, no parte de un
  commit `docs(spec)` de la iteración 031. Precedente: la enmienda 1.4.0 nació de
  un hallazgo C1 de `/speckit-analyze` en la iteración 019, en su propio PR.
- **Resolución sugerida / versión objetivo:** enmienda MINOR de la constitución
  que reescriba la sección a la realidad enviada (v0.4 = capa narrativa; vector
  search/export → horizonte demand-pulled sin versión). La enmienda viaja con el
  paso manual de release (`bookwright-release`), no con un commit de la rama de la
  iteración 032 — el cierre de v0.4 deja la rama verde y delega versión/CHANGELOG/
  constitución al skill de release tras el merge. Target: enmienda MINOR
  arrastrada por el paso `bookwright-release` de `v0.4.0` (post-merge).

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
