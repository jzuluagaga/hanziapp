from django.db import migrations

FREE = {"study.level.1": True, "study.level.2": True, "decks.own.max": 10}
PRO = {**{f"study.level.{n}": True for n in range(1, 7)}, "decks.own.max": 200,
       "pronunciation.assess": {"amount": 0, "period": "month"}}


def plans(apps, schema_editor):
    Plan = apps.get_model("entitlements", "Plan")
    Plan.objects.get_or_create(code="free", version=1, defaults={"capabilities": FREE, "is_current": True})
    Plan.objects.get_or_create(code="pro", version=1, defaults={"capabilities": PRO, "is_current": True})


class Migration(migrations.Migration):
    """Planes de R-DER-05 como datos. La cuota de pronunciación se fija en V4."""

    dependencies = [("entitlements", "0001_initial")]
    operations = [migrations.RunPython(plans, migrations.RunPython.noop)]
