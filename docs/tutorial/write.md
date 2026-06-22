# 4. Estructura y redacta

Tienes el canon y, si lo necesitabas, los hechos. Ahora bajas del *qué* al *cómo*:
la forma de la trama (outline), su desglose en escenas concretas, y por fin la
**prosa**. Tres skills, en orden.

## Traza el esqueleto

```text
/bookwright-outline traza los arcos y la estructura del cuento
```

La skill lee la constitución y la biblia y escribe el esqueleto narrativo:

- `outline/arcs.md` — el recorrido de cada personaje (estado inicial → quiebre → final).
- `outline/structure.md` — el modelo (tres actos, etc.), los latidos mayores y el mapa de capítulos.
- `outline/synopsis.md` — una sinopsis inicial.
- `outline/units/*.md` — una ficha por **beat** de la trama.

Esas fichas de `outline/units/` son especiales: **sí** entran al grafo como
unidades narrativas (a diferencia de los arcos y la estructura, que son prosa de
autor). Si activaste un vocabulario como Propp, la skill etiqueta cada beat con su
función. Es la base de la [estructura narrativa](../concepts/narrative-structure.md)
que el sistema puede después recorrer y validar.

## Desglosa en escenas

```text
/bookwright-scenes desglosa el primer capítulo en escenas
```

La skill convierte la estructura en una lista de **escenas concretas** en
`outline/scenes.md`, cada una identificada por capítulo y posición (`1.1`, `1.2`…)
y anotada con su función, los personajes presentes, el lugar y los *beats* (qué
cambia). La regla de oro: si una escena no cambia nada, sobra.

```text title="outline/scenes.md (extracto)"
### 1.1 — La subida al faro
- Función: arranque; establece a Mara y su soledad.
- Personajes: Mara.
- Lugar: el faro, antes del alba.
- Beats: Mara sube a encender la lámpara; sabemos que es la única que queda.
```

## Redacta la primera escena

`/bookwright-draft` es **la única skill que produce prosa de manuscrito**. Le pasas
el identificador de la escena:

```text
/bookwright-draft 1.1
```

La skill lee la ficha de la escena `1.1`, la constitución (voz, tono, tiempo) y las
fichas de los personajes presentes, decide el capítulo destino y escribe la prosa
en `manuscript/cap-01.md`, respetando la voz declarada. Donde la biblia no resuelva
un dato necesario, marca `[PENDING]` en vez de inventar.

```markdown title="manuscript/cap-01.md"
Mara subió los ciento veinte peldaños del faro antes del alba. La lámpara
necesitaba aceite, y ella era la única que quedaba para encenderla.
```

!!! note "Hemos escrito solo la escena de apertura"
    En ella aparece Mara, pero **todavía no Tobías** — su escena llega más
    adelante en el cuento. Es algo de lo más normal a mitad de un libro: una ficha
    de la biblia que aún no ha entrado en el manuscrito. Justo eso es lo que vamos a
    hacer aflorar en el siguiente paso.

Ya tienes canon, estructura y una escena escrita. Llega el momento más útil de
Bookwright: **revisar** que todo encaje y **rehacer** lo que no.

<div class="result" markdown>
**Siguiente:** [Revisa y vuelve atrás →](revise.md)
</div>
