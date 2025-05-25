from django.urls import path

from guessityet import views

urlpatterns = [
    path("test-game/", views.test_rawg_view, name="test_rawg_view"),
]
