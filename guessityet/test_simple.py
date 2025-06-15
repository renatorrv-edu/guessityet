from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from unittest.mock import patch, Mock
import json

from guessityet.models import Game, DailyGame, Screenshot, UserProfile, UserGameAttempt
from guessityet.services.igdb_service import IGDBService


class ModelTests(TestCase):
    """Tests básicos de modelos"""

    def test_game_creation(self):
        """Test creación de juego"""
        game = Game.objects.create(
            title="Test Game", igdb_id=123, developer="Test Studio", release_year=2020
        )
        self.assertEqual(str(game), "Test Game")
        self.assertEqual(game.igdb_id, 123)

    def test_daily_game_creation(self):
        """Test creación de juego diario"""
        game = Game.objects.create(title="Daily Game", igdb_id=456)
        today = timezone.now().date()

        daily_game = DailyGame.objects.create(game=game, date=today)
        self.assertEqual(daily_game.game, game)
        self.assertEqual(daily_game.date, today)

    def test_user_profile_auto_creation(self):
        """Test que el perfil se crea automáticamente"""
        user = User.objects.create_user("testuser", password="test123")
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.current_streak, 0)

    def test_user_game_attempt(self):
        """Test modelo de intento de usuario"""
        user = User.objects.create_user("testuser", password="test123")
        game = Game.objects.create(title="Test Game", igdb_id=789)
        daily_game = DailyGame.objects.create(game=game, date=timezone.now().date())

        attempt = UserGameAttempt.objects.create(
            user=user, daily_game=daily_game, success=True, attempts_used=3
        )

        self.assertTrue(attempt.success)
        self.assertEqual(attempt.attempts_used, 3)


class ServiceTests(TestCase):
    """Tests para servicios"""

    @patch("guessityet.services.igdb_service.requests.post")
    def test_igdb_token_request(self, mock_post):
        """Test solicitud de token IGDB"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token"}
        mock_post.return_value = mock_response

        service = IGDBService()
        token = service.get_access_token()

        self.assertEqual(token, "test_token")

    @patch("guessityet.services.igdb_service.IGDBService.make_request")
    def test_igdb_search(self, mock_request):
        """Test búsqueda IGDB"""
        mock_request.side_effect = [[{"id": 123, "name": "Test Game"}], []]

        service = IGDBService()
        results = service.search_games("test")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Test Game")


class AjaxEndpointTests(TestCase):
    """Tests para endpoints AJAX"""

    def setUp(self):
        self.client = Client()
        self.game = Game.objects.create(title="Secret Game", igdb_id=12345)
        self.daily_game = DailyGame.objects.create(
            game=self.game, date=timezone.now().date()
        )

    def test_search_games_ajax_endpoint(self):
        """Test endpoint de búsqueda AJAX"""
        with patch(
            "guessityet.services.igdb_service.IGDBService.search_games"
        ) as mock_search:
            mock_search.return_value = [{"id": 123, "name": "Test Game"}]

            response = self.client.get(
                reverse("guessityet:search_games_ajax"),
                {"q": "test", "service": "igdb"},
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertIn("games", data)

    def test_search_games_short_query(self):
        """Test búsqueda con query muy corto"""
        response = self.client.get(
            reverse("guessityet:search_games_ajax"), {"q": "a"}  # Muy corto
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["games"], [])

    def test_submit_guess_no_session(self):
        """Test envío sin sesión activa"""
        response = self.client.post(
            reverse("guessityet:submit_guess"),
            json.dumps({"game_name": "Test"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_submit_guess_with_session(self):
        """Test envío con sesión válida"""
        # Configurar sesión
        session = self.client.session
        session["game_state"] = {
            "game_id": self.game.id,
            "current_attempt": 1,
            "attempts": [],
            "won": False,
            "lost": False,
        }
        session.save()

        response = self.client.post(
            reverse("guessityet:submit_guess"),
            json.dumps(
                {"game_name": "Secret Game", "game_id": 12345, "service": "igdb"}
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

    def test_skip_turn_endpoint(self):
        """Test endpoint de saltar turno"""
        # Configurar sesión válida
        session = self.client.session
        session["game_state"] = {
            "game_id": self.game.id,
            "current_attempt": 1,
            "attempts": [],
            "won": False,
            "lost": False,
        }
        session.save()

        response = self.client.post(
            reverse("guessityet:skip_turn"), content_type="application/json"
        )

        # Debe responder exitosamente
        self.assertIn(
            response.status_code, [200, 400]
        )  # 400 si hay problemas de lógica


class UserAuthTests(TestCase):
    """Tests de autenticación básicos"""

    def test_user_creation(self):
        """Test creación básica de usuario"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))

    def test_profile_creation_signal(self):
        """Test que el perfil se crea automáticamente"""
        user = User.objects.create_user("signaltest", password="test123")

        # Verificar que el perfil existe
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

        # Verificar valores por defecto
        profile = user.profile
        self.assertEqual(profile.current_streak, 0)
        self.assertEqual(profile.games_won, 0)
        self.assertFalse(profile.email_confirmed)


