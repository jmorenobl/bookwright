# 3. Investiga lo que das por cierto

Toda historia se apoya en cosas que da por ciertas. Una novela histórica las toma
del mundo real; incluso nuestro cuento atemporal gana si el faro **funciona como un
faro de verdad**. Bookwright tiene una capa para eso: documentar qué sabes, **de
dónde lo sabes y con qué fiabilidad**, y dejar que esa investigación restrinja la
ficción de forma verificable.

!!! note "Este paso es opcional"
    Si tu obra es pura fantasía sin un solo dato real, puedes saltártelo y pasar a
    [Estructura y redacta](write.md) — Bookwright no te cobra nada por no usarlo. Lo
    incluimos porque, en cuanto tu historia toca el mundo, esta capa es lo que
    separa la verosimilitud del error que un lector pillará.

## Enciende la investigación

La capa de investigación se activa en `manifest.toml`. Pídeselo a tu agente:

```text
activa la investigación con procedencia en el manifiesto
```

Dejará el bloque así (es texto plano; también puedes editarlo tú):

```toml title="manifest.toml"
[research]
enabled = true
source_languages = []                # idiomas extranjeros de tus fuentes (ISO 639-1)
min_reliability_for_anchor = "media" # respaldo mínimo para que un hallazgo sea ancla
```

## Investiga un tema

Ahora pídele a la skill que investigue lo que tu historia da por sentado. Para
*La hija del farero*, cómo se encendía un faro antes de la electricidad:

```text
/bookwright-research cómo funcionaban las lámparas de los faros antes de la luz eléctrica
```

La skill **investiga con rigor** y deja el resultado como **hallazgos con
procedencia completa** bajo `bible/research/`, distinguiendo lo que es un dato
documentado de lo que sigue siendo una pregunta abierta. No escribe prosa de tu
manuscrito ni inventa: documenta y **cita**. El resultado se parece a esto:

```yaml title="bible/research/faros.md (front-matter)"
findings:
  - id: lampara-aceite
    claim: "Antes de la electrificación, los faros usaban lámparas de aceite
            (colza o esperma de ballena) con mecha, recargadas a mano cada noche."
    sources: ["Manual de alumbrado marítimo"]
sources:
  - name: "Manual de alumbrado marítimo"
    reference: "..."
    type: secundaria
    reliability: alta
    reliability_justification: "Obra técnica de referencia del sector."
```

Cada fuente lleva su **procedencia**: tipo, fiabilidad y por qué, la cita en lengua
original, la fecha de acceso. Así el grafo no dice solo «esto es verdad», sino
«**esto lo dice tal fuente, con esta fiabilidad**» — y tú, y tus lectores, podéis
rastrearlo.

## De hallazgo a ancla

Un hallazgo es algo que sabes. Un **ancla** es un hallazgo **promovido a regla
vinculante**: ata un hecho a una entidad de tu biblia (un personaje, un lugar, una
fecha) de modo que la ficción **deba** respetarlo. En una novela histórica
escribirías un ancla del tipo «la fábrica abrió en 1851», y a partir de ahí:

- el validador **`factual_anchor`** comprueba en automático que ningún evento de tu
  línea de tiempo contradiga esa fecha;
- la skill **`/bookwright-verify`** (post-redacción) lee tu prosa y caza
  anacronismos —un teléfono en 1851— que un grafo no puede ver.

Nuestro cuento atemporal no necesita anclas de fecha, así que nos quedamos con el
hallazgo como guía de verosimilitud. El modelo completo —Source, Finding, Anchor y
las dos capas de verificación— está en
[Investigación con procedencia](../concepts/research.md).

!!! tip "La investigación entra en la cola de trabajo"
    Las preguntas que dejes abiertas (`open: true`) y las anclas sin resolver las
    recoge `bookwright status`, y tu agente te las recordará como trabajo pendiente
    cuando vuelvas a sentarte. Es el [hilo conductor](../concepts/orchestration.md):
    nunca pierdes el hilo de lo que falta por averiguar.

Con el mundo poblado y los hechos asegurados, toca darle forma a la trama y
escribir.

<div class="result" markdown>
**Siguiente:** [Estructura y redacta →](write.md)
</div>
