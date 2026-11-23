"""
Señales de `accounts`. Los módulos de abajo escuchan sin que `accounts` dependa
de ellos (09-arquitectura.md §2).

- `account_created(account, policy_version, consents)`: `entitlements` crea la
  concesión Free y `privacy` guarda la aceptación y los consentimientos.
"""
from django.dispatch import Signal

account_created = Signal()
