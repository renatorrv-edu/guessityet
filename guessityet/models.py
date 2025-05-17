from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Game(models.Model):
    """Modelo para almacenar los juegos recibidos por la API"""

    rawg_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    developer = models.CharField(max_length=255, null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    genres = models.CharField(max_length=255, null=True, blank=True)
    platformdirs = models.CharField(max_length=255, null=True, blank=True)
    metacritic = models.IntegerField(null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    # Fecha en la que se usó en el juego diario
    used_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class Screenshot(models.Model):
    """Screenshots asociados a cada juego"""

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    image_url = models.URLField()
    # Ruta local para almacenar la captura
    local_path = models.CharField(max_length=255, null=True, blank=True)
    # Del 1 al 5
    difficulty = models.IntegerField()

    class Meta:
        ordering = ["difficulty"]


class DailyGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ("date",)


class UserProfile(models.Model):
    """Perfil del usuario"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    current_streak = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    # Juegos individuales y multijugador ganados. Guessed It! = acertar a la primera.
    games_won = models.IntegerField(default=0)
    mult_games_won = models.IntegerField(default=0)
    guessed_it = models.IntegerField(default=0)

    # Media de intentos y media de aciertos
    average_attempts = models.IntegerField(default=0)
    average_guesses = models.IntegerField(default=0)

    def __str__(self):
        return f"Perfil de {self.user.username}"


# TODO: Revisar para ver cómo se implementan estos registros
class UserGameAttempt(models.Model):
    """Registro de los intentos del usuario con cada juego diario"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # Para usuarios que juegan de manera anónima
    session_id = models.CharField(max_length=100, null=True, blank=True)
    daily_game = models.ForeignKey(DailyGame, on_delete=models.CASCADE)
    attempts_used = models.IntegerField(default=0)
    success = models.BooleanField(default=False)
    # Fecha y hora de completamiento
    completed_at = models.DateTimeField(null=True, blank=True)


# TODO: Revisar
class GameLobby(models.Model):
    """Lobbies multijugador"""

    code = models.CharField(max_length=8, unique=True)
    creator = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="created_lobbies"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_players = models.IntegerField(default=10)

    def __str__(self):
        return f"Lobby {self.code}"


# TODO: Revisar
class LobbyPlayer(models.Model):
    """Jugadores en un lobby"""

    lobby = models.ForeignKey(
        GameLobby, on_delete=models.CASCADE, related_name="players"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    nickname = models.CharField(max_length=50)
    score = models.IntegerField(default=0)
    joined_at = models.DateTimeField(null=True, blank=True)
