# Workshop 1: Requerimientos, historias de usuario y story map

**Proyecto:** HanziApp, aplicación web para aprender el vocabulario del HSK 3.0 (niveles 1 a 6) con repaso espaciado y práctica de escritura.
**Curso:** Ingeniería de Software II, semestre 2026-II, Universidad Nacional de Colombia.
**Docente:** Ing. Liliana Marcela Olarte, M.Sc.

**Equipo:**
- Juan Pablo Zuluaga Galindo
- Camilo Andrés Salinas Cuervo
- Daniel Santiago Rincón Santofimio
- Nicolás Fuentes Ramos
- Luis Alejandro Sanchez

## Entregable

El documento completo está en [`Workshop-1-HanziApp.pdf`](./Workshop-1-HanziApp.pdf).

| Sección | Contenido | Página del PDF |
|---|---|---|
| [1. Documentación de requerimientos](#1-documentación-de-requerimientos) | Descripción del producto, roles, reglas de negocio, requerimientos funcionales y no funcionales | pág. X |
| [2. Historias de usuario](#2-historias-de-usuario) | Historias por épica con criterios de aceptación | pág. X |
| [3. User story map](#3-user-story-map) | Backbone de actividades, mapa de historias y releases | pág. X |
| Referencias | Fuentes consultadas | pág. X |

## 1. Documentación de requerimientos

Define qué debe hacer HanziApp y con qué atributos de calidad.

- **Roles:** visitante, estudiante, profesor y administrador.
- **Reglas de negocio:** 14 reglas (RN-01 a RN-14), entre ellas el estado de repaso global por palabra y por carácter, la definición de palabra aprendida y el cálculo de la racha.
- **Requerimientos funcionales:** 65 requerimientos (RF-01 a RF-65) organizados en 11 módulos.
- **Requerimientos no funcionales:** 37 requerimientos (RNF-01 a RNF-37) organizados según las características de calidad de la norma ISO/IEC 25010, incluido el cumplimiento de la Ley 1581 de 2012.
- **Priorización:** MoSCoW (Must, Should, Could, Won't).

## 2. Historias de usuario

- **62 historias** (HU-01 a HU-62) agrupadas en 11 épicas.
- Formato: *Como [rol], quiero [acción] para [beneficio]*.
- Criterios de aceptación en formato *Dado [contexto], cuando [evento], entonces [resultado]*, incluyendo casos de excepción.
- Cada historia indica los requerimientos funcionales que implementa, lo que da trazabilidad completa entre requerimientos e historias.

## 3. User story map

![User story map de HanziApp](./assets/story-map-hanziapp.pdf)

El backbone tiene 9 actividades ordenadas según el recorrido del usuario y las dependencias entre ellas. Las historias se agrupan en releases:

| Release | Nombre | Prioridad | Historias |
|---|---|---|---|
| Release 1 | MVP: Estudiar y recordar | Must | 34 |
| Release 2 | Experiencia completa y bilingüe | Should | 14 |
| Release 3 | Aulas y motivación | Could | 13 |
| Futuro | Pronunciación | Won't | 1 |


## Referencias

- Atlassian. *Product requirements documents*. https://www.atlassian.com/agile/product-management/requirements
- MacKay, J. (2019). *A Guide to User Story Mapping*. Planio. https://plan.io/blog/user-story-mapping/
- Patton, J. (2014). *User Story Mapping*. O'Reilly Media.
- Cohn, M. (2004). *User Stories Applied*. Addison-Wesley.
- ISO/IEC 25010:2011 e ISO/IEC/IEEE 29148:2018.
- Ley Estatutaria 1581 de 2012 y Decreto 1377 de 2013 (Colombia).
- W3C. *Web Content Accessibility Guidelines (WCAG) 2.1*.
