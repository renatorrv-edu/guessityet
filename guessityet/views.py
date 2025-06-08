# guessityet/views.py - Migrado a Class-Based Views
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, DetailView, ListView, CreateView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
import json
import time
import re

from .models import Game, DailyGame, Screenshot, UserProfile, UserGameAttempt
from .services.rawg_service import RAWGService
from .services.igdb_service import IGDBService
from .forms import CustomUserCreationForm


class DailyGameView(TemplateView):
    """Vista principal del juego diario"""

    template_name = "game/daily_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().astimezone().date()

        try:
            daily_game = DailyGame.objects.get(date=today)
            game = daily_game.game
            print(f"Juego diario encontrado para {today}: {game.title}")
        except DailyGame.DoesNotExist:
            # Si no hay juego para hoy, mostrar mensaje informativo
            print(f"No hay juego diario disponible para {today}")
            context.update(
                {
                    "no_game": True,
                    "today": today,
                    "message": "El juego diario aún no está disponible. Los juegos se publican automáticamente a las 00:00.",
                    "next_game_time": "00:00",
                }
            )
            return context

        # Inicializar sesión de juego si es necesario
        if (
            "game_state" not in self.request.session
            or self.request.session.get("game_state", {}).get("game_id") != game.id
        ):
            self.init_game_session(game)

        screenshots = game.screenshot_set.all().order_by("difficulty")
        game_state = self.request.session["game_state"]

        context.update(
            {
                "game": game,
                "screenshots": screenshots,
                "game_state": game_state,
                "game_state_json": json.dumps(game_state),
                "today": today,
            }
        )

        return context

    def init_game_session(self, game):
        """Inicializar el estado del juego en la sesión"""
        self.request.session["game_state"] = {
            "game_id": game.id,
            "current_attempt": 1,
            "attempts": [],
            "won": False,
            "lost": False,
            "guessed_it": False,
        }
        self.request.session.modified = True


class GameHistoryView(ListView):
    """Vista del historial de juegos diarios"""

    model = DailyGame
    template_name = "game/game_history.html"
    context_object_name = "daily_games"
    paginate_by = 12
    ordering = ["-date"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("game")

        # Agregar información de si el usuario completó cada juego
        if self.request.user.is_authenticated:
            # Prefetch related user attempts
            queryset = queryset.prefetch_related("usergameattempt_set")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            # Obtener intentos del usuario para los juegos en la página actual
            daily_game_ids = [dg.id for dg in context["daily_games"]]
            user_attempts = UserGameAttempt.objects.filter(
                user=self.request.user, daily_game_id__in=daily_game_ids
            ).values("daily_game_id", "success", "attempts_used")

            # Crear diccionario para lookup rápido
            attempts_dict = {
                attempt["daily_game_id"]: attempt for attempt in user_attempts
            }

            # Añadir info de completado a cada juego
            for daily_game in context["daily_games"]:
                daily_game.user_attempt = attempts_dict.get(daily_game.id)

        context["total_games"] = self.get_queryset().count()
        return context


class GameDetailView(DetailView):
    """Vista de detalle de un juego específico por fecha"""

    model = DailyGame
    template_name = "game/game_detail.html"
    context_object_name = "daily_game"

    def get_object(self, queryset=None):
        try:
            game_date = datetime.strptime(self.kwargs["date"], "%Y-%m-%d").date()
            return get_object_or_404(DailyGame, date=game_date)
        except ValueError:
            messages.error(self.request, "Fecha de juego inválida")
            return None

    def get(self, request, *args, **kwargs):
        daily_game = self.get_object()
        if daily_game is None:
            return redirect("guessityet:game_history")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        daily_game = context["daily_game"]

        # Obtener información del intento del usuario si está autenticado
        user_attempt = None
        if self.request.user.is_authenticated:
            try:
                user_attempt = UserGameAttempt.objects.get(
                    user=self.request.user, daily_game=daily_game
                )
            except UserGameAttempt.DoesNotExist:
                pass

        context.update(
            {
                "game": daily_game.game,
                "screenshots": daily_game.game.screenshot_set.all().order_by(
                    "difficulty"
                ),
                "user_attempt": user_attempt,
            }
        )

        return context


# ============================================================================
# VISTAS DE PÁGINAS INFORMATIVAS
# ============================================================================


class HowToPlayView(TemplateView):
    """Vista de cómo jugar"""

    template_name = "pages/how_to_play.html"


class AboutView(TemplateView):
    """Vista de acerca de"""

    template_name = "pages/about.html"


# ============================================================================
# VISTAS DE AUTENTICACIÓN
# ============================================================================


class CustomRegisterView(CreateView):
    """Vista de registro personalizada"""

    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)

        # Crear perfil de usuario automáticamente
        UserProfile.objects.create(user=self.object)

        # Mensaje de éxito
        messages.success(
            self.request,
            f"¡Cuenta creada para {self.object.username}! Ya puedes iniciar sesión.",
        )

        return response

    def dispatch(self, request, *args, **kwargs):
        # Redirigir si ya está autenticado
        if request.user.is_authenticated:
            return redirect("guessityet:daily_game")
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    """Vista del perfil de usuario"""

    template_name = "accounts/profile.html"
    login_url = "/cuentas/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile, created = UserProfile.objects.get_or_create(user=self.request.user)

        # Obtener estadísticas del usuario
        user_attempts = UserGameAttempt.objects.filter(user=self.request.user)
        recent_games = user_attempts.select_related("daily_game__game").order_by(
            "-completed_at"
        )[:5]

        # Calcular estadísticas avanzadas
        total_games = user_attempts.count()
        won_games = user_attempts.filter(success=True).count()
        guessed_it_games = user_attempts.filter(success=True, attempts_used=1).count()

        # Calcular racha actual
        current_streak = self.calculate_current_streak()

        # Estadísticas por número de intentos
        attempts_stats = {}
        for i in range(1, 7):
            attempts_stats[i] = user_attempts.filter(
                success=True, attempts_used=i
            ).count()

        win_rate = (won_games / total_games * 100) if total_games > 0 else 0
        guessed_it_rate = (
            (guessed_it_games / total_games * 100) if total_games > 0 else 0
        )

        context.update(
            {
                "profile": profile,
                "total_games": total_games,
                "won_games": won_games,
                "guessed_it_games": guessed_it_games,
                "win_rate": round(win_rate, 1),
                "guessed_it_rate": round(guessed_it_rate, 1),
                "current_streak": current_streak,
                "recent_games": recent_games,
                "attempts_stats": attempts_stats,
            }
        )

        return context

    def calculate_current_streak(self):
        """Calcular la racha actual del usuario"""
        attempts = (
            UserGameAttempt.objects.filter(user=self.request.user)
            .select_related("daily_game")
            .order_by("-daily_game__date")
        )

        current_streak = 0
        for attempt in attempts:
            if attempt.success:
                current_streak += 1
            else:
                break

        return current_streak


