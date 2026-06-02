# GOLEM — Relaciones sociales (`G4_Social_Relationship`, `G6_Relationship_Role`)

Referencia de dominio para `bible/relationships.md`. La consultan
`bookwright-bible` (al poblar los vínculos) y `bookwright-continuity` (al razonar
sobre la coherencia de las relaciones frente al manuscrito).

## Modelado reificado del vínculo

En GOLEM una relación social **no** es una arista simple "A quiere a B". Se
*reifica*: la relación es una entidad de pleno derecho (`G4_Social_Relationship`)
que conecta a dos o más participantes, y cada participante entra en ella a través
de un **rol** (`G6_Relationship_Role`). Esto permite que una misma relación
tenga roles asimétricos (mentor ↔ aprendiz, acreedor ↔ deudor) y que evolucione
sin perder identidad.

- **`G4_Social_Relationship`** — el vínculo en sí: "lealtad fracturada",
  "rivalidad heredada". Tiene nombre y participantes.
- **`G6_Relationship_Role`** — la posición que ocupa cada participante dentro de
  ese vínculo. Captura la asimetría: en una relación de deuda, uno es acreedor y
  otro deudor.

Lo que importa al escribir la biblia: nombra el **vínculo** por su naturaleza
("Lealtad fracturada"), no por las personas, y deja que los participantes y sus
roles se expresen por separado.

## Contrato del contenedor `relationships.md`

`bible/relationships.md` es un archivo **contenedor indexado**. Su frontmatter
lleva una única clave de nivel superior, `relationships:`, una lista de mapas:

```yaml
relationships:
  - name: "Lealtad fracturada"
    participants: ["ana-soler", "marco-vega"]
  - name: "Rivalidad heredada"
    participants: ["marco-vega", "elsa-roan"]
```

- `name` — obligatorio; nombra la **naturaleza** del vínculo, no a las personas.
- `participants` — lista de *slugs* de personaje; cada slug debe existir como
  `bible/characters/<slug>.md` o aparecerá como referencia sin resolver.
- **Mantén `relationships:` como única clave de nivel superior** del
  frontmatter. Cualquier otra clave dispara un aviso del indexador.
- El cuerpo en prosa ("mapa de tensiones") describe cómo evolucionan las
  alianzas y conflictos; no se indexa.

## Roles asimétricos en prosa

El frontmatter v0 captura el vínculo y sus participantes; la asimetría de roles
(quién es mentor, quién aprendiz) y su evolución se narran en el cuerpo en prosa
de `relationships.md` y en los arcos del outline, hasta que un manejador de roles
explícito llegue en una iteración posterior. No inventes claves de frontmatter
para los roles: descríbelos en prosa.
