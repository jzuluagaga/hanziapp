"""Pruebas de HU-E00-03, HU-E00-04 y de los requisitos Q-10 y Q-11."""
import re
import uuid
from datetime import datetime, timezone as tz
from unittest import mock

from django.contrib.admin.sites import site
from django.test import RequestFactory, TestCase, override_settings
from django.urls import get_resolver

from content.models import Word
from decks.services import build_system_decks
from hanzi_backend.testing import answer, at, client_for, make_level, make_word, publish_word, set_param, start, student
from languages.models import Language
from ops import params
from ops.models import AuditLog, Parameter

DAY1 = datetime(2026, 12, 1, 15, 0, tzinfo=tz.utc)
KEY = re.compile(r"^[a-z_]+$")


class E00Languages(TestCase):
    def test_add_language_without_migration(self):
        # (1) cargar: fila de idioma y contenido; (2) publicar; (3) encender interruptores. Nada más.
        Language.objects.create(code="xx", name="Xxlandés", is_study_active=True, is_ui_active=True)
        words = make_level(1, 5, publish="xx", meaning="xx-palabra")
        build_system_decks()
        user = student()
        c = client_for(user)
        self.assertEqual(c.patch("/api/v1/me/profile", {"study_language": "xx", "ui_language": "xx"}, format="json").status_code, 200)
        self.assertEqual(len(c.get("/api/v1/words/search", {"q": "xx-palabra"}).json()), 5)
        self.assertEqual(c.get(f"/api/v1/words/{words[0].pk}").json()["senses"][0]["meaning"], "xx-palabra")
        with at(DAY1):
            s = start(c).json()["session"]
            while s["status"] == "active":
                answer(c, s)
                s = c.get(f"/api/v1/sessions/{s['id']}").json()["session"]
        self.assertEqual(s["summary"]["answered"], 5)
        self.assertTrue(any(lang["code"] == "xx" for lang in client_for().get("/api/v1/config").json()["languages"]))

    def test_ui_and_study_language_independent(self):
        w = make_word(1, 1, "爱", meaning="amar")
        publish_word(w, "en", meaning="to love")
        Language.objects.filter(code="en").update(is_ui_active=True)
        user = student()
        c = client_for(user)
        c.patch("/api/v1/me/profile", {"ui_language": "en"}, format="json")
        me = c.get("/api/v1/me").json()["profile"]
        self.assertEqual((me["ui_language"], me["study_language"]), ("en", "es"))
        self.assertEqual(c.get(f"/api/v1/words/{w.pk}").json()["senses"][0]["meaning"], "amar")

    def test_system_names_translated(self):
        make_level(1, 3)
        build_system_decks()
        c = client_for(student())
        deck = c.get("/api/v1/decks?level=1").json()[0]
        level = c.get("/api/v1/levels").json()[0]
        for payload in (deck, level):
            self.assertFalse({"name", "title", "label"} & set(payload))
        self.assertEqual((deck["level"], deck["index"]), (1, 1))  # la interfaz arma «HSK 1 · Parte 1» por clave
        self.assertEqual(c.get("/api/v1/me").json()["plan"], "free")  # el plan es un código, no un nombre

    def test_e00_03_server_errors_are_translation_keys(self):
        c = client_for(student())
        responses = [
            client_for().get("/api/v1/me"),                                   # 401
            c.get("/api/v1/words/999999"),                                     # 404
            c.post("/api/v1/answers", {"client_id": "x"}, format="json"),      # 400 con campos
            c.patch("/api/v1/me/profile", {"new_limit_writing": 99}, format="json"),
            c.delete("/api/v1/me", {"password": "mala"}, format="json"),
        ]
        for r in responses:
            body = r.json()
            self.assertRegex(body["error"], KEY)
            for v in body["detail"].values():
                for code in v if isinstance(v, list) else [v]:
                    self.assertTrue(isinstance(code, int) or KEY.match(str(code)) or str(code).isdigit(), (r.status_code, body))


