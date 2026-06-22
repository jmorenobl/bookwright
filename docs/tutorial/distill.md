# 2. Destila el canon

Tienes el esqueleto y el proyecto abierto en tu agente. Ahora vas a llenarlo de
**canon**: las reglas de la obra (la constitución) y el censo del mundo (la
biblia). No escribes estos archivos a mano — le das tu idea a una skill y ella los
**destila** por ti, preguntándote solo por lo que falte.

## Dale tu idea: el brief

Todo arranca de un *brief*: tu historia en bruto, en lenguaje natural. No hay
formato. Puede ser un archivo, texto pegado, o lo que ya le hayas contado al
agente en la conversación. Para este tutorial, dile a tu agente:

```text
Quiero escribir un cuento corto, "La hija del farero".

Mara cuida el faro de un pueblo costero desde que su padre enfermó. Es la única
que queda para encender la lámpara cada noche. Tobías es el pescador que le trae
noticias del puerto.

Tercera persona limitada, centrada en Mara. Tono sobrio, de cuento. Pasado.
```

## Destila la constitución

La **constitución** fija las reglas del juego: la voz narrativa, el tono, el pacto
con el lector, las líneas rojas. Es lo primero, porque todo lo demás se apoya en
ella. Pídesela a tu agente:

```text
/bookwright-constitution destila la constitución a partir de lo que te he contado
```

La skill lee tu brief y el molde que `init` ya dejó en `bible/constitution.md`,
rellena cada sección con lo que tu idea sostiene, marca con `[PENDING: ¿…?]` lo que
no, reconstruye el grafo para validar que todo parsea, y te devuelve un **reporte**
del estilo:

```text
Constitución destilada en bible/constitution.md.
  · Voz narrativa: tercera persona limitada (centrada en Mara).
  · Tono: sobrio, de cuento. Tiempo: pasado.
  · 1 campo quedó [PENDING]: el pacto histórico-ficcional.
  · Vocabularios activos: ninguno.
Sugerencia: ejecuta /bookwright-clarify antes de pasar a la biblia.
```

El resultado es texto plano que puedes leer y editar cuando quieras:

```markdown title="bible/constitution.md (extracto)"
## Voz y registro
- **Voz narrativa**: Tercera persona limitada, centrada en Mara.
- **Tiempo verbal dominante**: Pasado.
```

!!! info "La voz narrativa no es decorativa"
    Esa línea `- **Voz narrativa**: Tercera persona limitada…` la leerá luego el
    sistema para vigilar que no se te cuelen saltos de punto de vista. Si la dejaras
    como un `[PENDING]`, esa comprobación no podría ejecutarse — lo verás en el
    [paso 5](revise.md).

## El primer bucle de iteración: `[PENDING]` → resolver → rehacer

Aquí aparece el patrón que repetirás durante todo el libro. La constitución dejó un
`[PENDING]`. Para ver qué quedó abierto en todo el proyecto, pregúntale al agente:

```text
/bookwright-clarify
```

Es una skill de **solo lectura**: no toca nada, solo te devuelve la lista de dudas
abiertas, priorizadas. Te dirá, por ejemplo:

```text
Abierto en bible/constitution.md:
  · Pacto histórico-ficcional: ¿el cuento se ancla en un lugar/época reales,
    o es atemporal? [PENDING]
```

Respóndela en lenguaje natural y pídele a la skill que **rehaga** la constitución:

```text
/bookwright-constitution es atemporal, un pueblo costero sin fecha concreta
```

Y aquí está lo importante: la skill **actualiza in situ**. No empieza de cero ni
te pisa lo que ya habías decidido — conserva tu prosa y los pendientes ya
resueltos, y solo rellena el que acabas de responder. Ese mismo «rehacer respetando
lo anterior» es como cambiarás de idea más adelante sin miedo a romper nada.

!!! tip "¿Sin agente, siguiendo a mano?"
    Todo esto son archivos de texto plano: puedes editar `bible/constitution.md`
    directamente y saltarte las skills. Pero el flujo que enseña este tutorial —y
    para el que Bookwright está hecho— es el del agente. Las skills te ahorran el
    trabajo y conocen los contratos de cada archivo.

## Puebla la biblia

Con las reglas fijadas, la **biblia** es el censo del mundo: una ficha por
personaje, por setting, por localización, más cronología y relaciones. Una sola
skill la levanta entera:

```text
/bookwright-bible puebla la biblia con los personajes y el escenario del cuento
```

La skill funda cada entidad a partir de la constitución y el brief — sin inventar
canon de más — y escribe una ficha por archivo. Para nuestro cuento creará, entre
otros, `bible/characters/mara.md` y `bible/characters/tobias.md`:

```markdown title="bible/characters/mara.md"
---
name: "Mara"
---
Mara cuida el faro desde que su padre enfermó. Es la única que queda para
encender la lámpara cada noche.
```

Cada ficha es Markdown con un *front-matter* YAML: el `name` será la identidad del
personaje en el grafo; el cuerpo es prosa libre para ti y para el agente. Como
antes, lo que el brief no resuelva queda `[PENDING]` — y lo cierras con el mismo
bucle `clarify → responder → re-invocar`.

Ya tienes reglas y mundo. Antes de estructurar la trama, conviene asegurar los
**hechos** que tu historia da por ciertos.

<div class="result" markdown>
**Siguiente:** [Investiga lo que das por cierto →](research.md)
</div>
