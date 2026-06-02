# Protocolo `[PENDING: …]` — marcar y continuar vs. detenerse y preguntar

Esta es la regla compartida que todos los comandos generativos
(`bookwright-constitution`, `bookwright-bible`, `bookwright-outline`,
`bookwright-scenes`, `bookwright-draft`, `bookwright-synopsis`) siguen al
encontrar información que el brief o los artefactos existentes no proporcionan.
Es la única fuente de verdad de esta decisión: los cuerpos de los comandos
enlazan aquí en lugar de repetir la regla.

## El token

El marcador de relleno es exactamente `[PENDING: <pregunta en español>]`:

- El token `PENDING` se escribe **en inglés** y en mayúsculas.
- La pregunta que sigue se escribe **en español**, redactada como una pregunta
  concreta dirigida al autor (no una etiqueta genérica como `[PENDING]` a secas).
- Ejemplo: `[PENDING: ¿Desde qué distancia narrativa se cuenta la obra?]`.

Este es el mismo marcador que estampan las plantillas de la iteración 7, que
busca el barrido de centinelas y que evalúa `bookwright-checklist`. No inventes
variantes (`[PENDIENTE]`, `TODO`, `???`): romperían ese acuerdo.

## Marcar y continuar (caso por defecto)

Cuando el material disponible simplemente **carece** de un dato, escribe el
`[PENDING: …]` en su sitio y **continúa** con el resto del trabajo. No te
detengas a preguntar. Ejemplos de "carece de un dato":

- El brief no menciona el año de nacimiento de un personaje secundario.
- No se indica el tono exacto del registro coloquial.
- Falta el nombre de un lugar que aún no es relevante para la trama.

La obra puede avanzar con estos huecos marcados; el autor los resolverá después,
y una nueva invocación del comando los rellenará (regla de actualización en
sitio).

## Detenerse y preguntar (excepción)

Detente y consulta al autor **solo** cuando continuar exigiría inventar *canon
estructural* (load-bearing): un dato del que dependen otras decisiones y que no
puede derivarse de los artefactos existentes, o que **contradiría** algo ya
escrito. Ejemplos:

- La motivación central del protagonista (de ella cuelgan arco, escenas y
  desenlace).
- El modelo estructural de la obra cuando el outline depende por completo de él.
- Un hecho nuevo que chocaría con la constitución o con una ficha ya resuelta.

En estos casos, inventar sería peor que un hueco: propagaría una decisión
arbitraria por toda la obra. Formula una pregunta breve y precisa, y espera la
respuesta antes de escribir ese fragmento.

Regla mnemónica: **si el hueco solo te falta, márcalo; si rellenarlo te obliga a
decidir el rumbo de la obra, pregunta.**

## Comillas en YAML (campos de tipo cadena)

Cuando un `[PENDING: …]` cae dentro de un campo de frontmatter **de tipo
cadena** —el caso típico es `name:` en una ficha de personaje o de escenario—
debe ir **entre comillas**:

```yaml
name: "[PENDING: ¿Cómo se llama el personaje?]"
```

Sin comillas, los corchetes `[ … ]` se interpretan como una **lista YAML**: el
valor deja de ser una cadena, el indexador descarta la ficha y el dato se
pierde silenciosamente. Esto **solo** aplica a campos de cadena del frontmatter;
en el cuerpo en prosa el marcador se escribe sin comillas
(`[PENDING: ¿…?]`). Nunca pongas un `[PENDING]` en un campo numérico (`born`,
`died`): déjalo omitido en su lugar.
