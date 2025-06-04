from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from guessityet import views

urlpatterns = [
    path("", views.daily_game, name="daily_game"),
    path("search-games/", views.search_games_ajax, name="search_games_ajax"),
    path("submit-guess/", views.submit_guess, name="submit_guess"),
    path("skip-turn/", views.skip_turn, name="skip_turn"),
    path("new-test-game/", views.generate_test_game, name="generate_test_game"),
    path(
        "new-test-game-igdb/",
        views.generate_test_game_igdb,
        name="generate_test_game_igdb",
    ),
    path("debug-franchise/", views.debug_franchise, name="debug_franchise"),
    path("debug-igdb-auth/", views.debug_igdb_auth, name="debug_igdb_auth"),
    path("test-game/", views.test_rawg_view, name="test_rawg_view"),
    path("test-game-igdb/", views.test_igdb_view, name="test_igdb_view"),
    path("compare-services/", views.compare_services_view, name="compare_services"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
]
