"""Utilidades para testing"""

from django.contrib.auth.models import User
from guessityet.models import Game, DailyGame, Screenshot, UserGameAttempt
from django.utils import timezone
from datetime import timedelta


class TestDataFactory:
    """Factory para crear datos de test de forma consistente"""

    @staticmethod
    def create_user(
        username="testuser", email="test@example.com", password="testpass123", **kwargs
    ):
        """Crear usuario de prueba"""
        defaults = {"username": username, "email": email, "is_active": True}
        defaults.update(kwargs)

        user = User.objects.create_user(password=password, **defaults)
        # Confirmar email por defecto para tests
        user.profile.email_confirmed = True
        user.profile.save()
        return user

    @staticmethod
    def create_game(title="Test Game", igdb_id=12345, **kwargs):
        """Crear juego de prueba"""
        defaults = {
            "title": title,
            "igdb_id": igdb_id,
            "developer": "Test Developer",
            "release_year": 2020,
            "genres": "Action, Adventure",
            "platforms": "PC, PlayStation 5",
            "metacritic": 85,
        }
        defaults.update(kwargs)
        return Game.objects.create(**defaults)

    @staticmethod
    def create_daily_game(game=None, date=None, **kwargs):
        """Crear juego diario de prueba"""
        if game is None:
            game = TestDataFactory.create_game()
        if date is None:
            date = timezone.now().date()

        return DailyGame.objects.create(game=game, date=date, **kwargs)

    @staticmethod
    def create_screenshots(game, count=6):
        """Crear screenshots de prueba para un juego"""
        screenshots = []
        for i in range(count):
            screenshot = Screenshot.objects.create(
                game=game,
                image_url=f"https://example.com/screenshot{i}.jpg",
                difficulty=i + 1,
            )
            screenshots.append(screenshot)
        return screenshots

    @staticmethod
    def create_user_attempt(user, daily_game, success=True, attempts_used=3, **kwargs):
        """Crear intento de usuario de prueba"""
        defaults = {
            "success": success,
            "attempts_used": attempts_used,
            "guessed_it": success and attempts_used == 1,
            "attempts_data": [
                {"attempt": i, "type": "guess", "correct": i == attempts_used}
                for i in range(1, attempts_used + 1)
            ],
        }
        defaults.update(kwargs)

        return UserGameAttempt.objects.create(
            user=user, daily_game=daily_game, **defaults
        )


class GameSessionHelper:
    """Helper para simular sesiones de juego en tests"""

    @staticmethod
    def create_game_session(client, game, current_attempt=1, won=False):
        """Crear sesión de juego en el cliente de test"""
        session = client.session
        session["game_state"] = {
            "game_id": game.id,
            "current_attempt": current_attempt,
            "attempts": [],
            "won": won,
            "lost": False,
        }
        session.save()
        return session

    @staticmethod
    def add_attempt_to_session(
        client, attempt_type="guess", game_name="Test Game", correct=False
    ):
        """Añadir intento a la sesión actual"""
        session = client.session
        game_state = session.get("game_state", {})

        if "attempts" not in game_state:
            game_state["attempts"] = []

        game_state["attempts"].append(
            {
                "attempt": len(game_state["attempts"]) + 1,
                "type": attempt_type,
                "game_name": game_name,
                "correct": correct,
            }
        )

        session["game_state"] = game_state
        session.save()
        return session
