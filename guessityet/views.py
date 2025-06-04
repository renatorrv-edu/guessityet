from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import time

from .models import Game, DailyGame, Screenshot
from .services.rawg_service import RAWGService
from .services.igdb_service import IGDBService


def daily_game(request):
    """
    Vista principal del juego diario
    Muestra el juego del día actual o genera uno para pruebas
    """
    today = timezone.now().date()

    try:
        daily_game = DailyGame.objects.get(date=today)
        game = daily_game.game
    except DailyGame.DoesNotExist:
        game = generate_test_game_data()
        if not game:
            return render(request, "game/no_game_available.html")

    if (
        "game_state" not in request.session
        or request.session.get("game_state", {}).get("game_id") != game.id
    ):
        init_game_session(request, game)

    screenshots = game.screenshot_set.all().order_by("difficulty")
    game_state = request.session["game_state"]

    context = {
        "game": game,
        "screenshots": screenshots,
        "game_state": game_state,
        "game_state_json": json.dumps(game_state),
        "today": today,
    }

    return render(request, "game/daily_game.html", context)


def search_games_ajax(request):
    """
    Búsqueda de juegos para el autocompletado
    Ahora con franquicia y año de lanzamiento
    """
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    query = request.GET.get("q", "").strip()
    service_type = request.GET.get("service", "igdb")
    limit = int(request.GET.get("limit", 25))

    if len(query) < 2:
        return JsonResponse({"games": []})

    try:
        igdb_service = IGDBService()
        games = igdb_service.search_games(query, limit=limit)

        formatted_games = []
        for game in games or []:
            game_data = {
                "id": game["id"],
                "name": game["name"],
                "service": "igdb",
            }

            # Añadir fecha de lanzamiento si existe
            if game.get("first_release_date"):
                game_data["released"] = game["first_release_date"]

            # Añadir franquicia si existe
            if game.get("franchise"):
                game_data["franchise"] = game["franchise"]

            formatted_games.append(game_data)

        return JsonResponse({"games": formatted_games})

    except Exception as e:
        print(f"Error buscando juegos: {e}")
        return JsonResponse({"games": []})


def insert_spaces_in_compound_words(query):
    """Insertar espacios en palabras compuestas comunes de videojuegos"""
    import re

    patterns = [
        (r"metalgear", "metal gear"),
        (r"callofduty", "call of duty"),
        (r"grandtheft", "grand theft"),
        (r"assassinscreed", "assassins creed"),
        (r"farcry", "far cry"),
        (r"finalfantasy", "final fantasy"),
        (r"godofwar", "god of war"),
        (r"lastofus", "last of us"),
        (r"masseffect", "mass effect"),
        (r"deadspace", "dead space"),
        (r"dragonage", "dragon age"),
        (r"elderscrolls", "elder scrolls"),
        (r"needforspeed", "need for speed"),
        (r"tombraider", "tomb raider"),
        (r"streetfighter", "street fighter"),
        (r"mortalkombat", "mortal kombat"),
        (r"supermario", "super mario"),
        (r"donkeykong", "donkey kong"),
        (r"halflife", "half life"),
        (r"counterstrike", "counter strike"),
        (r"teamfortress", "team fortress"),
        (r"leftdead", "left dead"),
        (r"gearsswar", "gears war"),
    ]

    query_lower = query.lower()

    for pattern, replacement in patterns:
        if pattern in query_lower:
            return re.sub(pattern, replacement, query_lower, flags=re.IGNORECASE)

    return query


@require_http_methods(["POST"])
def submit_guess(request):
    """Procesar la respuesta del jugador"""
    if "game_state" not in request.session:
        return JsonResponse({"error": "No hay juego activo"}, status=400)

    try:
        data = json.loads(request.body)
        guessed_game_name = data.get("game_name", "").strip()
        guessed_game_id = data.get("game_id")
        service_type = data.get("service", "rawg")

        if not guessed_game_name:
            return JsonResponse({"error": "Nombre del juego requerido"}, status=400)

        game_state = request.session["game_state"]
        game = get_object_or_404(Game, id=game_state["game_id"])

        result = process_guess(
            game, guessed_game_name, guessed_game_id, service_type, game_state
        )

        request.session["game_state"] = game_state
        request.session.modified = True

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Datos inválidos"}, status=400)
    except Exception as e:
        print(f"Error procesando respuesta: {e}")
        return JsonResponse({"error": "Error interno"}, status=500)


