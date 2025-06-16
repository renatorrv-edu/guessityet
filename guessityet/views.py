# guessityet/views.py - Migrado a Class-Based Views con confirmación de email
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, Http404
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
from django.contrib.auth.models import User
from datetime import datetime, timedelta
import json
import time
import re
import logging

from .models import (
    Game,
    DailyGame,
    Screenshot,
    UserProfile,
    UserGameAttempt,
    EmailConfirmationToken,
)
from .services.rawg_service import RAWGService
from .services.igdb_service import IGDBService
from .services.email_service import EmailService
from .forms import CustomUserCreationForm

logger = logging.getLogger(__name__)


# ============================================================================
# VISTAS PRINCIPALES DEL JUEGO
# ============================================================================


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
    """Vista del historial de juegos diarios - Mejorada para mostrar progreso detallado"""

    model = DailyGame
    template_name = "game/game_history.html"
    context_object_name = "daily_games"
    paginate_by = 12
    ordering = ["-date"]  # Orden inverso (más recientes primero)

    def get_queryset(self):
        queryset = super().get_queryset().select_related("game")

        # Solo prefetch para usuarios autenticados
        if self.request.user.is_authenticated:
            queryset = queryset.prefetch_related("usergameattempt_set")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calcular el número de juego para cada elemento (orden inverso)
        total_games = self.get_queryset().count()

        # Solo calcular datos para usuarios autenticados
        if self.request.user.is_authenticated:
            # Obtener intentos del usuario para los juegos en la página actual
            daily_game_ids = [dg.id for dg in context["daily_games"]]
            user_attempts = UserGameAttempt.objects.filter(
                user=self.request.user, daily_game_id__in=daily_game_ids
            ).select_related("daily_game")

            # Crear diccionario para lookup rápido
            attempts_dict = {
                attempt.daily_game_id: attempt for attempt in user_attempts
            }

            # Enriquecer cada juego con información detallada
            for idx, daily_game in enumerate(context["daily_games"]):
                daily_game.user_attempt = attempts_dict.get(daily_game.id)
                daily_game.game_number = total_games - (
                    (context["page_obj"].number - 1) * self.paginate_by + idx
                )

            # Calcular estadísticas del usuario para mostrar en el template
            all_user_attempts = UserGameAttempt.objects.filter(user=self.request.user)
            total_played = all_user_attempts.count()
            total_won = all_user_attempts.filter(success=True).count()
            win_rate = (total_won / total_played * 100) if total_played > 0 else 0

            context["user_stats"] = {
                "played": total_played,
                "won": total_won,
                "win_rate": round(win_rate, 1),
            }
        else:
            # Para usuarios no autenticados, solo números y fechas
            for idx, daily_game in enumerate(context["daily_games"]):
                daily_game.user_attempt = None
                daily_game.game_number = total_games - (
                    (context["page_obj"].number - 1) * self.paginate_by + idx
                )

            context["user_stats"] = {
                "played": 0,
                "won": 0,
                "win_rate": 0,
            }

        context["total_games"] = total_games
        return context


class RandomGameView(View):
    """Vista para generar y jugar un juego aleatorio"""

    def post(self, request, *args, **kwargs):
        try:
            # Obtener un juego aleatorio de los ya disponibles
            random_daily_game = DailyGame.objects.order_by("?").first()

            if not random_daily_game:
                return JsonResponse(
                    {"error": "No hay juegos disponibles", "success": False}, status=404
                )

            # Redirigir directamente a GameDetailView con el juego aleatorio
            return JsonResponse(
                {
                    "success": True,
                    "redirect_url": reverse(
                        "guessityet:game_detail",
                        args=[random_daily_game.date.strftime("%Y-%m-%d")],
                    ),
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e), "success": False}, status=500)