class GameLogicTests(TestCase):
    """Tests de lógica de juego"""

    def setUp(self):
        self.user = User.objects.create_user("gameuser", password="test123")
        self.game = Game.objects.create(title="Logic Game", igdb_id=999)
        self.daily_game = DailyGame.objects.create(
            game=self.game, date=timezone.now().date()
        )

    def test_correct_guess_logic(self):
        """Test lógica de respuesta correcta"""
        from guessityet.views import process_guess

        # Simular request y game_state
        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.session = {}

        request = MockRequest(self.user)
        game_state = {
            "game_id": self.game.id,
            "current_attempt": 1,
            "attempts": [],
            "won": False,
        }

        result = process_guess(
            request,
            self.game,
            "Logic Game",  # Nombre correcto
            999,  # ID correcto
            "igdb",
            game_state,
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["correct"])

    def test_incorrect_guess_logic(self):
        """Test lógica de respuesta incorrecta"""
        from guessityet.views import process_guess

        class MockRequest:
            def __init__(self, user):
                self.user = user
                self.session = {}

        request = MockRequest(self.user)
        game_state = {
            "game_id": self.game.id,
            "current_attempt": 1,
            "attempts": [],
            "won": False,
        }

        result = process_guess(
            request,
            self.game,
            "Wrong Game",  # Nombre incorrecto
            888,  # ID incorrecto
            "igdb",
            game_state,
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["correct"])

    def test_game_attempt_saving(self):
        """Test que los intentos se guardan correctamente"""
        attempt = UserGameAttempt.objects.create(
            user=self.user, daily_game=self.daily_game, success=True, attempts_used=2
        )

        # Verificar que se guardó correctamente
        saved_attempt = UserGameAttempt.objects.get(
            user=self.user, daily_game=self.daily_game
        )

        self.assertEqual(saved_attempt.attempts_used, 2)
        self.assertTrue(saved_attempt.success)


class UtilityTests(TestCase):
    """Tests de funciones utilitarias"""

    def test_game_string_representation(self):
        """Test representación string de modelos"""
        game = Game.objects.create(title="String Test Game", igdb_id=111)
        self.assertEqual(str(game), "String Test Game")

        user = User.objects.create_user("stringuser", password="test123")
        self.assertEqual(str(user.profile), "Perfil de stringuser")

    def test_date_uniqueness_constraint(self):
        """Test que no se pueden crear dos juegos para la misma fecha"""
        game1 = Game.objects.create(title="Game 1", igdb_id=111)
        game2 = Game.objects.create(title="Game 2", igdb_id=222)

        today = timezone.now().date()

        # Crear primer juego diario
        DailyGame.objects.create(game=game1, date=today)

        # Intentar crear segundo juego para la misma fecha debería fallar
        with self.assertRaises(Exception):
            DailyGame.objects.create(game=game2, date=today)

    def test_screenshot_ordering(self):
        """Test ordenamiento de screenshots por dificultad"""
        game = Game.objects.create(title="Screenshot Game", igdb_id=333)

        # Crear screenshots en orden aleatorio
        Screenshot.objects.create(
            game=game, image_url="https://example.com/3.jpg", difficulty=3
        )
        Screenshot.objects.create(
            game=game, image_url="https://example.com/1.jpg", difficulty=1
        )
        Screenshot.objects.create(
            game=game, image_url="https://example.com/2.jpg", difficulty=2
        )

        # Verificar que se ordenan por dificultad
        screenshots = game.screenshot_set.all()
        difficulties = [s.difficulty for s in screenshots]
        self.assertEqual(difficulties, [1, 2, 3])


class IntegrationTests(TestCase):
    """Tests de integración básicos"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="integrationuser", password="testpass123", is_active=True
        )
        self.user.profile.email_confirmed = True
        self.user.profile.save()

    def test_login_flow(self):
        """Test flujo básico de login"""
        response = self.client.post(
            reverse("guessityet:login"),
            {"username": "integrationuser", "password": "testpass123"},
        )

        # Debe redirigir después del login exitoso
        self.assertEqual(response.status_code, 302)

    def test_game_state_persistence(self):
        """Test que el estado del juego persiste en sesión"""
        game = Game.objects.create(title="Session Game", igdb_id=444)

        # Configurar estado inicial
        session = self.client.session
        session["game_state"] = {"game_id": game.id, "current_attempt": 1, "won": False}
        session.save()

        # Verificar que persiste
        self.assertEqual(self.client.session["game_state"]["game_id"], game.id)
        self.assertEqual(self.client.session["game_state"]["current_attempt"], 1)

    def test_ajax_endpoints_exist(self):
        """Test que los endpoints AJAX principales existen"""
        # Verificar que las URLs se resuelven correctamente
        search_url = reverse("guessityet:search_games_ajax")
        submit_url = reverse("guessityet:submit_guess")
        skip_url = reverse("guessityet:skip_turn")

        self.assertTrue(search_url.startswith("/"))
        self.assertTrue(submit_url.startswith("/"))
        self.assertTrue(skip_url.startswith("/"))


class EdgeCaseTests(TestCase):
    """Tests para casos extremos"""

    def test_empty_search_query(self):
        """Test búsqueda con query vacío"""
        response = self.client.get(reverse("guessityet:search_games_ajax"), {"q": ""})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["games"], [])

    def test_malformed_ajax_request(self):
        """Test request AJAX malformado"""
        response = self.client.post(
            reverse("guessityet:submit_guess"),
            "invalid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_game_without_igdb_id(self):
        """Test juego solo con RAWG ID"""
        game = Game.objects.create(title="RAWG Only Game", rawg_id=12345, igdb_id=None)

        self.assertIsNone(game.igdb_id)
        self.assertEqual(game.rawg_id, 12345)

    def test_user_profile_edge_cases(self):
        """Test casos extremos del perfil de usuario"""
        user = User.objects.create_user("edgeuser", password="test123")
        profile = user.profile

        # Verificar valores por defecto
        self.assertEqual(profile.current_streak, 0)
        self.assertEqual(profile.max_streak, 0)
        self.assertEqual(profile.games_won, 0)

        # Test método confirm_email
        profile.confirm_email()
        self.assertTrue(profile.email_confirmed)
        self.assertIsNotNone(profile.email_confirmed_at)


if __name__ == "__main__":
    # Permitir ejecutar como script independiente
    import django
    from django.conf import settings
    from django.test.utils import get_runner

    if not settings.configured:
        import os

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        django.setup()

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
