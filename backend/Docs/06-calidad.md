# 06 · Calidad

**Para qué sirve:** lista los requisitos de calidad que se pueden medir, cada uno con su umbral y con la forma exacta de comprobarlo. Si un requisito no se puede verificar con una prueba, una herramienta o una revisión fechada, no entra en este archivo.

**Tope de extensión:** 140 líneas. **Estado:** primera versión (15 nov 2026).

**Convenciones**

- ID: `Q-nn`. No se reutiliza.
- "Desde" indica el corte a partir del cual el requisito debe cumplirse.
- Los umbrales de rendimiento y disponibilidad están fijados para la arquitectura actual: un servidor y una base (`09-arquitectura.md`, sección 8). Son puntos de partida míos, no mediciones; se ajustan con la primera prueba de carga.

---

## 1. No perder datos

| ID | Requisito | Umbral | Cómo se verifica | Desde |
|---|---|---|---|---|
| Q-01 | Guardar una respuesta es rápido | El servidor responde en 300 ms o menos en el percentil 95, con 50 estudiantes respondiendo a la vez | Prueba de carga `load_answer_submit` antes de cada corte | V1a |
| Q-02 | Ninguna respuesta se pierde ni se duplica | 1.000 respuestas enviadas con cortes de red, recargas y envíos dobles producen exactamente 1.000 efectos | `test_answers_exactly_once_under_chaos` | V1a |
| Q-03 | Pasar de tarjeta no espera a la red | La siguiente tarjeta aparece en 100 ms o menos tras responder, con la red simulada lenta | `e2e_next_card_does_not_wait_for_network` | V1a |
| Q-04 | Las copias de seguridad sirven | Copia diaria, conservada 30 días; pérdida máxima de 24 h; restauración completa en 4 h o menos | Restauración real en un entorno aparte, una vez por corte y luego cada mes; fecha y duración anotadas en `ops` | V1a |
| Q-05 | Reanudar es exacto | Tras cerrar a mitad de sesión en cualquier habilidad, se vuelve a la primera tarjeta sin responder, en el mismo u otro dispositivo | `e2e_resume_exact_recognition`, `e2e_resume_exact_listening`, `e2e_resume_exact_writing` | V1a (escritura: V1b) |

## 2. Rendimiento y disponibilidad

| ID | Requisito | Umbral | Cómo se verifica | Desde |
|---|---|---|---|---|
| Q-06 | La búsqueda responde rápido | 300 ms o menos en el percentil 95 con las 5.400 palabras cargadas | `load_dictionary_search` | V1b |
| Q-07 | Las páginas públicas cargan rápido en móvil | Contenido principal visible en 2,5 s o menos con conexión 4G simulada | Lighthouse en integración continua sobre inicio y una ficha | V2 |
| Q-08 | El servicio está disponible | 99 % mensual en V1; 99,5 % desde V2 | Monitor externo cada minuto sobre una ruta de salud que consulta la base; informe mensual | V1a |
| Q-09 | Los fallos se detectan solos | Todo error no controlado del servidor o de la interfaz genera una alerta en 5 minutos o menos | Error provocado a propósito tras cada despliegue a producción | V1a |

## 3. Seguridad y privacidad

| ID | Requisito | Umbral | Cómo se verifica | Desde |
|---|---|---|---|---|
| Q-10 | Nadie accede a datos de otra cuenta | Toda ruta que devuelve o modifica datos de una cuenta rechaza a cualquier otra | `test_authz_matrix`: recorre todas las rutas con una cuenta ajena; una ruta nueva sin caso en la matriz hace fallar la prueba | V1a |
| Q-11 | Las credenciales están protegidas | Contraseñas con el algoritmo de derivación por defecto de Django o Argon2; credencial de acceso solo en cookie httpOnly, Secure y SameSite; todo el tráfico por HTTPS | `test_password_hasher`, `test_auth_cookie_flags`, `test_http_redirects_to_https` | V1a |
| Q-12 | El acceso resiste intentos repetidos | Se cumple `R-CTA-08`; además, límite de peticiones por dirección en registro, acceso y recuperación | `test_login_lockout`, `test_rate_limit_auth_endpoints` | V1a |
| Q-13 | Sin dependencias con fallos conocidos graves | Ninguna vulnerabilidad crítica o alta sin tratar | Auditoría de dependencias en integración continua, en servidor e interfaz | V1a |
| Q-14 | Los eventos no llevan datos personales | Ningún evento contiene nombre, correo, texto libre ni audio (`R-DAT-07`) | `test_event_schemas_have_no_pii`: cada evento tiene un esquema cerrado y la prueba rechaza campos no declarados | V1a |
| Q-15 | Eliminar una cuenta la elimina de verdad | Tras eliminar, no queda ninguna fila ni archivo vinculado a la cuenta, salvo lo que `R-DAT-06` permite conservar sin vínculo | `test_account_deletion_leaves_no_trace`: crea una cuenta con datos en todos los módulos, la elimina y busca su identificador en toda la base y en el almacenamiento | V1b |
| Q-16 | Los plazos de conservación se cumplen | Las grabaciones de voz y las cuentas de invitado caducadas se borran en el plazo configurado | `test_retention_jobs` con datos ficticios y reloj simulado | V1a (voz: datos ficticios) |

