# El flujo de autoría

Las **skills de autoría** son el corazón de Bookwright. No rellenas los
documentos canónicos a mano: invocas una skill que **lee tu brief, destila el
artefacto y te pregunta solo por lo que falte**. Editar los `.md` directamente
es siempre posible —son texto plano— pero es el retoque, no el flujo principal.

Cada comando es un *Agent Skill* que `bookwright init` materializa en el
directorio de tu integración (`.claude/skills/` para `claude`,
`.agents/skills/` para `generic`). Los invocas desde tu agente —Claude Code o
cualquiera compatible con [agentskills.io](https://agentskills.io)— como
`/bookwright-<comando>`.

## Tu brief

El *brief* es todo lo que tienes de la obra volcado en Markdown libre: un
archivo `idea.md` con la premisa, los personajes que ya conoces, el tono que
buscas, escenas sueltas… Sin formato obligatorio. Es el input que pasas a las
skills generativas.

```
/bookwright-constitution lee idea.md y destila la constitución
```

Lo que pasas tras el comando llega a la skill como su argumento. Puede ser una
referencia a un archivo (`idea.md`), texto pegado, o la conversación previa que
ya tuviste con el agente. Si lo dejas vacío, la skill te pedirá que describas el
proyecto antes de continuar.

## Rellenar, no inventar: el loop `[PENDING]` → `clarify`

Cada skill generativa funciona igual frente a un dato que el brief no aporta,
según el protocolo `[PENDING: …]` compartido:

- **Si solo falta el dato**, escribe un marcador `[PENDING: ¿pregunta concreta?]`
  en su sitio y **continúa**. No te interrumpe por cada hueco.
- **Si rellenarlo exigiera decidir el rumbo de la obra** (la motivación central
  del protagonista, el modelo estructural del que cuelga todo el outline, o algo
  que contradiría lo ya escrito), **se detiene y te pregunta** antes de escribir.

Así avanzas con los huecos marcados y los resuelves cuando quieras. Dos skills
de solo lectura cierran el loop:

- `/bookwright-clarify` recorre el proyecto y te devuelve la **lista de dudas
  abiertas** que conviene resolver antes de seguir.
- `/bookwright-checklist` comprueba si **un artefacto concreto está completo**:
  todas sus secciones, sin `[PENDING]` sin resolver, sin placeholders vacíos.

Cuando resuelves un `[PENDING]` y vuelves a invocar la skill, esta **actualiza
en sitio**: respeta tu prosa y los pendientes ya resueltos, y solo rellena lo
que sigue abierto. No duplica ni sobrescribe lo que ya hay.

## Las skills, en orden

![Pipeline de destilación: /constitution → /bible → /outline → /scenes → /draft, con la rama opcional de investigación /research → /verify para obra basada en hechos](https://raw.githubusercontent.com/jmorenobl/bookwright/main/assets/pipeline.svg)

El orden importa: cada paso se funda en el anterior. La constitución fija las
reglas; la biblia puebla las entidades; el outline las estructura; las escenas
las desglosan; el draft redacta.

> **Nota:** `manuscript/` es **solo para el autor**: el scaffold lo crea, pero el
> motor no ingiere su contenido. `outline/` está **parcialmente ingerido** desde
> v0.4: las fichas de `outline/units/` alimentan unidades y funciones narrativas
> al grafo. Si das a varias unidades una misma clave `sequence` y las numeras con
> `order`, el motor las ensambla en una secuencia recorrible en ese orden. El
> resto del outline (`arcs`/`structure`/`synopsis`/`scenes`) sigue siendo prosa de
> autor que estructura tu trabajo, no el grafo derivado.

### Planificación (pre-draft)

| Skill | Qué hace |
|-------|----------|
| `/bookwright-constitution` | Destila voz, tono, pacto con el lector, líneas rojas e invariantes. El paso que va **antes** de todo. |
| `/bookwright-bible` | Puebla la biblia en una pasada: fichas de personajes, settings y localizaciones, cronología, relaciones, temas, glosario, subtramas. |
| `/bookwright-outline` | Construye el esqueleto: arcos de personaje, estructura de actos/capítulos y una sinopsis inicial. |
| `/bookwright-scenes` | Desglosa la estructura en una lista de escenas concretas (función, personajes, lugar, beats). Planifica, no redacta. |

### Redacción

| Skill | Qué hace |
|-------|----------|
| `/bookwright-draft` | Redacta la prosa de **una** escena (por su `scene_id`) en el capítulo correcto, respetando voz y focalización. El único comando que produce prosa de manuscrito. |

### Investigación y verificación

Las dos skills de **investigación con procedencia** (opcional, disponible desde
v0.2). Pueblan y vigilan `bible/research/`; el sistema entero es opcional y se
enciende con `[research]` en el manifiesto. Disparan tanto con prompts en español como en inglés.

| Skill | Qué hace |
|-------|----------|
| `/bookwright-research` | Investiga un tema del mundo real y lo documenta como **hallazgos con procedencia completa** (fuentes, citas en lengua original, fiabilidad) en `bible/research/`, marcando qué hallazgos son **anclas** que restringen la ficción. Pre-draft. |
| `/bookwright-verify` | Verifica el manuscrito **ya redactado** contra las anclas de investigación: señala anacronismos, errores de procedimiento e inexactitudes culturales o lingüísticas. Solo lectura, **post-draft**. |

Las anclas que `/bookwright-research` deja en el grafo las audita además el validador
determinista [`factual_anchor`](validation.md), que comprueba su integridad
estructural y cronológica en CI. La capa de juicio del LLM (`/bookwright-verify`) y la
capa determinista (`factual_anchor`) son **complementarias**: la primera lee prosa, la
segunda solo el grafo. Todo el modelo se explica en [Investigación](research.md).

### Revisión y mantenimiento

| Skill | Qué hace |
|-------|----------|
| `/bookwright-clarify` | Lista las dudas abiertas del proyecto. Solo lectura. |
| `/bookwright-checklist` | Comprueba la completitud de un artefacto concreto. Solo lectura. |
| `/bookwright-analyze` | Consistencia cruzada **pre-draft** entre constitución, biblia, outline y escenas. Solo lectura. |
| `/bookwright-continuity` | Continuidad **post-draft** del manuscrito frente a la biblia (cumplimiento, arcos, línea de tiempo). Solo lectura. |
| `/bookwright-synopsis` | Regenera la sinopsis corta y larga reflejando el estado actual de la trama. En cualquier momento. |

!!! tip "Las skills no son un co-escritor frase a frase"
    Tú consolidas el input en el brief; la skill lo destila en un artefacto
    versionable. Iteras los **documentos**, no el chat. Y entre el grafo y la
    validación cierras el círculo: tras tocar la biblia, `bookwright graph build`
    rederiva el grafo y `bookwright validate` corre los chequeos de continuidad.

## Después de destilar

- Reconstruye el grafo narrativo: [`bookwright graph build`](commands/graph-build.md).
- Valida la continuidad: [`bookwright validate`](validation.md).
- Cambia de integración sin re-inicializar: [`bookwright integration use`](commands/integration-use.md).
