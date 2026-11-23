"""
Registro de borrado (09-arquitectura.md §7): cada módulo declara en su servicio
una función `delete_account_data(account)` con lo que guarda de una cuenta.
`privacy` las llama en orden y no conoce las tablas de nadie.
"""
from importlib import import_module

MODULES = [
    "study.services",        # respuestas y sesiones
    "scheduling.services",   # estados de repaso e historial
    "progress.services",     # días y racha
    "users.services",        # intentos fallidos de acceso
]


def deleters():
    return {path: import_module(path).delete_account_data for path in MODULES}
