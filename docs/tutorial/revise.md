# 4. Revisa y vuelve atrás

Aquí está el corazón de Bookwright — y la parte más útil del día a día. Escribir un
libro es, sobre todo, **cambiar de idea**: descubrir un descuido, repensar un
personaje, rehacer una escena sin que se desmorone el resto. Este paso te enseña a
hacerlo con red.

## Comprueba la continuidad

Le pides a tu agente que revise tu manuscrito contra la biblia:

```text
/bookwright-continuity
```

La skill lee tu manuscrito y tu biblia, reconstruye el grafo y coteja tres ejes:
cumplimiento de la biblia, coherencia de los arcos y coherencia temporal. Es de
**solo lectura** — no toca nada, solo te informa. Sobre nuestro cuento te dirá algo
así:

```text
Desviación (cumplimiento de la biblia):
  · 'Tobías' está fichado en bible/characters/tobias.md pero no aparece en
    ninguna línea del manuscrito. ¿Falta su escena, o sobra la ficha?
```

**Lo ha visto.** Tobías está en tu biblia pero no en una sola línea de prosa: es un
personaje *huérfano*. Quizá su escena aún no la has escrito; quizá lo metiste y
cambiaste de idea. La continuidad te lo pone delante antes de que llegue a tu
lector.

!!! info "La misma comprobación, como puerta determinista"
    La skill se apoya en un validador determinista, `character_presence`. Si quieres
    el veredicto crudo —el mismo que corre en integración continua— puedes pedírselo
    al agente o ejecutarlo tú:

    ```text
    bookwright validate
    ```
    ```text
    character_presence:
      error: character 'Tobías' is defined in the bible but never mentioned in the
      manuscript — bible/characters/tobias.md
    ```
    Sale con código `1`: un personaje huérfano es severidad **`error`**, y los
    errores **bloquean**. Los `warning` (heurísticos: un nombre sin ficha, un posible
    salto de voz) avisan pero no bloquean. Lo cubre a fondo
    [Interpretar la validación](../guides/interpret-validation.md).

## Vuelve atrás y rehazlo

Hay dos formas honestas de resolverlo, y cuál elijas es **una decisión narrativa**,
no técnica:

- **Tobías importa** → vuelve atrás, dale su escena y redáctala.
- **Tobías sobra** → quítale la ficha de la biblia.

Hagamos la primera, que es la que enseña el bucle de iteración. Vuelves un paso
atrás, a las escenas, y le pides a tu agente que añada el beat de Tobías:

```text
/bookwright-scenes añade una escena donde Tobías llega en su barca y le trae
noticias del puerto a Mara
```

La skill **actualiza in situ**: conserva la escena `1.1` que ya tenías y añade la
nueva (`1.2`), sin renumerar ni borrar lo fijado. Ahora la redactas:

```text
/bookwright-draft 1.2
```

Y queda en el manuscrito:

```markdown title="manuscript/cap-01.md (añadido)"
Al mediodía, Tobías amarró su barca al espigón y le trajo noticias del puerto.
```

Vuelves a comprobar:

```text
/bookwright-continuity
```
```text
Sin desviaciones. El manuscrito es coherente con la biblia.
```

🎉 Acabas de recorrer el bucle completo de Bookwright: **destilar → escribir →
revisar → volver atrás → rehacer**. Y lo decisivo: rehiciste editando el canon y
re-invocando una skill, no peleándote con un chat que olvida. Cada skill respeta lo
que ya habías decidido, así que **cambiar de idea es barato**.

!!! tip "El otro camino, en una línea"
    Si Tobías sobrara, le habrías dicho a tu agente «elimina la ficha de Tobías de
    la biblia» y la continuidad quedaría limpia igual. Mismo bucle: editas el canon
    en texto plano, vuelves a comprobar.

## Verde de verdad: tres resultados, no dos

Una última idea que te ahorrará sustos. Comprobar no tiene dos respuestas (*bien* /
*mal*), sino **tres**. Si hubieras pedido la validación **recién creado el
proyecto**, antes de escribir nada, habrías visto:

```text
not evaluated:
  focalization [input gap]: the narrative-voice declaration is still unanswered ([PENDING])
  setting_continuity [input gap]: the manuscript is empty
```

Ni errores ni avisos… pero tampoco un «todo bien». Esos validadores **no pudieron
mirar**: no había prosa, ni una voz narrativa declarada. La etiqueta `[input gap]`
te lo dice: faltaba una entrada *tuya*. Un resultado vacío que se leyera como
«limpio» sería *falsa confianza*. (Verás también una entrada
`[known limitation — no action available yet]`: un límite permanente del enfoque, no
algo que tú puedas arreglar — esa **no** te impide el verde.)

!!! success "La definición de verde"
    Tu libro está realmente comprobado cuando **no hay errores _y_ ningún validador
    se quedó sin mirar por falta de una entrada tuya** (`status == "ok"` y ninguna
    entrada `not_evaluated` de tipo `missing_input`). Por eso te convino responder el
    `[PENDING]` de la voz narrativa en el [paso 1](distill.md): despertó al validador
    de focalización. Tu agente, al leer `bookwright status`, te recuerda cualquier
    validador dormido **accionable** como trabajo pendiente.

## Y a partir de aquí

Has visto el flujo entero con un cuento de dos personajes. Para llevarlo a un libro
de verdad:

- Entiende **por qué** funciona así en [Cómo piensa Bookwright](../concepts/index.md).
- Conoce las doce skills y el orden en que se apoyan unas en otras en
  [El loop de autoría](../concepts/authoring.md).
- Aprende a leer la validación a fondo en
  [Interpretar la validación](../guides/interpret-validation.md).
- Deja que `status` te diga siempre el siguiente paso:
  [Orquestación de contexto](../concepts/orchestration.md).