class E00Operations(TestCase):
    def test_e00_04_health_checks_database(self):
        c = client_for()
        self.assertEqual(c.get("/api/v1/health").json(), {"status": "ok"})
        with mock.patch("ops.views.connection.cursor", side_effect=Exception("base caída")):
            self.assertEqual(c.get("/api/v1/health").status_code, 503)

    def test_e00_04_signup_switch_closes_registration(self):
        set_param("signup_mode", "closed")
        r = client_for().post("/api/v1/auth/register", {"name": "A", "email": "a@b.co", "password": "clave-segura-123",
                                                         "policy_version": "2026-11", "is_adult": True}, format="json")
        self.assertEqual((r.status_code, r.json()["error"]), (403, "signup_closed"))
        self.assertEqual(client_for().get("/api/v1/config").json()["signup_mode"], "closed")

    def test_e00_04_parameter_change_is_audited(self):
        self.assertEqual(params.value("session_max_cards"), 50)  # valor inicial sin fila
        owner = student("dueno@example.com")
        request = RequestFactory().post("/admin/")
        request.user = owner
        admin = site._registry[Parameter]
        obj = Parameter(key="session_max_cards", value=40)
        admin.save_model(request, obj, form=None, change=False)
        self.assertEqual(params.value("session_max_cards"), 40)
        log = AuditLog.objects.get(action="parameter_changed")
        self.assertEqual((log.data["old"], log.data["new"], log.actor_id), (None, 40, owner.pk))


class Security(TestCase):
    PUBLIC = {"health", "config", "auth_register", "auth_login", "auth_refresh", "auth_google",
              "password_reset_request", "password_reset_confirm"}
    OWN = {"me", "me_profile", "me_policy_accept", "me_consent", "today", "progress", "levels", "decks", "deck_detail",
           "word_list", "word_search", "word_detail", "word_report", "sessions", "client_events", "answers"}
    OTHER_RESOURCE = {"session_detail", "session_resume", "session_discard"}

    def test_authz_matrix(self):
        v1 = next(p for p in get_resolver().url_patterns if str(p.pattern) == "api/v1/")
        names = set()

        def walk(patterns):
            for p in patterns:
                if hasattr(p, "url_patterns"):
                    walk(p.url_patterns)
                else:
                    names.add(p.name)

        walk(v1.url_patterns)
        # Una ruta nueva sin caso en la matriz hace fallar la prueba (Q-10).
        self.assertEqual(names, self.PUBLIC | self.OWN | self.OTHER_RESOURCE)

        make_level(1, 3)
        build_system_decks()
        ana, beto = student(), student("beto@example.com")
        with at(DAY1):
            s = start(client_for(ana)).json()["session"]
            intruder = client_for(beto)
            for path, method in ((f"/api/v1/sessions/{s['id']}", "get"), (f"/api/v1/sessions/{s['id']}/resume", "post"),
                                 (f"/api/v1/sessions/{s['id']}/discard", "post")):
                self.assertEqual(getattr(intruder, method)(path).status_code, 404, path)
            r = intruder.post("/api/v1/answers", {"client_id": str(uuid.uuid4()), "session_id": s["id"], "position": 0,
                                                  "unit": s["cards"][0]["unit"], "grade": "pass"}, format="json")
            self.assertEqual(r.status_code, 404)
        anon = client_for()
        for path in ("/api/v1/me", "/api/v1/today", "/api/v1/progress", "/api/v1/levels", "/api/v1/decks",
                     "/api/v1/words/search?q=a", "/api/v1/sessions"):
            self.assertEqual(anon.get(path).status_code, 401, path)

    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_redirects_to_https(self):
        r = client_for().get("/api/v1/config")
        self.assertEqual(r.status_code, 301)
        self.assertTrue(r["Location"].startswith("https://"))
        self.assertEqual(client_for().get("/api/v1/health").status_code, 200)  # el monitor interno no se redirige
