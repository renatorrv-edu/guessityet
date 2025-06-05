# guessityet/urls.py - URLs de la aplicación
from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from guessityet import views

app_name = "guessityet"

urlpatterns = [
    # Página principal - Juego diario
    path("", views.DailyGameView.as_view(), name="daily_game"),
    # Registro personalizado (las demás auth están en config/urls.py)
    path("cuentas/registrarse/", views.CustomRegisterView.as_view(), name="register"),
    # Historial de juegos
    path("historial/", views.GameHistoryView.as_view(), name="game_history"),
    path("historial/<str:date>/", views.GameDetailView.as_view(), name="game_detail"),
    # Páginas informativas
    path("como-jugar/", views.HowToPlayView.as_view(), name="how_to_play"),
    path("acerca-de/", views.AboutView.as_view(), name="about"),
    # Perfil de usuario
    path("perfil/", views.ProfileView.as_view(), name="profile"),
    path(
        "perfil/actualizar/", views.UpdateProfileView.as_view(), name="update_profile"
    ),
    # Funcionalidades AJAX del juego
    path("search-games/", views.search_games_ajax, name="search_games_ajax"),
    path("submit-guess/", views.submit_guess, name="submit_guess"),
    path("skip-turn/", views.skip_turn, name="skip_turn"),
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
1
