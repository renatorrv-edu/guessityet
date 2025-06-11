# guessityet/urls.py - URLs completas con autenticación
from django.urls import path
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
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
    path("", views.DailyGameView.as_view(), name="daily_game"),
    path("historial/", views.GameHistoryView.as_view(), name="game_history"),
    path("historial/<str:date>/", views.GameDetailView.as_view(), name="game_detail"),
    path("juego-aleatorio/", views.RandomGameView.as_view(), name="random_game"),
    # ============================================================================
    # URLS DE AUTENTICACIÓN Y CONFIRMACIÓN DE EMAIL
    # ============================================================================
    path("cuentas/registrarse/", views.CustomRegisterView.as_view(), name="register"),
    path(
        "cuentas/registro/completo/",
        views.RegistrationCompleteView.as_view(),
        name="registration_complete",
    ),
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
    path("cuentas/login/", views.CustomLoginView.as_view(), name="login"),
    path(
        "cuentas/logout/",
        LogoutView.as_view(
            next_page="guessityet:daily_game",
            template_name="registration/logged_out.html",
        ),
        name="logout",
    ),
    # ============================================================================
    # URLS DE RESET DE CONTRASEÑA
    # ============================================================================
    path(
        "cuentas/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html"
        ),
        name="password_reset",
    ),
    path(
        "cuentas/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "cuentas/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "cuentas/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "cuentas/password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html"
        ),
        name="password_change",
    ),
    path(
        "cuentas/password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # ============================================================================
    # URLS DE PERFIL DE USUARIO
    # ============================================================================
    path("perfil/", views.ProfileView.as_view(), name="profile"),
    path(
        "perfil/actualizar/", views.UpdateProfileView.as_view(), name="update_profile"
    ),
    # ============================================================================
    # URLS DE PÁGINAS INFORMATIVAS
    # ============================================================================
    path("como-jugar/", views.HowToPlayView.as_view(), name="how_to_play"),
    path("acerca-de/", views.AboutView.as_view(), name="about"),
    # ============================================================================
    # URLS AJAX PARA FUNCIONALIDAD DEL JUEGO
    # ============================================================================
    path("search-games/", views.search_games_ajax, name="search_games_ajax"),
    path("submit-guess/", views.submit_guess, name="submit_guess"),
    path("skip-turn/", views.skip_turn, name="skip_turn"),
    # ============================================================================
    # URLS DE TESTING Y DEBUG (solo en desarrollo)
    # ============================================================================
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
    # TODO: Borrar cuando se termine
    path("test-email-direct/", views.test_email_direct, name="test_email_direct"),
]
