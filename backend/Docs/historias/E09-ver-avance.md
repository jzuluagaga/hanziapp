# E09 · Ver avance y mantener el hábito

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 se detallan HU-E09-01 y HU-E09-02.

---

### HU-E09-01 · Ver mi progreso
**Como** estudiante **quiero** ver cuántas palabras y caracteres he aprendido y mi avance por nivel **para** saber cuánto me falta.
**Corte:** V1b · **Tipo:** U · **Reglas:** R-PRO-05, R-PRO-06, R-REP-12 · **Necesita:** HU-E03-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado estados de repaso, cuando se calcula el progreso, entonces una palabra está aprendida con estabilidad de lectura de `learned_stability_days` o más, y un carácter con la de escritura | `test_e09_01_learned_threshold` |
| 2 | Dado una palabra en varios mazos, cuando se cuenta, entonces cuenta una sola vez, y las retiradas no cuentan | `test_e09_01_counts_each_word_once` |
| 3 | Dado un nivel, cuando se muestra su avance, entonces son las aprendidas sobre el total del sílabo, junto a cuántas están publicadas | `test_e09_01_level_progress` |
| 4 | Dado una palabra aprendida, cuando recibe un "No recordé", entonces deja de contar como aprendida | `test_e09_01_learned_can_be_lost` |

- **Derechos:** el progreso de niveles que ya no se pueden estudiar sigue visible (`R-DER-08`).
- **Idioma:** claves `progress.*`.
- **Guardado:** no aplica; es un valor derivado.
- **Analítica:** `progress_viewed`.
- **Datos personales:** no guarda nada nuevo.
- **Fuera de alcance:** meta de examen (`HU-E09-03`, V2).

### HU-E09-02 · Mantener mi racha
**Como** estudiante **quiero** ver mi racha y saber qué la mantiene **para** sostener el hábito sin castigos injustos.
**Corte:** V1a · **Tipo:** U · **Reglas:** R-PRO-01, R-PRO-02, R-PRO-03, R-PRO-04, R-PRO-09 · **Necesita:** HU-E03-02

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una respuesta a la 1:30 a. m. en la zona horaria del estudiante, cuando se le asigna día, entonces pertenece al día anterior | `test_e09_02_local_day_rollover` |
| 2 | Dado un día cerrado, cuando se clasifica, entonces es activo si cambió algún estado de repaso, exento si no había nada pendiente y fallado si lo había | `test_e09_02_day_classification` |
| 3 | Dado una secuencia de días, cuando se calcula la racha, entonces cuenta los días activos desde el último fallado; un exento no la rompe ni la aumenta | `test_e09_02_streak_rules` |
| 4 | Dado un día ya cerrado, cuando cambian después las tarjetas o el plan, entonces su estado no se recalcula | `test_e09_02_day_status_fixed_once` |
| 5 | Dado el día en curso sin actividad, cuando se calcula la racha, entonces no cuenta como fallado | `test_e09_02_today_never_missed_before_close` |

- **Derechos:** "que pudiera estudiar" se evalúa con el plan vigente al cerrar el día.
- **Idioma:** claves `streak.*`.
- **Guardado:** el estado del día se guarda una vez al cerrarse; si la tarea no corrió, se cierra al primer acceso.
- **Analítica:** `day_closed`, `streak_changed`.
- **Datos personales:** estados de los días; se borran con la cuenta.
- **Fuera de alcance:** recordatorios por correo (`HU-E09-04`, V3).
