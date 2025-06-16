from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from datetime import timedelta


class Game(models.Model):
    """Modelo para almacenar los juegos recibidos por la API"""

    # Transición gradual de RAWG a IGDB
    igdb_id = models.IntegerField(null=True, blank=True, unique=True)
    rawg_id = models.IntegerField(null=True, blank=True)  # Mantener por compatibilidad

    title = models.CharField(max_length=255)
    developer = models.CharField(max_length=255, null=True, blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    genres = models.CharField(max_length=255, null=True, blank=True)
    platforms = models.CharField(max_length=255, null=True, blank=True)
    metacritic = models.IntegerField(null=True, blank=True)

    # Campos específicos de IGDB
    franchise_name = models.CharField(max_length=255, null=True, blank=True)
    franchise_slug = models.CharField(max_length=255, null=True, blank=True)

    video_url = models.URLField(null=True, blank=True)
    gif_path = models.CharField(max_length=500, null=True, blank=True)
    used_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class Screenshot(models.Model):
    """Screenshots asociados a cada juego"""

    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    image_url = models.URLField()
    local_path = models.CharField(max_length=255, null=True, blank=True)
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
    games_won = models.IntegerField(default=0)
    mult_games_won = models.IntegerField(default=0)
    guessed_it = models.IntegerField(default=0)
    average_attempts = models.IntegerField(default=0)
    average_guesses = models.IntegerField(default=0)

    # Nuevos campos para confirmación de email
    email_confirmed = models.BooleanField(default=False)
    email_confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"

    def confirm_email(self):
        """Marcar el email como confirmado"""
        self.email_confirmed = True
        self.email_confirmed_at = timezone.now()
        self.save()


class EmailConfirmationToken(models.Model):
    """Token para confirmación de email del usuario"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="confirmation_tokens"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Token de confirmación"
        verbose_name_plural = "Tokens de confirmación"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Token para {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token expira en 24 horas
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Verificar si el token ha expirado"""
        return timezone.now() > self.expires_at

    def is_valid(self):
        """Verificar si el token es válido"""
        return not self.is_used and not self.is_expired()


class UserGameAttempt(models.Model):
    """Registro de los intentos del usuario con cada juego diario"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    daily_game = models.ForeignKey(DailyGame, on_delete=models.CASCADE)
    attempts_used = models.IntegerField(default=0)
    success = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Campo para guardar los detalles de todos los intentos
    attempts_data = models.JSONField(default=list, blank=True)

    def get_attempt_icons(self):
        """Retorna una lista de iconos para mostrar en el historial"""
        icons = []
        max_attempts = 6

        for i in range(1, max_attempts + 1):
            # Buscar si existe un intento para este número
            attempt_data = next(
                (a for a in self.attempts_data if a.get("attempt") == i), None
            )

            if attempt_data:
                if attempt_data.get("correct"):
                    icons.append(
                        {
                            "icon": "fas fa-check",
                            "class": "correct",
                            "title": f"Acierto en intento {i}",
                        }
                    )
                elif attempt_data.get("franchise_match"):
                    icons.append(
                        {
                            "icon": "fas fa-star",
                            "class": "franchise",
                            "title": f"Franquicia correcta en intento {i}",
                        }
                    )
                elif attempt_data.get("type") == "skipped":
                    icons.append(
                        {
                            "icon": "fas fa-forward",
                            "class": "skipped",
                            "title": f"Turno {i} saltado",
                        }
                    )
                else:
                    icons.append(
                        {
                            "icon": "fas fa-times",
                            "class": "wrong",
                            "title": f"Fallo en intento {i}",
                        }
                    )
            else:
                # No hubo intento en este turno - mostrar como no alcanzado
                icons.append(
                    {
                        "icon": "fas fa-question",
                        "class": "not-reached",
                        "title": f"Intento {i} no alcanzado",
                    }
                )

        return icons

    class Meta:
        unique_together = ["user", "daily_game"]
        verbose_name = "Intento de juego del usuario"
        verbose_name_plural = "Intentos de juegos del usuario"


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


# Signals para manejar la creación automática de perfiles
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crear perfil automáticamente al crear usuario"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Guardar perfil cuando se guarda usuario"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        # Si por alguna razón no existe el perfil, crearlo
        UserProfile.objects.create(user=instance)