@require_http_methods(["POST"])
def skip_turn(request):
    """Saltar el turno actual"""
    if "game_state" not in request.session:
        return JsonResponse({"error": "No hay juego activo"}, status=400)

    game_state = request.session["game_state"]
    game = get_object_or_404(Game, id=game_state["game_id"])

    # Calcular máximo de intentos según disponibilidad de GIF
    has_gif = game.gif_path and game.gif_path.strip()
    max_attempts = 6 if has_gif else min(6, game.screenshot_set.count())

    if game_state["won"] or game_state["current_attempt"] > max_attempts:
        return JsonResponse({"error": "Juego ya terminado"}, status=400)

    game_state["attempts"].append(
        {
            "attempt": game_state["current_attempt"],
            "type": "skipped",
            "game_name": "Turno saltado",
            "correct": False,
            "franchise_match": False,
        }
    )

    game_state["current_attempt"] += 1

    # Verificar si el juego ha terminado
    if game_state["current_attempt"] > max_attempts:
        game_state["lost"] = True

    request.session["game_state"] = game_state
    request.session.modified = True

    return JsonResponse(
        {
            "success": True,
            "skipped": True,
            "current_attempt": game_state["current_attempt"],
            "game_ended": game_state.get("lost", False),
        }
    )


def generate_test_game(request):
    """Generar un nuevo juego de prueba usando RAWG por defecto"""
    print("Forzando generación de nuevo juego de prueba...")

    request.session.flush()

    rawg_service = RAWGService()
    game = rawg_service.select_random_game()

    if game:
        print(f"Nuevo juego generado: {game.title}")
        request.session["current_test_game_id"] = game.id
        request.session.modified = True
        return HttpResponseRedirect(reverse("test_rawg_view"))
    else:
        print("No se pudo generar juego")
        return render(
            request,
            "game/no_game_available.html",
            {"error": "No se pudo generar un juego de prueba"},
        )


def generate_test_game_igdb(request):
    """Generar un nuevo juego de prueba usando IGDB"""
    print("Forzando generación de nuevo juego de prueba con IGDB...")

    request.session.flush()

    igdb_service = IGDBService()
    game = igdb_service.select_random_game()

    if game:
        print(f"Nuevo juego generado con IGDB: {game.title}")
        request.session["current_test_game_id"] = game.id
        request.session.modified = True
        return HttpResponseRedirect(reverse("test_igdb_view"))
    else:
        print("No se pudo generar juego con IGDB")
        return render(
            request,
            "game/no_game_available.html",
            {"error": "No se pudo generar un juego de prueba con IGDB"},
        )


