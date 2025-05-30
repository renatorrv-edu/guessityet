from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Game, DailyGame
from .services.rawg_service import RAWGService
from .services.igdb_service import IGDBService
from .services.image_analysis_service import GameDifficultyService


@shared_task
def select_daily_game(use_igdb=False):
    """
    Seleccionar juego diario

    Args:
        use_igdb (bool): Si True, usa IGDB en lugar de RAWG
    """
    tomorrow = timezone.now().date() + timedelta(days=1)

    if DailyGame.objects.filter(date=tomorrow).exists():
        return "Ya existe un juego para mañana."

    # Seleccionar servicio
    if use_igdb:
        print("Usando servicio IGDB para selección diaria")
        service = IGDBService()
    else:
        print("Usando servicio RAWG para selección diaria")
        service = RAWGService()

    game = service.select_random_game()

    if not game:
        service_name = "IGDB" if use_igdb else "RAWG"
        return f"No se ha podido seleccionar un juego usando {service_name}."

    DailyGame.objects.create(
        game=game,
        date=tomorrow,
    )

    game.used_date = tomorrow
    game.save(update_fields=["used_date"])

    return f"Juego para el {tomorrow} seleccionado correctamente: {game.title}"


@shared_task
def select_daily_game_igdb():
    """Seleccionar juego diario usando IGDB"""
    return select_daily_game(use_igdb=True)


@shared_task
def process_game_gif_async(game_id, service_type="rawg"):
    """
    Procesar GIF de un juego de forma asíncrona

    Args:
        game_id: ID del juego
        service_type: "rawg" o "igdb" para usar el servicio correcto
    """
    try:
        game = Game.objects.get(id=game_id)

        if not game.video_url:
            return f"El juego {game.title} no tiene vídeo disponible"

        if game.gif_path:
            return f"El juego {game.title} ya tiene GIF procesado"

        # Seleccionar servicio según el tipo
        if service_type == "igdb":
            service = IGDBService()
        else:
            service = RAWGService()

        if not service.check_video_size(game.video_url):
            return f"Vídeo demasiado grande para {game.title}, saltando GIF"

        gif_path = service.download_and_convert_video_to_gif(game.video_url, game.id)

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
def batch_process_gifs(service_type="rawg"):
    """
    Procesar GIFs para juegos que no los tienen

    Args:
        service_type: "rawg" o "igdb" para determinar qué juegos procesar
    """
    if service_type == "igdb":
        # Procesar juegos de IGDB sin GIF
        games_without_gif = Game.objects.filter(
            video_url__isnull=False, gif_path__isnull=True, igdb_id__isnull=False
        )[:5]
    else:
        # Procesar juegos de RAWG sin GIF
        games_without_gif = Game.objects.filter(
            video_url__isnull=False, gif_path__isnull=True, rawg_id__isnull=False
        )[:5]

    results = []
    for game in games_without_gif:
        result = process_game_gif_async.delay(game.id, service_type)
        results.append(f"Procesando GIF para {game.title} - Task ID: {result.id}")

    service_name = "IGDB" if service_type == "igdb" else "RAWG"
    return f"Iniciado procesamiento de {len(results)} GIFs ({service_name}): {results}"


@shared_task
def process_screenshots_difficulty(game_id):
    """
    Procesa las capturas de un juego para organizarlas por dificultad
    Compatible con ambos servicios RAWG e IGDB
    """
    try:
        game = Game.objects.get(id=game_id)
        difficulty_service = GameDifficultyService()

        # Determinar número de capturas según disponibilidad de vídeo
        max_screenshots = 5 if game.video_url else 6

        success = difficulty_service.select_and_organize_best_screenshots(
            game, max_screenshots=max_screenshots
        )

        if success:
            return f"Capturas procesadas correctamente para {game.title} ({max_screenshots} capturas)"
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
    Compatible con juegos de RAWG e IGDB
    """
    games_to_process = Game.objects.filter(
        screenshot__isnull=False, screenshot__local_path__isnull=True
    ).distinct()[:5]

    results = []
    for game in games_to_process:
        result = process_screenshots_difficulty.delay(game.id)
        service_type = "IGDB" if game.igdb_id else "RAWG"
        results.append(
            f"Procesando capturas para {game.title} ({service_type}) - Task ID: {result.id}"
        )

    return f"Iniciado procesamiento de capturas para {len(results)} juegos: {results}"


@shared_task
def migrate_rawg_to_igdb_batch(limit=5):
    """
    Tarea para migrar juegos de RAWG a IGDB de forma gradual
    """
    try:
        # Buscar juegos de RAWG que no tienen datos de IGDB
        rawg_games = Game.objects.filter(rawg_id__isnull=False, igdb_id__isnull=True)[
            :limit
        ]

        if not rawg_games:
            return "No hay más juegos de RAWG para migrar a IGDB"

        igdb_service = IGDBService()
        migrated_count = 0
        results = []

        for game in rawg_games:
            print(f"Intentando migrar: {game.title}")

            # Buscar el juego en IGDB por nombre
            search_results = igdb_service.search_games(game.title, limit=5)

            if search_results:
                # Tomar el primer resultado que coincida mejor
                best_match = search_results[0]

                # Obtener detalles completos
                igdb_details = igdb_service.get_game_details(best_match["id"])

                if igdb_details:
                    # Actualizar el juego con información de IGDB
                    game.igdb_id = igdb_details["id"]
                    game.franchise_name = igdb_service.get_franchise_name(igdb_details)
                    game.franchise_slug = igdb_service.get_franchise_slug(igdb_details)
                    game.save(
                        update_fields=["igdb_id", "franchise_name", "franchise_slug"]
                    )

                    migrated_count += 1
                    results.append(f"✅ {game.title} -> IGDB ID {game.igdb_id}")
                else:
                    results.append(
                        f"❌ {game.title} -> No se pudieron obtener detalles"
                    )
            else:
                results.append(f"❌ {game.title} -> No encontrado en IGDB")

        return (
            f"Migrados {migrated_count}/{len(rawg_games)} juegos. Resultados: {results}"
        )

    except Exception as e:
        return f"Error en migración batch: {str(e)}"


@shared_task
def test_igdb_service():
    """
    Tarea de prueba para verificar que el servicio IGDB funciona
    """
    try:
        igdb_service = IGDBService()

        # Probar autenticación
        token = igdb_service.get_access_token()
        if not token:
            return "❌ Error: No se pudo obtener token de IGDB"

        # Probar búsqueda
        search_results = igdb_service.search_games("Mario", limit=3)
        if not search_results:
            return "❌ Error: Búsqueda en IGDB falló"

        # Probar selección de juego aleatorio
        random_game = igdb_service.select_random_game(max_iterations=2)
        if random_game:
            return f"✅ Servicio IGDB funcionando. Juego de prueba: {random_game.title}"
        else:
            return "⚠️ Servicio IGDB autenticado pero no encontró juegos válidos"

    except Exception as e:
        return f"❌ Error probando servicio IGDB: {str(e)}"