class UpdateProfileView(LoginRequiredMixin, View):
    """Vista para actualizar el perfil"""

    login_url = "/cuentas/login/"

    def post(self, request, *args, **kwargs):
        # Aquí implementarías campos personalizados del perfil
        # Por ejemplo: avatar, configuraciones, etc.

        user = request.user
        profile = user.profile

        # Ejemplo de campos que podrías actualizar:
        # first_name = request.POST.get('first_name', '')
        # last_name = request.POST.get('last_name', '')
        # email = request.POST.get('email', '')

        # user.first_name = first_name
        # user.last_name = last_name
        # user.email = email
        # user.save()

        messages.success(request, "Perfil actualizado correctamente.")
        return redirect("guessityet:profile")

    def get(self, request, *args, **kwargs):
        return redirect("guessityet:profile")


# ============================================================================
# VISTAS DE TESTING Y DEBUG (solo en desarrollo)
# ============================================================================


class GenerateTestGameView(View):
    """Generar un nuevo juego de prueba usando RAWG"""

    def get(self, request, *args, **kwargs):
        print("Forzando generación de nuevo juego de prueba...")

        request.session.flush()

        rawg_service = RAWGService()
        game = rawg_service.select_random_game()

        if game:
            print(f"Nuevo juego generado: {game.title}")
            request.session["current_test_game_id"] = game.id
            request.session.modified = True
            return HttpResponseRedirect(reverse("guessityet:test_rawg_view"))
        else:
            print("No se pudo generar juego")
            return render(
                request,
                "game/no_game_available.html",
                {"error": "No se pudo generar un juego de prueba"},
            )


class GenerateTestGameIGDBView(View):
    """Generar un nuevo juego de prueba usando IGDB"""

    def get(self, request, *args, **kwargs):
        print("Forzando generación de nuevo juego de prueba con IGDB...")

        request.session.flush()

        igdb_service = IGDBService()
        game = igdb_service.select_random_game()

        if game:
            print(f"Nuevo juego generado con IGDB: {game.title}")
            request.session["current_test_game_id"] = game.id
            request.session.modified = True
            return HttpResponseRedirect(reverse("guessityet:test_igdb_view"))
        else:
            print("No se pudo generar juego con IGDB")
            return render(
                request,
                "game/no_game_available.html",
                {"error": "No se pudo generar un juego de prueba con IGDB"},
            )


class TestRAWGView(TemplateView):
    """Vista de prueba RAWG"""

    template_name = "test_random_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        rawg_service = RAWGService()
        game = rawg_service.select_random_game()

        if game:
            context["game"] = game
        else:
            context["error"] = "No se pudo obtener un juego"
            self.template_name = "game/no_game_available.html"

        return context


class TestIGDBView(TemplateView):
    """Vista de prueba para IGDB"""

    template_name = "test_random_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        igdb_service = IGDBService()
        game = igdb_service.select_random_game()

        if game:
            context.update({"game": game, "service": "IGDB"})
        else:
            context["error"] = "No se pudo obtener un juego con IGDB"
            self.template_name = "game/no_game_available.html"

        return context