def debug_franchise(request):
    """Vista temporal para probar qué devuelve RAWG sobre franquicias"""
    if request.method == "GET":
        test_games = [
            {"name": "Call of Duty: Modern Warfare", "id": 4200},
            {"name": "Assassin's Creed", "id": 4729},
            {"name": "Grand Theft Auto V", "id": 3498},
            {"name": "Metal Gear Solid V", "id": 3206},
            {"name": "Layers of Fear", "id": 4386},
            {"name": "Halo: Combat Evolved", "id": 28448},
        ]

        rawg_service = RAWGService()
        results = []

        for test_game in test_games:
            print(f"\nProbando: {test_game['name']}")

            game_details = rawg_service.get_game_details(test_game["id"])

            if game_details:
                franchise_name, franchise_slug = rawg_service.extract_franchise_info(
                    game_details
                )

                result = {
                    "name": test_game["name"],
                    "id": test_game["id"],
                    "franchise_name": franchise_name,
                    "franchise_slug": franchise_slug,
                    "has_franchise_field": "franchise" in game_details,
                    "franchise_field_value": game_details.get("franchise"),
                    "sample_tags": [
                        tag.get("name") for tag in game_details.get("tags", [])[:5]
                    ],
                }

                results.append(result)
                print(f"Resultado: {franchise_name} ({franchise_slug})")
            else:
                print(f"No se pudieron obtener detalles")

        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Debug Franquicia RAWG</title></head>
        <body>
        <h1>Test de Franquicias RAWG.io</h1>
        """

        for result in results:
            html += f"""
            <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                <h3>{result['name']} (ID: {result['id']})</h3>
                <p><strong>Franquicia detectada:</strong> {result['franchise_name'] or 'Ninguna'}</p>
                <p><strong>Slug:</strong> {result['franchise_slug'] or 'Ninguno'}</p>
                <p><strong>Tiene campo 'franchise':</strong> {result['has_franchise_field']}</p>
                <p><strong>Valor del campo 'franchise':</strong> {result['franchise_field_value']}</p>
                <p><strong>Tags de ejemplo:</strong> {', '.join(result['sample_tags'])}</p>
            </div>
            """

        html += "</body></html>"

        from django.http import HttpResponse

        return HttpResponse(html)

    return JsonResponse({"error": "Solo GET permitido"})


def init_game_session(request, game):
    """Inicializar el estado del juego en la sesión"""
    request.session["game_state"] = {
        "game_id": game.id,
        "current_attempt": 1,
        "attempts": [],
        "won": False,
        "lost": False,
        "guessed_it": False,
    }
    request.session.modified = True


def generate_test_game_data(use_igdb=True):
    """
    Generar un juego completamente nuevo - por defecto usa IGDB

    Args:
        use_igdb (bool): Si True, usa IGDB en lugar de RAWG
    """
    print(f"Generando nuevo juego con {'IGDB' if use_igdb else 'RAWG'}...")

    if use_igdb:
        service = IGDBService()
    else:
        service = RAWGService()

    new_game = service.select_random_game()

    if new_game:
        print(f"Nuevo juego generado: {new_game.title}")
    else:
        print("No se pudo generar un juego")

    return new_game


def process_guess(game, guessed_game_name, guessed_game_id, service_type, game_state):
    """
    Procesar la respuesta del jugador y determinar si es correcta
    Actualizado para usar principalmente IGDB
    """
    is_correct = False
    franchise_match = False
    franchise_name = None

    # Determinar ID correcto del juego actual según el servicio disponible
    if game.igdb_id:
        correct_game_id = game.igdb_id
        game_service = "igdb"
        print(f"Juego actual: IGDB ID {correct_game_id}")
    elif game.rawg_id:
        correct_game_id = game.rawg_id
        game_service = "rawg"
        print(f"Juego actual: RAWG ID {correct_game_id}")
    else:
        print("ERROR: El juego no tiene ID válido")
        return {"success": False, "error": "Juego sin ID válido"}

    print(
        f"Comparando: {guessed_game_name} (ID: {guessed_game_id}, servicio: {service_type})"
    )
    print(f"Con: {game.title} (ID: {correct_game_id}, servicio: {game_service})")

    # Verificar si es el juego correcto
    if guessed_game_id == correct_game_id and service_type == game_service:
        is_correct = True
        print(f"Respuesta correcta: {guessed_game_name}")
    else:
        print(f"Respuesta incorrecta: {guessed_game_name} != {game.title}")
        print(
            f"   IDs: {guessed_game_id} != {correct_game_id} o servicios: {service_type} != {game_service}"
        )

        # Verificar franquicia si el juego correcto tiene franquicia
        if game.franchise_name and game.franchise_slug:
            print(f"Verificando franquicia del juego correcto: {game.franchise_name}")

            # Obtener franquicia del juego adivinado según el servicio
            if service_type == "igdb":
                igdb_service = IGDBService()
                guessed_game_details = igdb_service.get_game_details(guessed_game_id)
                if guessed_game_details:
                    guessed_franchise_name = igdb_service.get_franchise_name(
                        guessed_game_details
                    )
                    guessed_franchise_slug = igdb_service.get_franchise_slug(
                        guessed_game_details
                    )
                else:
                    guessed_franchise_name, guessed_franchise_slug = None, None
            else:
                rawg_service = RAWGService()
                guessed_franchise_name, guessed_franchise_slug = (
                    rawg_service.get_franchise_for_game_id(guessed_game_id)
                )

            if guessed_franchise_name and guessed_franchise_slug:
                print(f"Franquicia del juego adivinado: {guessed_franchise_name}")

                if (
                    game.franchise_slug == guessed_franchise_slug
                    or game.franchise_name.lower() == guessed_franchise_name.lower()
                ):
                    franchise_match = True
                    franchise_name = game.franchise_name
                    print(f"¡Franquicia correcta!: {franchise_name}")
                else:
                    print(
                        f"Franquicias diferentes: '{game.franchise_name}' vs '{guessed_franchise_name}'"
                    )
            else:
                print("No se pudo obtener franquicia del juego adivinado")
        else:
            print("El juego correcto no tiene franquicia definida")

    # Crear registro del intento
    attempt_data = {
        "attempt": game_state["current_attempt"],
        "type": "guess",
        "game_name": guessed_game_name,
        "game_id": guessed_game_id,
        "service": service_type,
        "correct": is_correct,
        "franchise_match": franchise_match,
        "franchise_name": franchise_name,
    }

    game_state["attempts"].append(attempt_data)

    if is_correct:
        game_state["won"] = True
        if game_state["current_attempt"] == 1:
            game_state["guessed_it"] = True
    else:
        game_state["current_attempt"] += 1

        # Calcular máximo de intentos según disponibilidad de GIF
        has_gif = game.gif_path and game.gif_path.strip()
        max_attempts = 6 if has_gif else min(6, game.screenshot_set.count())

        if game_state["current_attempt"] > max_attempts:
            game_state["lost"] = True

    return {
        "success": True,
        "correct": is_correct,
        "franchise_match": franchise_match,
        "franchise_name": franchise_name,
        "current_attempt": game_state["current_attempt"],
        "won": game_state["won"],
        "lost": game_state.get("lost", False),
        "guessed_it": game_state.get("guessed_it", False),
        "game_name": game.title if is_correct else None,
    }


def check_franchise_match(correct_title, guessed_title):
    """Verificar si dos juegos pertenecen a la misma franquicia"""
    franchise_words = [
        "Call of Duty",
        "Assassin's Creed",
        "Grand Theft Auto",
        "The Elder Scrolls",
        "Fallout",
        "FIFA",
        "Madden",
        "Metal Gear",
        "Final Fantasy",
        "Dragon Age",
    ]

    correct_lower = correct_title.lower()
    guessed_lower = guessed_title.lower()

    for franchise in franchise_words:
        if franchise.lower() in correct_lower and franchise.lower() in guessed_lower:
            return True

    return False


def test_rawg_view(request):
    """Vista de prueba RAWG original"""
    rawg_service = RAWGService()
    game = rawg_service.select_random_game()

    if game:
        return render(request, "test_random_game.html", {"game": game})
    else:
        return render(
            request,
            "game/no_game_available.html",
            {"error": "No se pudo obtener un juego"},
        )


def test_igdb_view(request):
    """Vista de prueba para IGDB"""
    igdb_service = IGDBService()
    game = igdb_service.select_random_game()

    if game:
        return render(
            request, "test_random_game.html", {"game": game, "service": "IGDB"}
        )
    else:
        return render(
            request,
            "game/no_game_available.html",
            {"error": "No se pudo obtener un juego con IGDB"},
        )


def compare_services_view(request):
    """Vista para comparar resultados de RAWG vs IGDB"""
    try:
        rawg_service = RAWGService()
        igdb_service = IGDBService()

        # Generar juego con cada servicio
        rawg_game = rawg_service.select_random_game()
        igdb_game = igdb_service.select_random_game()

        context = {
            "rawg_game": rawg_game,
            "igdb_game": igdb_game,
            "comparison_data": {
                "rawg_available": rawg_game is not None,
                "igdb_available": igdb_game is not None,
                "rawg_franchises": rawg_game.franchise_name if rawg_game else None,
                "igdb_franchises": igdb_game.franchise_name if igdb_game else None,
            },
        }

        return render(request, "test_services_comparison.html", context)

    except Exception as e:
        return render(
            request,
            "game/no_game_available.html",
            {"error": f"Error comparando servicios: {str(e)}"},
        )


def debug_igdb_auth(request):
    """Vista para debuggear autenticación IGDB"""
    try:
        igdb_service = IGDBService()

        # Probar autenticación
        token = igdb_service.get_access_token()

        if token:
            # Probar búsqueda simple
            search_results = igdb_service.search_games("Mario", limit=3)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>Debug IGDB</title></head>
            <body>
            <h1>Debug IGDB Authentication</h1>
            <p><strong>Token obtenido:</strong> ✅ Sí (oculto por seguridad)</p>
            <p><strong>Búsqueda funciona:</strong> {'✅ Sí' if search_results else '❌ No'}</p>
            <h2>Resultados de búsqueda "Mario":</h2>
            <ul>
            """

            for game in search_results or []:
                html += (
                    f"<li>{game.get('name', 'N/A')} (ID: {game.get('id', 'N/A')})</li>"
                )

            html += """
            </ul>
            </body>
            </html>
            """
        else:
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Debug IGDB</title></head>
            <body>
            <h1>Debug IGDB Authentication</h1>
            <p><strong>Token obtenido:</strong> ❌ No</p>
            <p>Verificar credenciales IGDB_CLIENT_ID e IGDB_CLIENT_SECRET</p>
            </body>
            </html>
            """

        from django.http import HttpResponse

        return HttpResponse(html)

    except Exception as e:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Debug IGDB Error</title></head>
        <body>
        <h1>Error en Debug IGDB</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        </body>
        </html>
        """
        from django.http import HttpResponse

        return HttpResponse(html)
