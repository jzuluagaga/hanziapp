# E14 · Operar el producto

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 solo se detalla HU-E14-01.

---

### HU-E14-01 · Ver si vuelven y si aprenden
**Como** dueño **quiero** un tablero con la retención a 1, 7 y 28 días y los aciertos por intervalo **para** decidir si sigo con V2.
**Corte:** V1a · **Tipo:** O · **Reglas:** R-DAT-07 · **Necesita:** HU-E00-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado cuentas activadas con días activos conocidos, cuando se calcula `M-03`, entonces da la proporción con día activo exactamente el día 1, 7 y 28, por cohorte | `test_e14_01_retention_by_day` |
| 2 | Dado cuentas activadas, cuando se calcula `M-02`, entonces da la proporción con algún día activo entre el 22 y el 28 desde su registro | `test_e14_01_week4_retention` |
| 3 | Dado respuestas contadas, cuando se calcula `M-04`, entonces da los aciertos sin refuerzos por tramo de intervalo programado y por habilidad | `test_e14_01_accuracy_by_interval` |
| 4 | Dado alguien que no es dueño, cuando abre el tablero, entonces no puede verlo | `test_e14_01_dashboard_staff_only` |

- **Derechos:** solo el dueño (personal con permiso `owner`).
- **Idioma:** no aplica; el tablero vive en el panel de Django.
- **Guardado:** no aplica.
- **Analítica:** no aplica; lee los eventos y no emite.
- **Datos personales:** muestra agregados por cohorte, nunca cuentas individuales.
- **Fuera de alcance:** gestión de personas (`HU-E14-02`, V2).
