# guessityet/urls.py - URLs de la aplicación con autenticación y confirmación
from django.urls import path
from django.contrib.auth.views import LogoutView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from guessityet import views

app_name = "guessityet"

urlpatterns = [
    # ============================================================================
    # URLS PRINCIPALES DEL JUEGO
    # ============================================================================
    # Página principal - Juego diario
    path("", views.DailyGameView.as_view(), name="daily_game"),
    # Historial de juegos
    path("historial/", views.GameHistoryView.as_view(), name="game_history"),
    path("historial/<str:date>/", views.GameDetailView.as_view(), name="game_detail"),
    # Juego aleatorio
    path("juego-aleatorio/", views.RandomGameView.as_view(), name="random_game"),
    # ============================================================================
    # URLS DE AUTENTICACIÓN Y CONFIRMACIÓN DE EMAIL
    # ============================================================================
    # Registro personalizado con confirmación por email
    path("cuentas/registrarse/", views.CustomRegisterView.as_view(), name="register"),
    path(
        "cuentas/registro/completo/",
        views.RegistrationCompleteView.as_view(),
        name="registration_complete",
    ),
    # Login y logout (las demás auth están en config/urls.py)
    path("cuentas/login/", views.CustomLoginView.as_view(), name="login"),
    path(
        "cuentas/logout/",
        LogoutView.as_view(next_page="guessityet:daily_game"),
        name="logout",
    ),
    # Confirmación de email
    path(
        "cuentas/confirmar/<uuid:token>/",
        views.ConfirmEmailView.as_view(),
        name="confirm_email",
    ),
    path(
        "cuentas/reenviar-confirmacion/",
        views.ResendConfirmationView.as_view(),
        name="resend_confirmation",
    ),
    # ============================================================================
    # URLS DE PERFIL DE USUARIO
    # ============================================================================
    # Perfil de usuario
    path("perfil/", views.ProfileView.as_view(), name="profile"),
    path(
        "perfil/actualizar/", views.UpdateProfileView.as_view(), name="update_profile"
    ),
    # ============================================================================
    # URLS DE PÁGINAS INFORMATIVAS
    # ============================================================================
    # Páginas informativas
    path("como-jugar/", views.HowToPlayView.as_view(), name="how_to_play"),
    path("acerca-de/", views.AboutView.as_view(), name="about"),
    # ============================================================================
    # URLS AJAX PARA FUNCIONALIDAD DEL JUEGO
    # ============================================================================
    # Funcionalidades AJAX del juego
    path("search-games/", views.search_games_ajax, name="search_games_ajax"),
    path("submit-guess/", views.submit_guess, name="submit_guess"),
    path("skip-turn/", views.skip_turn, name="skip_turn"),
    # ============================================================================
    # URLS DE TESTING Y DEBUG (solo en desarrollo)
    # ============================================================================
    # Vistas de desarrollo/testing
    path(
        "nuevo-juego-test/",
        views.GenerateTestGameView.as_view(),
        name="generate_test_game",
    ),
    path(
        "nuevo-juego-igdb/",
        views.GenerateTestGameIGDBView.as_view(),
        name="generate_test_game_igdb",
    ),
    path(
        "debug-franchise/", views.DebugFranchiseView.as_view(), name="debug_franchise"
    ),
    path("debug-igdb-auth/", views.DebugIGDBAuthView.as_view(), name="debug_igdb_auth"),
    path("test-rawg/", views.TestRAWGView.as_view(), name="test_rawg_view"),
    path("test-igdb/", views.TestIGDBView.as_view(), name="test_igdb_view"),
    path(
        "comparar-servicios/",
        views.CompareServicesView.as_view(),
        name="compare_services",
    ),
    # ============================================================================
    # URLS DE DOCUMENTACIÓN API
    # ============================================================================
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="guessityet:schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/",
        SpectacularRedocView.as_view(url_name="guessityet:schema"),
        name="redoc",
    ),
]
