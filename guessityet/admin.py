from django.contrib import admin
from .models import *


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "developer", "release_year", "metacritic", "used_date")
    search_fields = ("title", "developer", "genres", "platforms")
    list_filter = ("release_year", "genres")


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ("game", "difficulty", "image_url", "local_path")
    list_filter = ("difficulty",)
    search_fields = ("game__title",)


@admin.register(DailyGame)
class DailyGameAdmin(admin.ModelAdmin):
    list_display = ("game", "date")
    list_filter = ("date",)
    search_fields = ("game__title",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "current_streak",
        "max_streak",
        "games_won",
        "mult_games_won",
        "guessed_it",
    )


@admin.register(UserGameAttempt)
class UserGameAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "daily_game",
        "attempts_used",
        "success",
        "completed_at",
        "session_id",
    )
    list_filter = ("success", "completed_at")
    search_fields = ("user__username", "daily_game__game__title", "session_id")


@admin.register(GameLobby)
class GameLobbyAdmin(admin.ModelAdmin):
    list_display = ("code", "creator", "created_at", "is_active", "max_players")
    list_filter = ("is_active", "created_at")
    search_fields = ("code", "creator__username")


@admin.register(LobbyPlayer)
class LobbyPlayerAdmin(admin.ModelAdmin):
    list_display = ("lobby", "user", "nickname", "score", "joined_at", "session_id")
    list_filter = ("joined_at",)
    search_fields = ("user__username", "nickname", "session_id")