class CompareServicesView(TemplateView):
    """Vista para comparar resultados de RAWG vs IGDB"""

    template_name = "test_services_comparison.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            rawg_service = RAWGService()
            igdb_service = IGDBService()

            # Generar juego con cada servicio
            rawg_game = rawg_service.select_random_game()
            igdb_game = igdb_service.select_random_game()

            context.update(
                {
                    "rawg_game": rawg_game,
                    "igdb_game": igdb_game,
                    "comparison_data": {
                        "rawg_available": rawg_game is not None,
                        "igdb_available": igdb_game is not None,
                        "rawg_franchises": (
                            rawg_game.franchise_name if rawg_game else None
                        ),
                        "igdb_franchises": (
                            igdb_game.franchise_name if igdb_game else None
                        ),
                    },
                }
            )
        except Exception as e:
            context["error"] = f"Error comparando servicios: {str(e)}"
            self.template_name = "game/no_game_available.html"

        return context


class DebugFranchiseView(TemplateView):
    """Vista temporal para probar franquicias de RAWG"""

    def get(self, request, *args, **kwargs):
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

        return HttpResponse(html)


class DebugIGDBAuthView(TemplateView):
    """Vista para debuggear autenticación IGDB"""

    def get(self, request, *args, **kwargs):
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
                    html += f"<li>{game.get('name', 'N/A')} (ID: {game.get('id', 'N/A')})</li>"

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
            return HttpResponse(html)


# ============================================================================
# VISTAS AJAX (mantener como function-based para simplicidad)
# ============================================================================


@require_http_methods(["GET"])
def search_games_ajax(request):
    """Búsqueda de juegos para el autocompletado"""
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
            request, game, guessed_game_name, guessed_game_id, service_type, game_state
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


# ============================================================================
# FUNCIONES DE UTILIDAD (conservar como están)
# ============================================================================


def process_guess(
    request, game, guessed_game_name, guessed_game_id, service_type, game_state
):
    """Procesar la respuesta del jugador y determinar si es correcta"""
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

    # Guardar estadísticas del usuario si está autenticado
    if request.user.is_authenticated:
        save_user_attempt(request, game, is_correct, game_state["current_attempt"] - 1)

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


def save_user_attempt(request, game, success, attempts_used):
    """Guardar intento del usuario en la base de datos"""
    try:
        # Obtener el DailyGame actual
        today = timezone.now().date()
        daily_game = DailyGame.objects.get(date=today, game=game)

        # Crear o actualizar el intento del usuario
        user_attempt, created = UserGameAttempt.objects.update_or_create(
            user=request.user,
            daily_game=daily_game,
            defaults={
                "success": success,
                "attempts_used": attempts_used,
                "completed_at": timezone.now() if success else None,
            },
        )

        # Actualizar estadísticas del perfil solo si es un nuevo intento exitoso
        if success and created:
            profile = request.user.profile
            profile.games_won += 1
            if attempts_used == 1:
                profile.guessed_it += 1

            # Actualizar racha
            profile.current_streak = calculate_user_streak(request.user)
            if profile.current_streak > profile.max_streak:
                profile.max_streak = profile.current_streak

            profile.save()

    except DailyGame.DoesNotExist:
        print(f"No se encontró DailyGame para el juego {game.title}")
    except Exception as e:
        print(f"Error guardando intento del usuario: {e}")


def calculate_user_streak(user):
    """Calcular la racha actual del usuario"""
    attempts = (
        UserGameAttempt.objects.filter(user=user)
        .select_related("daily_game")
        .order_by("-daily_game__date")
    )

    current_streak = 0
    for attempt in attempts:
        if attempt.success:
            current_streak += 1
        else:
            break

    return current_streak


def insert_spaces_in_compound_words(query):
    """Insertar espacios en palabras compuestas comunes de videojuegos"""
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


# ============================================================================
# VISTAS DE MANEJO DE ERRORES
# ============================================================================


def custom_404(request, exception):
    """Vista personalizada para error 404"""
    return render(request, "errors/404.html", status=404)


def custom_500(request):
    """Vista personalizada para error 500"""
    return render(request, "errors/500.html", status=500)


# ============================================================================
# ALIASES DE VISTAS (para compatibilidad con URLs existentes)
# ============================================================================

# Crear instancias de las class-based views para usar en urls.py
daily_game = DailyGameView.as_view()
game_history = GameHistoryView.as_view()
game_detail = GameDetailView.as_view()
how_to_play = HowToPlayView.as_view()
about = AboutView.as_view()
profile = ProfileView.as_view()
update_profile = UpdateProfileView.as_view()

# Vistas de testing
generate_test_game = GenerateTestGameView.as_view()
generate_test_game_igdb = GenerateTestGameIGDBView.as_view()
test_rawg_view = TestRAWGView.as_view()
test_igdb_view = TestIGDBView.as_view()
compare_services_view = CompareServicesView.as_view()
debug_franchise = DebugFranchiseView.as_view()
debug_igdb_auth = DebugIGDBAuthView.as_view()
