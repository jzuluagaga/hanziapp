# E08 · Organizar

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 solo se detalla HU-E08-01.

---

### HU-E08-01 · Ver los mazos de cada nivel
**Como** estudiante **quiero** ver los mazos de cada nivel con lo nuevo, lo pendiente y lo bloqueado **para** elegir qué estudiar.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-MAZ-01, R-MAZ-02, R-CON-16, R-DER-11 · **Necesita:** HU-E13-01, HU-E11-01

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado un nivel cargado, cuando se arman los mazos del sistema, entonces cada palabra vigente está en exactamente un mazo, en el orden del sílabo, con el tamaño de su nivel y el resto en el último | `test_e08_01_system_decks_partition_level` |
| 2 | Dado mazos ya armados, cuando se vuelve a ejecutar la construcción, entonces no se duplican ni cambian de identificador | `test_e08_01_build_system_decks_idempotent` |
| 3 | Dado un mazo, cuando lo ve, entonces aparecen cuántas palabras tiene, cuántas nuevas, cuántas pendientes y cuántas en revisión | `test_e08_01_deck_counts` |
| 4 | Dado un nivel con contenido a medias, cuando ve la lista de niveles, entonces aparece con las publicadas sobre el total del sílabo | `test_e08_01_level_shows_published_over_total` |
| 5 | Dado un nivel fuera del plan, cuando lo ve, entonces aparece bloqueado con el plan que lo desbloquea, sin ocultarlo | `test_e08_01_locked_levels_show_unlocking_plan` |

- **Derechos:** consulta `study.level.N`; quien no lo tiene ve el nivel bloqueado.
- **Idioma:** los mazos y niveles se nombran por clave (`decks.deckFull`); las cuentas dependen del idioma de estudio.
- **Guardado:** no aplica.
- **Analítica:** `deck_viewed`.
- **Datos personales:** no aplica.
- **Fuera de alcance:** mazos propios (`HU-E08-02`, V2).
