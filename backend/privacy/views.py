"""Rutas de cuenta y datos personales (Docs/10-api.md §4)."""
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from entitlements.services import allowed_levels, limit, plan_name
from users.services import local_day, profile_of
from users.views import profile_payload

from . import services


def me_payload(account) -> dict:
    current, accepted = services.current_policy(), services.accepted_policy(account)
    accepted_at = account.policy_acceptances.values_list("accepted_at", flat=True).first()
    return {
        "account": {"id": str(account.pk), "email": account.email, "email_verified": bool(account.email_verified_at),
                    "cohort": account.cohort, "created_at": account.date_joined},
        "profile": profile_payload(profile_of(account)),
        "plan": plan_name(account),
        "entitlements": {"levels": allowed_levels(account), "own_decks_max": limit(account, "decks.own.max")},
        "consents": services.consents(account),
        "policy": {"current": current, "accepted": accepted, "accepted_at": accepted_at, "required": accepted != current},
        "today": local_day(account),
    }


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(me_payload(request.user))

    def delete(self, request):
        services.delete_account(request.user, request.data.get("password", ""))
        return Response(status=204)


class PolicyAcceptView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        services.accept_policy(request.user, str(request.data.get("version", "")))
        policy = me_payload(request.user)["policy"]
        return Response({k: policy[k] for k in ("current", "accepted", "required")})


class ConsentSerializer(serializers.Serializer):
    granted = serializers.BooleanField()


class ConsentView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, purpose):
        s = ConsentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response(services.set_consent(request.user, purpose, s.validated_data["granted"]))
