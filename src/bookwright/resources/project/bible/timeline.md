---
events: []
---

# Línea de tiempo

<!--
Guía: registra aquí los hechos cronológicos de la obra. Cada evento es un
mapa `{ name, participants }`, donde `participants` es una lista de *slugs* de
personaje. El *slug* se deriva del campo `name` de la ficha (p. ej.
`name: "Ana Soler"` → `ana-soler`), no del nombre del archivo; nombra cada
`bible/characters/<slug>.md` con ese mismo slug para mantenerlos alineados.
El indexador sólo lee la clave `events:` del frontmatter — mantenla como única
clave de nivel superior. Deja la lista vacía hasta que el agente o tú la
rellenéis; los ejemplos viven dentro de este comentario para que nunca se
indexen. Ejemplo de lista poblada:

events:
  - name: "Caída del puente de Ardía"
    participants: ["ana-soler", "marco-vega"]
  - name: "Pacto en la torre"
    participants: ["ana-soler"]
-->

## Cómo se rellena

- Añade cada hecho como un ítem bajo `events:` en el frontmatter, no en el cuerpo.
- `name` es obligatorio y debe ser una cadena no vacía.
- `participants` es opcional; cada *slug* debe corresponder a un personaje real
  de `bible/characters/` o aparecerá como referencia sin resolver.
- El orden de la lista refleja el orden cronológico interno de la historia.

## Notas de cronología

<!-- Guía: usa esta sección en prosa para anclar fechas, saltos temporales o
     ambigüedades deliberadas que no encajan como eventos discretos. -->

[PENDING: ¿Cuál es el marco temporal global de la obra (época, duración, saltos)?]
