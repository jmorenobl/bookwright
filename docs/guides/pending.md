# Resolver pendientes `[PENDING]`

Cuando una skill no puede rellenar un dato a partir de tu *brief*, no se lo
inventa: escribe un marcador `[PENDING: ¿pregunta concreta?]` en su sitio y
**continúa**. Esta guía explica cómo trabajar con esos marcadores — el mecanismo
que deja avanzar sin fabricar canon. El *porqué* de este diseño está en
[El loop de autoría](../concepts/authoring.md).

## Cómo se ve un pendiente

```markdown
## Voz y registro
- **Voz narrativa**: [PENDING: ¿(primera/tercera persona, omnisciente/limitada)?]
- **Tono**: sobrio, de cuento.
```

El marcador es **texto plano** dentro de tu artefacto. Lo lees, lo buscas con
`grep`, lo versionas — como todo lo demás.

## El loop, en tres movimientos

### 1. Lista lo que está abierto

```text
/bookwright-clarify
```

La skill recorre todo el proyecto y te devuelve la lista de dudas abiertas que
conviene resolver antes de seguir. Es de **solo lectura**: no toca nada, solo
informa.

!!! tip "También por la CLI"
    `bookwright status` cuenta las preguntas abiertas de investigación bajo
    `state.open_questions`, y su orquestación las enruta a la skill adecuada. Para
    los `[PENDING]` dentro de artefactos, `grep -rn "\[PENDING" .` es el atajo
    más rápido.

### 2. Resuélvelo donde está

Edita el archivo y sustituye el marcador por el dato real. Puedes hacerlo a mano
(es texto plano) o volcando la respuesta en tu *brief* y reinvocando la skill.

### 3. Reinvoca la skill: actualiza in situ

```text
/bookwright-constitution he respondido la voz narrativa en idea.md
```

Cuando vuelves a invocar la skill, **respeta tu prosa y los pendientes ya
resueltos**: solo rellena lo que sigue abierto. No duplica ni sobrescribe lo que
ya hay.

## `[PENDING]` que callan a un validador

Algunos pendientes no son solo huecos cosméticos: **apagan** un chequeo. El caso
canónico es la voz narrativa. Mientras la constitución diga

```markdown
- **Voz narrativa**: [PENDING: ¿(primera/tercera persona, omnisciente/limitada)?]
```

el validador [`focalization`](interpret-validation.md) no puede ejecutarse y
`bookwright validate` lo reporta como **no evaluado**. No es un error — pero es
canon sin vigilar. Respóndelo y el validador despierta solo:

```markdown
- **Voz narrativa**: Tercera persona limitada, centrada en Mara.
```

!!! info "¿Detenerse o seguir?"
    Una skill no siempre marca `[PENDING]` y sigue. Si rellenar el hueco exigiera
    **decidir el rumbo de la obra** —la motivación central del protagonista, el
    modelo estructural del que cuelga todo el outline, o algo que contradiría lo
    ya escrito—, la skill **se detiene y te pregunta** antes de escribir. El
    marcador es para datos; la pausa, para decisiones.

## Comprobar que un artefacto está cerrado

```text
/bookwright-checklist
```

Comprueba si **un artefacto concreto está completo**: todas sus secciones, sin
`[PENDING]` sin resolver, sin placeholders vacíos. Úsalo antes de dar por bueno un
documento y pasar al siguiente paso del *pipeline*.
