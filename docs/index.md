# Bookwright

<p style="font-size:1.25rem;margin-top:-0.4rem;color:var(--md-default-fg-color--light)">
Escribe tu novela <em>con</em> un agente de IA — sin que se contradiga a sí mismo.
</p>

Bookwright es un *toolkit* de autoría **spec-driven** para novelas, ensayos y
memorias. En lugar de improvisar tu libro en un chat infinito que olvida lo que
dijo hace tres mensajes, destilas tu historia en un puñado de **documentos
canónicos** —constitución, biblia, outline, escenas— y dejas que el agente
escriba a partir de *ellos*. Tu libro vive en texto plano, versionado en git y
completamente auditable.

```bash
pip install bookwright-cli        # o: uv tool install bookwright-cli
bookwright init mi-novela --integration claude
```

Eso es **todo** lo que harás en la terminal. Abre el proyecto en tu agente y, a
partir de ahí, destilas tu libro pidiéndole *skills*:

```text
/bookwright-constitution destila el tono y la voz a partir de mi idea
/bookwright-bible         puebla los personajes y el mundo
/bookwright-draft 1.1     redacta la primera escena
/bookwright-continuity    ¿es coherente con la biblia lo que llevo escrito?
```

---

## El problema que resuelve

Pídele a un agente que escriba un capítulo y obtendrás prosa decente. Pídele el
capítulo veinte y descubrirás que tu protagonista ha cambiado de color de ojos,
que un secundario muerto reaparece, y que la voz narrativa salta de tercera a
primera persona sin avisar. El chat no tiene memoria de tu **canon**: cada
mensaje parte casi de cero.

Bookwright invierte la relación. El canon no vive en la conversación, vive en
**archivos de texto plano** que son la única fuente de verdad. El agente los lee
antes de escribir, y una capa de **validación determinista** comprueba que lo
escrito no los contradiga — en tu máquina y en CI, sin pedirle opinión a ningún
modelo.

## Cómo piensa Bookwright, en 30 segundos

<div class="grid cards" markdown>

-   :material-file-document-edit: __Texto plano es la verdad__

    Tu biblia, tu constitución y tu manuscrito son Markdown. Versionables,
    *diffeable*, tuyos. Nada importante vive en una base de datos opaca.

-   :material-graph: __El grafo es una caché__

    Bookwright indexa tu biblia en un grafo de conocimiento (GOLEM/RDF) para
    poder razonar sobre ella. Es **derivado**: si lo borras, `graph build` lo
    reconstruye desde el texto. Nunca es la fuente.

-   :material-robot-happy: __Las skills destilan, no improvisan__

    Doce *Agent Skills* convierten tu *brief* libre en artefactos canónicos.
    Iteras los **documentos**, no el chat. Lo que no sabe, lo marca
    `[PENDING: ¿…?]` en vez de inventarlo.

-   :material-shield-check: __La validación protege el canon__

    Seis validadores deterministas comprueban continuidad de personajes, voz
    narrativa, línea de tiempo, settings y estructura. Los errores bloquean; las
    advertencias avisan.

</div>

## Empieza por aquí

<div class="grid cards" markdown>

-   :material-school: __[Tutorial](tutorial/index.md)__

    De un directorio vacío a una escena validada de tu primera mini-novela.
    El mejor sitio para empezar si nunca has usado Bookwright.

-   :material-lightbulb: __[Conceptos](concepts/index.md)__

    El modelo mental completo: por qué el texto plano manda, qué es el grafo, el
    loop de autoría y cómo encajan las doce skills.

-   :material-tools: __[Guías prácticas](guides/interpret-validation.md)__

    Recetas para tareas concretas: interpretar la validación, resolver
    pendientes, investigar un hecho real.

-   :material-book-open-variant: __[Referencia](commands/init.md)__

    La CLI verbo a verbo, los validadores y los contratos `--json` que consumen
    los agentes.

</div>

---

Bookwright se distribuye bajo
[EUPL-1.2](https://github.com/jmorenobl/bookwright/blob/main/LICENSE). El
contenido que crees con la herramienta sigue siendo enteramente tuyo. ¿El resumen
completo —el porqué, el *loop* del escritor y los principios de diseño— en un solo
sitio? El [README](https://github.com/jmorenobl/bookwright/blob/main/README.md).