class GameDetailView(DetailView):
    """Vista de detalle de un juego específico por fecha - Mejorada"""

    model = DailyGame
    template_name = "game/daily_game.html"  # Reutilizar el template principal
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

        # Determinar si es el juego de hoy
        today = timezone.now().astimezone().date()
        is_today = daily_game.date == today

        # SI EL USUARIO YA COMPLETÓ EL JUEGO: cargar el estado desde la BD
        if user_attempt and (user_attempt.success or user_attempt.attempts_data):
            # Reconstruir el game_state desde los datos guardados
            game_state = {
                "game_id": daily_game.game.id,
                "current_attempt": (
                    user_attempt.attempts_used + 1
                    if not user_attempt.success
                    else user_attempt.attempts_used
                ),
                "attempts": user_attempt.attempts_data,
                "won": user_attempt.success,
                "lost": not user_attempt.success
                and len(user_attempt.attempts_data) >= 6,
                "guessed_it": user_attempt.success and user_attempt.attempts_used == 1,
            }

            # Actualizar la sesión con el estado completado
            self.request.session["game_state"] = game_state
            self.request.session.modified = True

        else:
            # SI NO HA JUGADO: crear nuevo game_state
            # Limpiar la sesión para empezar fresh
            if "game_state" in self.request.session:
                del self.request.session["game_state"]

            # Inicializar sesión de juego para este juego específico
            game_state = {
                "game_id": daily_game.game.id,
                "current_attempt": 1,
                "attempts": [],
                "won": False,
                "lost": False,
                "guessed_it": False,
            }
            self.request.session["game_state"] = game_state
            self.request.session.modified = True

        context.update(
            {
                "game": daily_game.game,
                "screenshots": daily_game.game.screenshot_set.all().order_by(
                    "difficulty"
                ),
                "game_state": game_state,
                "game_state_json": json.dumps(game_state),
                "user_attempt": user_attempt,
                "today": daily_game.date,  # Usar la fecha del juego, no hoy
                "is_historical": not is_today,  # Flag para mostrar si es histórico
                "historical_date": daily_game.date if not is_today else None,
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
# VISTAS DE AUTENTICACIÓN CON CONFIRMACIÓN DE EMAIL
# ============================================================================


class CustomLoginView(LoginView):
    """Vista de login personalizada"""

    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("guessityet:daily_game")


class CustomRegisterView(CreateView):
    """Vista de registro personalizada con confirmación de email"""

    form_class = CustomUserCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("guessityet:registration_complete")

    def form_valid(self, form):
        response = super().form_valid(form)

        # El usuario se crea pero no se activa hasta confirmar email
        user = self.object
        user.is_active = False
        user.save()

        # Crear perfil de usuario
        UserProfile.objects.get_or_create(user=user)

        # Enviar email de confirmación
        email_service = EmailService()
        email_service.send_confirmation_email(user, self.request)

        messages.success(
            self.request,
            f"Te hemos enviado un email de confirmación a {user.email}. "
            f"Por favor, revisa tu bandeja de entrada y spam.",
        )

        return response

    def form_invalid(self, form):
        # Verificar si el email ya existe pero no está confirmado
        email = form.cleaned_data.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    messages.warning(
                        self.request,
                        f"Ya existe una cuenta con este email que no ha sido confirmada. "
                        f"Revisa tu email {user.email} o solicita un reenvío.",
                    )
                    return redirect("login")

            except User.DoesNotExist:
                pass

        return super().form_invalid(form)


class RegistrationCompleteView(TemplateView):
    """Vista que se muestra después del registro"""

    template_name = "registration/registration_complete.html"


class ConfirmEmailView(View):
    """Vista para confirmar el email del usuario"""

    def get(self, request, token, *args, **kwargs):
        try:
            email_token = get_object_or_404(EmailConfirmationToken, token=token)

            if not email_token.is_valid():
                if email_token.is_used:
                    messages.error(
                        request, "Este enlace de confirmación ya ha sido utilizado."
                    )
                else:
                    messages.error(request, "Este enlace de confirmación ha expirado.")
                return redirect("login")

            # Activar usuario
            user = email_token.user
            user.is_active = True
            user.save()

            # Marcar token como usado
            email_token.is_used = True
            email_token.save()

            # Login automático
            login(request, user)

            messages.success(
                request,
                f"¡Bienvenido {user.username}! Tu cuenta ha sido confirmada exitosamente.",
            )
            return redirect("guessityet:daily_game")

        except Exception as e:
            logger.error(f"Error confirmando email: {e}")
            messages.error(
                request, "Hubo un error confirmando tu email. Inténtalo nuevamente."
            )
            return redirect("login")


class ResendConfirmationView(View):
    """Vista para reenviar email de confirmación"""

    def post(self, request, *args, **kwargs):
        email = request.POST.get("email", "").strip()

        if not email:
            messages.error(request, "Email requerido.")
            return redirect("login")

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                messages.info(request, "Esta cuenta ya está activada.")
                return redirect("login")

            # Reenviar email de confirmación
            email_service = EmailService()
            email_service.send_confirmation_email(user, request)

            messages.success(
                request,
                f"Hemos reenviado el email de confirmación a {email}. "
                f"Revisa tu bandeja de entrada y spam.",
            )

        except User.DoesNotExist:
            # Por seguridad, no revelamos si el email existe o no
            messages.success(
                request,
                f"Si existe una cuenta con este email, recibirás un enlace de confirmación.",
            )

        return redirect("login")


class ProfileView(LoginRequiredMixin, TemplateView):
    """Vista del perfil de usuario mejorada"""

    template_name = "accounts/profile.html"
    login_url = "/cuentas/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile, created = UserProfile.objects.get_or_create(user=self.request.user)

        # Obtener estadísticas del usuario
        user_attempts = UserGameAttempt.objects.filter(user=self.request.user)

        # Últimas 10 partidas jugadas (con más información)
        recent_games = user_attempts.select_related("daily_game__game").order_by(
            "-completed_at"
        )[:10]

        # Calcular estadísticas avanzadas
        total_games = user_attempts.count()
        won_games = user_attempts.filter(success=True).count()
        guessed_it_games = user_attempts.filter(success=True, attempts_used=1).count()

        # Calcular racha actual y máxima
        current_streak = self.calculate_current_streak()
        max_streak = profile.max_streak

        # Estadísticas por número de intentos
        attempts_stats = {}
        for i in range(1, 7):
            attempts_stats[i] = user_attempts.filter(
                success=True, attempts_used=i
            ).count()

        # Calcular porcentajes
        win_rate = (won_games / total_games * 100) if total_games > 0 else 0
        guessed_it_rate = (
            (guessed_it_games / total_games * 100) if total_games > 0 else 0
        )

        # Obtener el mejor y peor rendimiento por desarrollador/género
        performance_by_developer = self.get_performance_by_developer()
        performance_by_genre = self.get_performance_by_genre()

        # Estadísticas mensuales
        monthly_stats = self.get_monthly_stats()

        # Actividad reciente (últimos 30 días)
        recent_activity = self.get_recent_activity()

        context.update(
            {
                "profile": profile,
                "total_games": total_games,
                "won_games": won_games,
                "guessed_it_games": guessed_it_games,
                "win_rate": round(win_rate, 1),
                "guessed_it_rate": round(guessed_it_rate, 1),
                "current_streak": current_streak,
                "max_streak": max_streak,
                "recent_games": recent_games,
                "attempts_stats": attempts_stats,
                "performance_by_developer": performance_by_developer,
                "performance_by_genre": performance_by_genre,
                "monthly_stats": monthly_stats,
                "recent_activity": recent_activity,
            }
        )

        return context

    def calculate_current_streak(self):
        """Calcular la racha actual del usuario"""
        from datetime import date, timedelta

        today = timezone.now().date()
        current_date = today
        current_streak = 0

        # Revisar día por día hacia atrás
        while True:
            try:
                daily_game = DailyGame.objects.get(date=current_date)
                user_attempt = UserGameAttempt.objects.get(
                    user=self.request.user, daily_game=daily_game
                )

                if user_attempt.success:
                    current_streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

            except (DailyGame.DoesNotExist, UserGameAttempt.DoesNotExist):
                break

        return current_streak

    def get_performance_by_developer(self):
        """Obtener rendimiento por desarrollador"""
        from django.db.models import Count, Q

        attempts_with_developer = UserGameAttempt.objects.filter(
            user=self.request.user, daily_game__game__developer__isnull=False
        ).exclude(daily_game__game__developer="")

        developer_stats = {}

        for attempt in attempts_with_developer:
            developer = attempt.daily_game.game.developer
            if developer not in developer_stats:
                developer_stats[developer] = {"total": 0, "won": 0}

            developer_stats[developer]["total"] += 1
            if attempt.success:
                developer_stats[developer]["won"] += 1

        # Calcular porcentajes y filtrar desarrolladores con al menos 2 juegos
        filtered_stats = []
        for dev, stats in developer_stats.items():
            if stats["total"] >= 2:
                win_rate = (stats["won"] / stats["total"]) * 100
                filtered_stats.append(
                    {
                        "developer": dev,
                        "total": stats["total"],
                        "won": stats["won"],
                        "win_rate": round(win_rate, 1),
                    }
                )

        # Ordenar por win rate
        return sorted(filtered_stats, key=lambda x: x["win_rate"], reverse=True)[:5]

    def get_performance_by_genre(self):
        """Obtener rendimiento por género"""
        attempts_with_genre = UserGameAttempt.objects.filter(
            user=self.request.user, daily_game__game__genres__isnull=False
        ).exclude(daily_game__game__genres="")

        genre_stats = {}

        for attempt in attempts_with_genre:
            genres = attempt.daily_game.game.genres.split(",")
            for genre in genres:
                genre = genre.strip()
                if genre and genre not in genre_stats:
                    genre_stats[genre] = {"total": 0, "won": 0}

                if genre:
                    genre_stats[genre]["total"] += 1
                    if attempt.success:
                        genre_stats[genre]["won"] += 1

        # Calcular porcentajes y filtrar géneros con al menos 2 juegos
        filtered_stats = []
        for genre, stats in genre_stats.items():
            if stats["total"] >= 2:
                win_rate = (stats["won"] / stats["total"]) * 100
                filtered_stats.append(
                    {
                        "genre": genre,
                        "total": stats["total"],
                        "won": stats["won"],
                        "win_rate": round(win_rate, 1),
                    }
                )

        return sorted(filtered_stats, key=lambda x: x["win_rate"], reverse=True)[:5]

    def get_monthly_stats(self):
        """Obtener estadísticas de los últimos 6 meses"""
        from datetime import date, timedelta
        from django.db.models import Count

        today = timezone.now().date()
        six_months_ago = today - timedelta(days=180)

        monthly_data = []
        current_date = today.replace(day=1)  # Primer día del mes actual

        for i in range(6):
            month_start = current_date
            if current_date.month == 12:
                month_end = current_date.replace(
                    year=current_date.year + 1, month=1
                ) - timedelta(days=1)
            else:
                month_end = current_date.replace(
                    month=current_date.month + 1
                ) - timedelta(days=1)

            attempts_in_month = UserGameAttempt.objects.filter(
                user=self.request.user,
                daily_game__date__gte=month_start,
                daily_game__date__lte=month_end,
            )

            total = attempts_in_month.count()
            won = attempts_in_month.filter(success=True).count()

            monthly_data.append(
                {
                    "month": current_date.strftime("%B %Y"),
                    "total": total,
                    "won": won,
                    "win_rate": round((won / total * 100), 1) if total > 0 else 0,
                }
            )

            # Mes anterior
            if current_date.month == 1:
                current_date = current_date.replace(
                    year=current_date.year - 1, month=12
                )
            else:
                current_date = current_date.replace(month=current_date.month - 1)

        return list(reversed(monthly_data))

    def get_recent_activity(self):
        """Obtener actividad de los últimos 30 días"""
        from datetime import date, timedelta

        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        recent_attempts = (
            UserGameAttempt.objects.filter(
                user=self.request.user, daily_game__date__gte=thirty_days_ago
            )
            .select_related("daily_game__game")
            .order_by("-daily_game__date")
        )

        return {
            "total_games": recent_attempts.count(),
            "won_games": recent_attempts.filter(success=True).count(),
            "guessed_it": recent_attempts.filter(success=True, attempts_used=1).count(),
            "average_attempts": round(
                sum(a.attempts_used for a in recent_attempts if a.success)
                / max(recent_attempts.filter(success=True).count(), 1),
                1,
            ),
        }


class PublicProfileView(TemplateView):
    """Vista pública del perfil de usuario (para retos futuros)"""

    template_name = "accounts/public_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = kwargs.get("username")

        try:
            user = User.objects.get(username=username)
            profile = user.profile

            # Solo mostrar estadísticas públicas básicas
            user_attempts = UserGameAttempt.objects.filter(user=user)

            context.update(
                {
                    "profile_user": user,
                    "profile": profile,
                    "total_games": user_attempts.count(),
                    "won_games": user_attempts.filter(success=True).count(),
                    "guessed_it_games": user_attempts.filter(
                        success=True, attempts_used=1
                    ).count(),
                    "current_streak": profile.current_streak,
                    "max_streak": profile.max_streak,
                }
            )

        except User.DoesNotExist:
            context["user_not_found"] = True

        return context


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
# AJAX ENDPOINTS PARA EL JUEGO
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
# FUNCIONES DE UTILIDAD
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
                    print(f"¡Franquicia correcta: {franchise_name}")
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
        # Buscar el DailyGame correspondiente a este juego
        daily_game = DailyGame.objects.filter(game=game).first()

        if daily_game:
            # Determinar si es el juego más reciente disponible (lo consideramos "actual")
            latest_game = DailyGame.objects.order_by("-date").first()
            is_current_game = latest_game and daily_game.id == latest_game.id

            if is_current_game:
                # Es el juego más reciente, actualizar estadísticas
                save_user_attempt(
                    request, daily_game, is_correct, game_state["current_attempt"]
                )
            else:
                # Es un juego anterior, no actualizar estadísticas
                save_historical_user_attempt(
                    request, daily_game, is_correct, game_state["current_attempt"]
                )

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


def save_user_attempt(request, daily_game, success, attempts_used):
    """Guardar intento del usuario en la base de datos con detalles completos"""
    try:
        # Obtener los detalles de los intentos desde la sesión
        game_state = request.session.get("game_state", {})
        attempts_data = game_state.get("attempts", [])

        # Crear o actualizar el intento del usuario
        user_attempt, created = UserGameAttempt.objects.update_or_create(
            user=request.user,
            daily_game=daily_game,
            defaults={
                "success": success,
                "attempts_used": attempts_used,
                "completed_at": timezone.now() if success else None,
                "attempts_data": attempts_data,  # Guardar todos los detalles
            },
        )

        # Actualizar estadísticas del perfil solo si es un nuevo intento exitoso
        # y es el juego de hoy (no histórico)
        today = timezone.now().date()
        if success and created and daily_game.date == today:
            profile = request.user.profile
            profile.games_won += 1
            if attempts_used == 1:
                profile.guessed_it += 1

            # Actualizar racha
            profile.current_streak = calculate_user_streak(request.user)
            if profile.current_streak > profile.max_streak:
                profile.max_streak = profile.current_streak

            profile.save()

        print(
            f"Intento guardado para {request.user.username}: {success} en {attempts_used} intentos"
        )
        print(f"Detalles de intentos: {attempts_data}")

    except Exception as e:
        print(f"Error guardando intento del usuario: {e}")


def save_historical_user_attempt(request, daily_game, success, attempts_used):
    """Guardar intento del usuario para juegos históricos con detalles completos"""
    try:
        # Obtener los detalles de los intentos desde la sesión
        game_state = request.session.get("game_state", {})
        attempts_data = game_state.get("attempts", [])

        # Crear o actualizar el intento del usuario
        user_attempt, created = UserGameAttempt.objects.update_or_create(
            user=request.user,
            daily_game=daily_game,
            defaults={
                "success": success,
                "attempts_used": attempts_used,
                "completed_at": timezone.now() if success else None,
                "attempts_data": attempts_data,  # Guardar todos los detalles
            },
        )

        # Para juegos históricos, no actualizamos estadísticas de perfil
        print(
            f"Intento histórico guardado para {request.user.username}: {success} en {attempts_used} intentos"
        )
        print(f"Detalles de intentos: {attempts_data}")

    except Exception as e:
        print(f"Error guardando intento histórico del usuario: {e}")


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


def is_similar_franchise(correct_franchise, guessed_franchise):
    """Verificar si dos franquicias son similares usando palabras clave"""
    if not correct_franchise or not guessed_franchise:
        return False

    # Normalizar y dividir en palabras
    correct_words = re.findall(r"\w+", correct_franchise.lower())
    guessed_words = re.findall(r"\w+", guessed_franchise.lower())

    # Palabras clave de franquicias comunes
    franchise_words = set(correct_words + guessed_words)

    # Verificar coincidencias de palabras importantes
    correct_lower = correct_franchise.lower()
    guessed_lower = guessed_franchise.lower()

    for franchise in franchise_words:
        if franchise.lower() in correct_lower and franchise.lower() in guessed_lower:
            return True

    return False


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
            context["screenshots"] = game.screenshot_set.all().order_by("difficulty")
        else:
            context["error"] = "No se pudo obtener juego"

        return context


class TestIGDBView(TemplateView):
    """Vista de prueba IGDB"""

    template_name = "test_random_game.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        igdb_service = IGDBService()
        game = igdb_service.select_random_game()

        if game:
            context["game"] = game
            context["screenshots"] = game.screenshot_set.all().order_by("difficulty")
        else:
            context["error"] = "No se pudo obtener juego con IGDB"

        return context


class CompareServicesView(TemplateView):
    """Vista para comparar ambos servicios"""

    template_name = "compare_services.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        rawg_service = RAWGService()
        igdb_service = IGDBService()

        rawg_game = rawg_service.select_random_game()
        igdb_game = igdb_service.select_random_game()

        context.update(
            {
                "rawg_game": rawg_game,
                "igdb_game": igdb_game,
                "rawg_screenshots": (
                    rawg_game.screenshot_set.all().order_by("difficulty")
                    if rawg_game
                    else []
                ),
                "igdb_screenshots": (
                    igdb_game.screenshot_set.all().order_by("difficulty")
                    if igdb_game
                    else []
                ),
            }
        )

        return context


class DebugFranchiseView(TemplateView):
    """Vista para debuggear franquicias"""

    template_name = "debug_franchise.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener juegos con franquicia para debugging
        games_with_franchise = Game.objects.filter(
            franchise_name__isnull=False
        ).exclude(franchise_name="")[:10]

        context["games"] = games_with_franchise
        return context


class DebugIGDBAuthView(View):
    """Vista para debuggear autenticación IGDB"""

    def get(self, request, *args, **kwargs):
        igdb_service = IGDBService()
        auth_status = igdb_service.test_authentication()

        return JsonResponse(
            {
                "authenticated": auth_status["authenticated"],
                "token_expires": auth_status.get("token_expires"),
                "error": auth_status.get("error"),
            }
        )


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

# Vistas de autenticación
register = CustomRegisterView.as_view()
registration_complete = RegistrationCompleteView.as_view()
confirm_email = ConfirmEmailView.as_view()
resend_confirmation = ResendConfirmationView.as_view()
login_view = CustomLoginView.as_view()

# Vistas de testing
generate_test_game = GenerateTestGameView.as_view()
generate_test_game_igdb = GenerateTestGameIGDBView.as_view()
test_rawg_view = TestRAWGView.as_view()
test_igdb_view = TestIGDBView.as_view()
compare_services_view = CompareServicesView.as_view()
debug_franchise = DebugFranchiseView.as_view()
debug_igdb_auth = DebugIGDBAuthView.as_view()
