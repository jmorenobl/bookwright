---
relationships: []
---

# Relaciones

<!--
Guía: registra aquí los vínculos sociales entre personajes. Cada relación es un
mapa `{ name, participants }`, donde `participants` es una lista de *slugs* de
personaje (el nombre de archivo de `bible/characters/<slug>.md`, sin extensión).
El indexador sólo lee la clave `relationships:` del frontmatter — mantenla como
única clave de nivel superior. Deja la lista vacía hasta rellenarla; los
ejemplos viven dentro de este comentario para que nunca se indexen. Ejemplo:

relationships:
  - name: "Lealtad fracturada"
    participants: ["ana-soler", "marco-vega"]
  - name: "Rivalidad heredada"
    participants: ["marco-vega", "elsa-roan"]
-->

## Cómo se rellena

- Añade cada vínculo como un ítem bajo `relationships:` en el frontmatter.
- `name` es obligatorio y nombra la naturaleza del vínculo, no a las personas.
- `participants` enumera los *slugs* de los personajes implicados; deben existir
  en `bible/characters/` para resolverse.

## Mapa de tensiones

<!-- Guía: en prosa, describe las alianzas y los conflictos que mueven la
     trama, y cómo evolucionan a lo largo del libro. -->

[PENDING: ¿Cuáles son las tres relaciones que más empujan el conflicto central?]
