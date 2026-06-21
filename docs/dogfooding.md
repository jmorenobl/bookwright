# Dogfooding — probar Bookwright sobre un libro real

El roadmap condiciona el avance a **uso real, no a especulación**: el **export** se
activa cuando "el flujo de punta a punta esté probado en un libro real"; la
**búsqueda vectorial**, ante "un fallo medido de structural-recall". Ambas
condiciones solo se comprueban *usando* la herramienta como un autor. Esta página es
la **receta repetible** para hacerlo: autorar un libro real de extremo a extremo y
registrar dónde cruje.

Es una práctica de calidad, no un comando: produce un **log de fricción** y dos
veredictos (recall y export-readiness), y de ahí salen entradas en el registro de
deuda interno y en el plan de implementación.

## Cuándo hacerlo

- **Antes** de declarar el flujo "probado sobre un libro real" (gate de export / `1.0`).
- Para **medir** structural-recall y decidir si la búsqueda vectorial se justifica.
- Tras un hito grande, como sanity de punta a punta sobre algo que no es un fixture.

## 1. Scaffold

`bookwright init <nombre>` y luego edita `manifest.toml` (init **no** tiene flags de
metadata: título, idioma y tipo se autoran en el manifest). Para ejercitar todo:

```toml
[vocabularies]
active = ["propp", "greimas"]   # tipa funciones (G10) y roles (G11)
[research]
enabled = true                  # activa fuentes/findings/anchors
[validators]
enabled = []                    # vacío → todos los integrados corren
disabled = []                   # nada deshabilitado
```

## 2. Inventa **un** libro para cobertura total

No varios libros finos —no estresan la escala ni el recall— sino **un libro a escala
real, ingenierizado para tocar todos los subsistemas**. El género que más cubre es la
**fantasía histórica**: la quest da estructura Propp/Greimas; el trasfondo histórico
real da pie a `research`/anchors; el multi-POV ejercita focalización; el asedio o
viaje aporta settings, localizaciones, objetos densos y una timeline.

Escala orientativa (≈10× un fixture `tiny-*`): ~10 personajes, ~5 settings, ~4
localizaciones, ~4 objetos, ~5 relaciones, ~20 unidades narrativas en **3 secuencias**
(trama + 2 subtramas), ~4 fuentes con findings/anchors, una timeline y ~6 capítulos de
manuscrito multi-POV.

**No dupliques los esquemas de front-matter**: cálcalos de `tests/fixtures/`.
`tiny-historical` es el más rico (personajes con `born`/`features`/`narrative_roles`,
settings, `research/` y `timeline.md`); `tiny-quest` cubre `outline/units/` con
`functions`/`roles`/`sequence`/`order`.

## 3. Matriz de cobertura — un defecto por validador

Mantén el resto coherente y planta **una** incoherencia por validador, para confirmar
que cada uno dispara:

| Validador | Defecto deliberado |
|---|---|
| `character_presence` | un personaje del bible que nunca se nombra en el manuscrito |
| `focalization` | declara una voz narrativa **parseable** y rompe el foco (head-hopping, o primera persona bajo tercera declarada) |
| `setting_continuity` | un salto de setting incoherente entre escenas |
| `temporal` | un orden de eventos contradictorio para un personaje |
| `narrative_structure` | un beat huérfano (unit sin `sequence:`) + un `roles:` que no resuelve |
| `factual_anchor` | un anchor anacrónico (rango disjunto al evento fechado) + uno sostenido solo por una fuente `baja` |

## 4. El bucle

`graph build` → si crashea por front-matter, **arréglalo y anota si el error fue
accionable** → `validate` → repite hasta que (a) el build no crashea y (b) los defectos
de la matriz disparan. Guarda la salida final de `validate` y de `status`.

Gotchas conocidos que vale la pena tener a mano: `source.type` es vocabulario **cerrado**
(`primaria|secundaria|oficial|académica|periodística|testimonial`) y `access_date` debe
ser una **fecha YAML sin comillas**.

## 5. Sondas de recall (SPARQL, con forma de skill)

Con `bookwright graph query`, intenta responder preguntas como las que haría una skill,
y registra si SPARQL **contesta limpio o choca**:

- Estructurales: beats de un rol que están fuera de toda secuencia; settings huérfanos
  (sin unit/evento que los referencie); personajes con un rol Greimas dado.
- De orden: las funciones de una secuencia **en su orden** declarado.
- Una **semántica/borrosa**: "beats sobre 'traición' o 'sacrificio'".

Usa **IRIs de clase exactas** (p. ej. `G12_Setting`, no `G2`): un typo devuelve cero
filas, no un error —indistinguible de "no hay datos".

## 6. Qué registrar (la salida del ejercicio)

1. **Log de fricción** — lo más valioso: todo lo incómodo, sorprendente o roto al
   autorar o correr (calidad de los mensajes de error, claves silenciosamente
   ignoradas, fricción de escala). Concreto: fichero, comando, qué pasó vs. qué
   esperabas.
2. **Veredicto de recall**: ¿basta rdflib/SPARQL para lo estructural, o hay un fallo
   **medido** que justifique búsqueda vectorial? Cita la evidencia.
3. **Veredicto de export-readiness**: ¿el flujo `build → validate` queda verde
   (warnings tolerables, sin errores que gateen) sobre un libro real?
4. **Hallazgos nuevos → el registro de deuda interno** (con ubicación, clase, repro) y
   su entrada en el plan de implementación.

## El proyecto de prueba es **desechable**

No se commitea: un libro de decenas de ficheros rompería la convención de fixtures
**`tiny-*`** (mínimos, source-only, con oráculo) e inflaría CI. Su valor no es el libro
sino **esta receta** y los hallazgos que ya quedan registrados. Cada iteración que
arregle un hallazgo escribe su repro **mínimo** como fixture, al estilo del proyecto —
nunca el libro entero.
