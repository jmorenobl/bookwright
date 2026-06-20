# Propp — Funciones narrativas y dramatis personae

Referencia de dominio para la estructura. La consultan `bookwright-outline` (al
montar arcos y estructura) y `bookwright-scenes` (al asignar a cada escena su
función narrativa). Úsala **solo** si la constitución activó el vocabulario de
Propp en "Vocabularios activos"; si no, es material de consulta opcional.

## Qué aporta Propp

Vladimir Propp analizó el cuento maravilloso y observó que, bajo la variedad
superficial, las historias reutilizan un repertorio limitado de **funciones**:
unidades de acción definidas por su papel en el desarrollo de la trama, no por
quién las ejecuta. Su valor para Bookwright es doble: dar a cada escena una
**función** identificable (que justifica su existencia) y detectar huecos
estructurales (una promesa sin pago, un villano sin fechoría).

## Canonical match-names

Las 31 funciones de Propp, en su orden canónico. Cuando el vocabulario de Propp
está activo, una función narrativa (`functions:` en una ficha de unidad) cuyo
nombre coincida con cualquiera de estos nombres — en inglés o en español, sin
distinguir mayúsculas ni acentos — se tipa automáticamente contra el término
correspondiente. Cada línea lista los nombres equivalentes separados por `/`;
úsalos **literalmente** para que la función quede tipada. La función #8 es la
casilla combinada villanía/carencia de Propp, así que admite los cuatro nombres.

- absentation / alejamiento
- interdiction / prohibición
- violation / transgresión
- reconnaissance / interrogatorio
- delivery / información
- trickery / engaño
- complicity / complicidad
- villainy / lack / fechoría / carencia
- mediation / mediación
- counteraction / principio de la acción contraria
- departure / partida
- donor function / primera función del donante
- hero reaction / reacción del héroe
- acquisition / recepción del objeto mágico
- guidance / desplazamiento
- struggle / combate
- branding / marca
- victory / victoria
- liquidation / reparación
- return / regreso
- pursuit / persecución
- rescue / socorro
- unrecognized arrival / llegada de incógnito
- unfounded claims / pretensiones engañosas
- difficult task / tarea difícil
- solution / realización de la tarea
- recognition / reconocimiento
- exposure / desenmascaramiento
- transfiguration / transfiguración
- punishment / castigo
- wedding / boda

Cada escena debería poder etiquetarse con la función que cumple. Una escena que
no avanza ninguna función suele ser una escena que sobra.

## Dramatis personae (las siete esferas de acción)

> **Contexto, no match-names.** Esta sección describe los *roles* de personaje, que
> se tipan vía los actantes de Greimas (`narrative_roles:`, ver
> `references/greimas-actants.md`), **no** vía una función de Propp. Los nombres de
> abajo no tipan funciones; los match-names de Propp son sólo los de la sección
> "Canonical match-names".

Propp agrupa a los personajes por la **esfera de acción** que ocupan, no por su
identidad. Un mismo personaje puede cambiar de esfera; varias personas pueden
compartir una:

- **Héroe** — quien repara la carencia o vence; sigue el recorrido central.
- **Antagonista / villano** — causa la fechoría y se opone al héroe.
- **Donante** — provee el medio (objeto, saber) tras una prueba.
- **Auxiliar** — ayuda al héroe en la misión.
- **Princesa (y su padre)** — el objeto buscado y quien fija/recompensa la tarea.
- **Mandatario** — quien envía al héroe a la misión.
- **Falso héroe** — reclama el mérito ajeno; será desenmascarado.

Estas esferas conversan con `narrative_roles` en las fichas de personaje y con el
modelo actancial de Greimas (ver `references/greimas-actants.md`), que ofrece una
lectura más abstracta de las mismas fuerzas.
