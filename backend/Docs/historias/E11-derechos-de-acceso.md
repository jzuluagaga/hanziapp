# E11 · Derechos de acceso

**Tope de extensión:** 160 líneas. **Estado:** primera versión (22 nov 2026). En V1 solo se detalla HU-E11-01.

---

### HU-E11-01 · Motor de derechos, límites y cuotas
**Como** dueño **quiero** que un solo punto decida qué puede hacer cada cuenta, con planes y concesiones como datos, **para** poder cobrar después sin rehacer el producto.
**Corte:** V1a · **Tipo:** H · **Reglas:** R-DER-01, R-DER-02, R-DER-03, R-DER-04, R-DER-05, R-DER-09, R-DER-13 · **Necesita:** —

| # | Criterio de aceptación | Prueba |
|---|---|---|
| 1 | Dado una cuenta registrada, cuando se consultan sus derechos, entonces tiene la concesión Free: estudiar HSK 1 y 2 y hasta `free_own_decks` mazos propios | `test_e11_01_default_free_grant` |
| 2 | Dado que se cambian las capacidades de un plan en la base, cuando se consultan los derechos, entonces rige el cambio sin tocar código | `test_e11_01_plan_is_data` |
| 3 | Dado varias concesiones, cuando se combinan, entonces rige la unión y, en límites, el mayor; una concesión vencida o futura no cuenta | `test_e11_01_grants_union_and_expiry` |
| 4 | Dado una concesión nueva, cuando se crea, entonces su efecto es inmediato aunque haya caché | `test_e11_01_new_grant_immediate` |
| 5 | Dado palabras de un nivel no permitido, cuando se arma una cola, entonces no entran, se cuentan como bloqueadas y se emite `entitlement_denied` si se pidió ese nivel | `test_e11_01_queue_respects_entitlements` |
| 6 | Dado una cuota, cuando se reserva, se confirma o se revierte, entonces el saldo cambia de forma atómica y un reintento no descuenta dos veces | `test_e11_01_quota_reserve_confirm_revert` |

- **Derechos:** es el objeto de la historia.
- **Idioma:** los planes se nombran por clave (`plan.free`, `plan.pro`).
- **Guardado:** no aplica.
- **Analítica:** `entitlement_denied`.
- **Datos personales:** concesiones y consumos ligados a la cuenta; se borran con ella.
- **Fuera de alcance:** comprar (`HU-E12-01`, V3); conceder a mano desde una pantalla propia (`HU-E11-03`, V2; mientras tanto, panel de Django).
