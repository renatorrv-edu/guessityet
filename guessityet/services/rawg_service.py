import requests
import random
import os
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from guessityet.models import Game, Screenshot, DailyGame  # TODO: *?


class RAWGService:
    BASE_URL = "https://api.rawg.io/api"

    def __init__(self):
        self.api_key = settings.RAWG_API_KEY

    def search_games(self, query, page_size=10):
        """Buscar juegos por nombre para autocompletado de input"""

        endpoint = f"{self.BASE_URL}/games"
        params = {
            "key": self.api_key,
            "search": query,
            page_size: page_size,
        }

        response = requests.get(endpoint, params=params)
        return response.json()

    def get_game_details(self, rawg_id):
        """Obtener detalles del juego seleccionado por ID"""

        endpoint = f"{self.BASE_URL}/games/{rawg_id}"
        params = {"key": self.api_key}

        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            return response.json()

        return None

    def get_game_screenshots(self, rawg_id):
        """Obtener capturas de pantalla del juego seleccionado por ID"""

        endpoint = f"{self.BASE_URL}/games/{rawg_id}/screenshots"
        params = {"key": self.api_key}

        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            return response.json()

        return []

    def get_game_videos(self, rawg_id):
        """Obtener vídeo del juego seleccionado por ID. Última pista"""

        endpoint = f"{self.BASE_URL}/games/{rawg_id}/movies"
        params = {"key": self.api_key}

        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            return response.json()

        return []

    def select_random_game(self):
        """Seleccionar juego aleatorio que no haya sido utilizado anteriormente"""

        endpoint = f"{self.BASE_URL}/games"

        # Obtener IDs de juegos ya utilizados anteriormente
        used_games_ids = set(
            Game.objects.filter(used_date__isnull=False).values_list(
                "rawg_id", flat=True
            )
        )

        for _ in range(5):
            # Generamos un rango de fechas aleatorio para elegir juegos.
            start_year = random.randint(1980, 2020)
            end_year = start_year + random.randint(3, 7)

            params = {
                "key": self.api_key,
                "page_size": 100,
                "page": random.randint(1, 10),
                "metacritic": "40,100",  # Elegimos solo juegos que tengan una media entre 40 y 100
                "dates": f"{start_year}-01-01,{end_year}-12-31",
            }

            response = requests.get(endpoint, params=params)

            if response.status_code == 200:
                games = response.json().get("results", [])
                available_games = [g for g in games if g["id"] not in used_games_ids]

                for game_data in available_games:
                    rawg_id = game_data["id"]

                    # Comprobamos que tenga al menos 5 capturas de pantalla
                    screenshots = self.get_game_screenshots(rawg_id)
                    if not screenshots or len(screenshots) < 5:
                        continue

                    # Comprobamos que tenga también un vídeo disponible
                    videos = self.get_game_videos(rawg_id)
                    if not videos:
                        continue

                    # Si se cumplen los requisitos, procesamos el juego
                    return self.process_selected_game(rawg_id)

        return None

    def process_selected_game(self, rawg_id):
        """Procesar el juego seleccionado. Obtener detalles, screenshots y vídeo"""

        game_details = self.get_game_details(rawg_id)

        if not game_details:
            return None

        # Vídeo
        videos = self.get_game_videos(rawg_id)

        if not videos:
            return None

        video_url = videos[0].get("data", {}).get("max", "")

        # Capturas de pantalla
        screenshots = self.get_game_screenshots(rawg_id)

        if not screenshots:
            return None

        selected_screenshots = random.sample(screenshots, 5)

        # Registrar juego en la base de datos
        game, created = Game.objects.update_or_create(
            rawg_id=game_details["id"],
            defaults={
                "title": game_details["name"],
                "developer": self.get_developer_name(game_details),
                "release_year": self.get_release_year(game_details.get("released")),
                "genres": self.format_genres(game_details.get("genres", [])),
                "platforms": self.format_platforms(game_details.get("platforms", [])),
                "metacritic": game_details.get("metacritic"),
                "video_url": video_url,
            },
        )

        Screenshot.objects.filter(game=game).delete()

        for i, screenshot in enumerate(selected_screenshots, 1):
            Screenshot.objects.create(
                game=game, image_url=screenshot["image"], difficulty_level=i
            )

        return game

    def get_release_year(self, date_str):
        """Extraer el año de lanzamiento del juego"""

        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").year
        except ValueError:
            return None

    def get_developer_name(self, game_details):
        """Obtener el nombre del desarrollador"""

        developers = game_details.get("developers")
        # Ternario
        return developers[0]["name"] if developers else None

    def format_genres(self, genres):
        """Formatea la lista de géneros como una cadena"""

        return ", ".join([g["name"] for g in genres])

    def format_platforms(self, platforms):
        """Formatea la lista de plataformas como una cadena"""

        return ", ".join([p["platform"]["name"] for p in platforms])