## 4. Idioma, accesibilidad y dispositivos

| ID | Requisito | Umbral | Cómo se verifica | Desde |
|---|---|---|---|---|
| Q-17 | Añadir un idioma no toca código ni esquema | Se cumplen las ocho pruebas de `R-IDI-10` | Las listadas en `03-reglas-de-negocio.md`, sección 2 | V1a |
| Q-18 | Los flujos centrales son accesibles | Sin incumplimientos graves de WCAG 2.1 nivel AA en registro, acceso, sesión de estudio y ficha | Análisis automático de accesibilidad en las pruebas de extremo a extremo, más una revisión manual con lector de pantalla por corte | V1a |
| Q-19 | Se puede estudiar solo con teclado | Revelar, calificar, oír el audio y deshacer tienen atajo, y el foco es siempre visible | `e2e_study_session_keyboard_only` | V1a |
| Q-20 | Funciona en un teléfono pequeño | Sin desplazamiento horizontal desde 360 px de ancho; todo control táctil mide 44 px o más; la escritura funciona con el dedo | `e2e_viewport_360` y prueba manual de escritura en un teléfono real por corte | V1a (escritura: V1b) |
| Q-21 | Funciona en los navegadores habituales | Dos últimas versiones de Chrome, Safari (incluido iOS), Firefox y Edge | Pruebas de extremo a extremo en los tres motores | V1a |

## 5. Corrección del aprendizaje y del contenido

| ID | Requisito | Umbral | Cómo se verifica | Desde |
|---|---|---|---|---|
| Q-22 | El calendario de repasos es correcto y reproducible | El adaptador da los mismos intervalos que la librería de FSRS fijada, para una batería de secuencias de referencia | `test_fsrs_adapter_reference_vectors`; la versión de la librería está fijada y subirla exige volver a generar la batería | V1a |
| Q-23 | Todo lo publicado pasó revisión | El 100 % de las versiones publicadas tiene todas sus validaciones aprobadas y un revisor registrado | `test_cannot_publish_with_failed_validation` y la consulta `audit_published_without_review`, que debe devolver cero filas | V1a |
| Q-24 | El contenido publicado tiene pocos errores | Menos del 1 % de las palabras publicadas de un nivel con un reporte de error confirmado en sus primeros 90 días | Consulta sobre los reportes resueltos, revisada cada mes | V1b |

## 6. Mantenibilidad y costos

| ID | Requisito | Umbral | Cómo se verifica | Desde |
|---|---|---|---|---|
| Q-25 | Cada criterio de aceptación tiene su prueba | Todo nombre de prueba citado en `docs/historias/` existe en el código y pasa | Script de verificación de `00-indice.md`, ejecutado en integración continua | V1a |
| Q-26 | La lógica crítica está cubierta | 90 % o más de cobertura de ramas en `scheduling`, `study`, `entitlements` y `progress` | Informe de cobertura en integración continua; por debajo del umbral no se fusiona | V1a |
| Q-27 | Nada llega a producción sin pasar las pruebas | La rama principal solo acepta cambios con la integración continua en verde | Regla de protección de la rama | V1a |
| Q-28 | Los cambios de esquema son seguros | Toda migración se aplica sobre una copia de los datos de producción antes de desplegar y tiene vuelta atrás probada | Paso de la integración continua `migrate_on_snapshot` | V1a |
| Q-29 | El gasto está acotado | El gasto mensual en servicios con costo variable no supera el tope configurado (`R-DER-10`); al 80 % se avisa | `test_global_budget_pauses_feature` y alerta de gasto | V1a (tope), V4 (uso real) |
| Q-30 | La documentación no se rompe | Todo ID citado en `docs/` existe y ningún archivo supera su tope de extensión | Script de verificación de `00-indice.md` | V1a |

## 7. Lo que no está aquí, a propósito

- **Escalabilidad a miles de usuarios concurrentes.** No hay usuarios todavía; se fijará un umbral cuando la prueba de carga de `Q-01` muestre dónde está el límite real.
- **Modo sin conexión e instalación como aplicación.** Fuera del producto (`D-03`).
- **"Cumplir OWASP" como requisito.** No es verificable tal cual; lo sustituyen `Q-10` a `Q-13`.
- **Plazos de respuesta a consultas y reclamos.** Son una obligación de operación, no del software; están en `R-DAT-09` y en la historia `HU-E14-02`.
