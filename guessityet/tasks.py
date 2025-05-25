from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Game, DailyGame
from .services.rawg_service import RAWGService
from .services.image_analysis_service import GameDifficultyService


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

    return f"Juego para el {tomorrow} seleccionado correctamente: {game.title}"


@shared_task
def process_game_gif_async(game_id):
    """
    Procesar GIF de un juego de forma asíncrona
    Útil para evitar timeouts en la interfaz web
    """
    try:
        game = Game.objects.get(id=game_id)

        if not game.video_url:
            return f"El juego {game.title} no tiene vídeo disponible"

        if game.gif_path:
            return f"El juego {game.title} ya tiene GIF procesado"

        rawg_service = RAWGService()

        # Verificar tamaño del vídeo antes de procesarlo
        if not rawg_service.check_video_size(game.video_url):
            return f"Vídeo demasiado grande para {game.title}, saltando GIF"

        gif_path = rawg_service.download_and_convert_video_to_gif(
            game.video_url, game.id
        )

        if gif_path:
            game.gif_path = gif_path
            game.save(update_fields=["gif_path"])
            return f"GIF procesado correctamente para {game.title}"
        else:
            return f"Error al procesar GIF para {game.title}"

    except Game.DoesNotExist:
        return f"Juego con ID {game_id} no encontrado"
    except Exception as e:
        return f"Error al procesar GIF: {str(e)}"


@shared_task
def batch_process_gifs():
    """
    Procesar GIFs para juegos que no los tienen
    Ejecutar esta tarea periódicamente
    """
    games_without_gif = Game.objects.filter(
        video_url__isnull=False, gif_path__isnull=True
    )[
        :5
    ]  # Procesar máximo 5 por vez

    results = []
    for game in games_without_gif:
        result = process_game_gif_async.delay(game.id)
        results.append(f"Procesando GIF para {game.title} - Task ID: {result.id}")

    return f"Iniciado procesamiento de {len(results)} GIFs: {results}"


@shared_task
def process_screenshots_difficulty(game_id):
    """
    Procesa las capturas de un juego para organizarlas por dificultad
    """
    try:
        game = Game.objects.get(id=game_id)
        difficulty_service = GameDifficultyService()

        success = difficulty_service.select_and_organize_best_screenshots(
            game, max_screenshots=5
        )

        if success:
            return f"Capturas procesadas correctamente para {game.title}"
        else:
            return f"Error procesando capturas para {game.title}"

    except Game.DoesNotExist:
        return f"Juego con ID {game_id} no encontrado"
    except Exception as e:
        return f"Error procesando capturas: {str(e)}"


@shared_task
def batch_process_screenshots_difficulty():
    """
    Procesa capturas para múltiples juegos que aún no han sido procesadas
    """
    # Buscar juegos que tienen capturas pero no han sido procesadas por dificultad
    games_to_process = Game.objects.filter(
        screenshot__isnull=False, screenshot__local_path__isnull=True
    ).distinct()[
        :5
    ]  # Procesar máximo 5 por vez

    results = []
    for game in games_to_process:
        result = process_screenshots_difficulty.delay(game.id)
        results.append(f"Procesando capturas para {game.title} - Task ID: {result.id}")

    return f"Iniciado procesamiento de capturas para {len(results)} juegos: {results}"
