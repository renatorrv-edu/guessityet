from django.shortcuts import render
from guessityet.services.rawg_service import RAWGService


# Test
def test_rawg_view(request):
    service = RAWGService()
    game = service.select_random_game()

    if not game:
        return render(request, "game_not_found.html")

    screenshots = game.screenshot_set.order_by("id")
    video_url = game.video_url

    context = {
        "game": game,
        "screenshots": screenshots,
        "video_url": video_url,
    }

    return render(request, "test_random_game.html", context)
