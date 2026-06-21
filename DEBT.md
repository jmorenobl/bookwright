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

> Las dos entradas siguientes salieron del **ejercicio de dogfooding** sobre un
> libro real ("El Cerco de Almenara", 49 ficheros / 90 entidades / 1550 triples,
> 2026-06-21). Cada una tiene su iteración asignada en
> `bookwright-implementation-plan.md` y se **borra** al cerrar esa iteración.

### DEBT-005 — la capa narrativa (G9) no es consultable por contenido ni por orden
- **Estado:** abierta
- **Detectada en:** dogfooding post-`v0.4.1` (2026-06-21)
- **Ubicación:** `src/bookwright/golem/modules/narrative.py` (`NarrativeUnit` sin
  `rdfs:label`; `NarrativeSequence`: el orden vive solo como orden de tupla del
  emisor, FR-015, no como triple — líneas 67-68).
- **Clase de deuda:** gap de recall estructural / información de autoría no
  materializada en el grafo.
- **Descripción:** (a) las `G9_Narrative_Unit` no emiten `rdfs:label`; su nombre
  humano vive **solo** en el slug de la URI, así que ninguna consulta SPARQL por
  nombre/contenido de beat es posible. (b) El `order:` declarado se consume al
  ensamblar la secuencia y **no se materializa**: RDF es no-ordenado, así que SPARQL
  no puede recuperar el orden de los beats. Medido en dogfooding: las sondas "lista
  las funciones en orden de la secuencia X" y "beats sobre <tema>" fallan
  estructuralmente. Es el **prerequisito** antes de evaluar búsqueda vectorial
  (horizonte demand-pulled): primero hay que poder hacer match por label/orden.
- **Por qué se difiere:** añade triples a la capa narrativa y exige decidir el
  mecanismo de orden bajo RDF respetando Principio X — es su propia iteración, no
  material del fix de `focalization`.
- **Resolución sugerida / versión objetivo:** emitir `rdfs:label` en `NarrativeUnit`
  (y `NarrativeFunction` si aplica) con su `name`, siguiendo el patrón de
  `CharacterRole`/`E55_Type`; y materializar un ordinal **consultable** de la
  membresía de secuencia, **sin clase de ontología nueva** (Principio X). Verificar
  con dos consultas SPARQL (por label y units en orden). **Iteración 035 → `v0.4.3`.**

### DEBT-006 — mensajes de error de autoría ciegan al autor (research sources)
- **Estado:** abierta
- **Detectada en:** dogfooding post-`v0.4.1` (2026-06-21)
- **Ubicación:** el loader/modelo de fuentes de research (p. ej. `src/bookwright/io/research.py`
  + el modelo Pydantic `Source`).
- **Clase de deuda:** calidad de diagnósticos de error (UX de autoría).
- **Descripción:** (F1) cuando una fuente declara un `type` fuera del vocabulario
  cerrado (`primaria|secundaria|oficial|académica|periodística|testimonial`), el
  error nombra el valor inválido pero **no enumera los aceptados** → el autor itera a
  ciegas. (F2) cuando `access_date` se escribe entrecomillado (string en vez de fecha
  YAML), el error `Input should be a valid date` **no nombra qué fuente** de la lista
  falló ni que la causa son las comillas. (Footgun relacionado, fuera de fix de
  mensaje: un typo de clase/predicado en `graph query` devuelve resultado vacío
  indistinguible de "no hay datos" — se **documenta**, no se arregla con un mensaje.)
- **Por qué se difiere:** clase distinta (UX de errores) a DEBT-005; agrupable en
  su propia pasada de endurecimiento.
- **Resolución sugerida / versión objetivo:** enumerar los valores válidos en el
  error de `type`; anteponer el `name` (o índice 1-based) de la fuente a los errores
  por-fuente; tests para ambos mensajes; nota de documentación para el footgun de
  SPARQL. **Iteración 036 → `v0.4.4`.**

---

## Deuda aceptada (no se arreglará)

_Ninguna por ahora._
