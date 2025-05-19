from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Game, DailyGame
from .services.rawg_service import RAWGService


@shared_task
def select_daily_game():
    """Seleccionar juego diario"""

    tomorrow = timezone.now().date() + timedelta(days=1)

    # Comprobamos que no haya ya un juego seleccionado para mañana
    if DailyGame.objects.filter(date=tomorrow).exists():
        return "Ya existe un juego para mañana."

    rawg_service = RAWGService()
    game = rawg_service.select_random_game()

    if not game:
        return "No se ha podido seleccionar un juego."

    DailyGame.objects.create(
        game=game,
        date=tomorrow,
    )

    # Marcamos el juego como "usado"
    game.used_date = tomorrow
    game.save(update_fields=["used_date"])

    return f"Juego para el {tomorrow} seleccionado correctamente."


# TODO: ¿Actualizar en batches de una semana?
