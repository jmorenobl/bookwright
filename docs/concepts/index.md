# Cómo piensa Bookwright

El [tutorial](../tutorial/index.md) te enseñó *qué* hacer. Esta sección explica
*por qué* funciona así. Si entiendes estas cuatro ideas, entiendes Bookwright
entero — todo lo demás son detalles.

## 1. El texto plano es la única fuente de verdad

Tu libro **es** un puñado de archivos Markdown: la constitución, las fichas de la
biblia, el outline, el manuscrito. No hay una base de datos escondida, ni un
formato propietario, ni un estado que solo viva en la memoria de un chat. Si
puedes leerlo en un editor y versionarlo en git, es canon.

Esto no es un detalle de implementación: es el [primer
principio](architecture.md#principios-no-negociables) de la constitución del
proyecto, y de él se deriva casi todo lo demás. Tu trabajo es **auditable**
(cada cambio es un *diff*), **portable** (no dependes de Bookwright para leerlo) y
**tuyo** (nadie te encierra el contenido).

## 2. El grafo es una caché, nunca la fuente

Para *razonar* sobre tu historia —«¿qué personaje no aparece nunca?», «¿este
evento contradice la línea de tiempo?»— Bookwright indexa la biblia en un **grafo
de conocimiento** (el modelo de dominio **GOLEM**, serializado en RDF/Turtle, en
`bible/graph.ttl`).

Pero ese grafo es **derivado**: una proyección de tu texto plano que
`bookwright graph build` reconstruye desde cero cada vez. Bórralo y vuelve a
construirlo: obtienes exactamente lo mismo. Por eso **nunca lo editas a mano** —
editas el Markdown y reconstruyes. El grafo es el motor de razonamiento; el texto
es la verdad.

[→ Texto plano y grafo derivado](architecture.md)

## 3. Destilas documentos, no improvisas en un chat

El flujo de trabajo de Bookwright no es «pídele prosa al modelo y reza». Es un
*pipeline* de **destilación**: vuelcas tu idea en bruto (un *brief*) y una serie
de **Agent Skills** la convierten en artefactos canónicos, en orden — primero la
constitución, luego la biblia, luego el outline, luego las escenas, luego la
prosa.

Iteras los **documentos**, no la conversación. Y cuando una skill no sabe un dato,
no se lo inventa: deja un marcador `[PENDING: ¿…?]` y sigue, para que tú lo
resuelvas cuando quieras.

[→ El loop de autoría y las skills](authoring.md)

## 4. La validación protege el canon, sin pedirle opinión a nadie

Una vez tienes canon, Bookwright lo **vigila**. Seis validadores deterministas
recorren el grafo y el manuscrito buscando contradicciones: un personaje
huérfano, un salto de voz narrativa, una línea de tiempo imposible, un setting
descrito de dos formas incompatibles, un beat narrativo suelto.

Es **determinista**: sin LLM, sin red, mismos bytes de entrada → mismo veredicto.
Los `error` bloquean (en tu máquina y en CI); los `warning` avisan. Y un resultado
vacío **no** se confunde con «todo bien»: si un validador no pudo mirar, te lo
dice.

[→ Interpretar la validación](../guides/interpret-validation.md)

---

## Las capas opcionales

Las cuatro ideas anteriores son el núcleo. Sobre ellas, Bookwright añade dos
capas que **solo pagas si las usas** — un proyecto que las ignora se comporta como
si no existieran:

<div class="grid cards" markdown>

-   :material-magnify-scan: __[Investigación con procedencia](research.md)__

    Para obra basada en hechos: documenta qué sabes, de dónde y con qué
    fiabilidad, y deja que esa investigación **restrinja** la ficción de forma
    verificable.

-   :material-sitemap: __[Estructura narrativa](narrative-structure.md)__

    Modela tu trama con las funciones de Propp y los actantes de Greimas:
    unidades, funciones y secuencias narrativas, tipadas y consultables.

</div>

Y un hilo que las cose todas:

-   :material-compass: __[Orquestación de contexto](orchestration.md)__ — *¿en qué
    trabajo ahora y qué hago a continuación?* `bookwright status` deriva el plan de
    trabajo desde el texto plano, sin un TODO que se pudra.
