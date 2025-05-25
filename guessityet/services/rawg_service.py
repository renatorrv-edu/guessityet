import requests
import random
import os
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO
import uuid
from guessityet.models import Game, Screenshot
import tempfile
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from moviepy.editor import VideoFileClip


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
            "page_size": page_size,
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
        endpoint = f"{self.BASE_URL}/games/{rawg_id}/screenshots"
        params = {"key": self.api_key}
        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            return response.json().get("results", [])

        return []

    def get_game_videos(self, rawg_id):
        endpoint = f"{self.BASE_URL}/games/{rawg_id}/movies"
        params = {"key": self.api_key}
        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            return response.json().get("results", [])

        return []

    def download_and_convert_video_to_gif(self, video_url, game_id):
        """
        Descarga un vídeo, extrae 5 segundos del medio y lo convierte a GIF
        Optimizado para MoviePy 1.0.3
        """

        temp_video_path = None
        temp_gif_path = None
        video_clip = None

        try:
            # Crear archivo temporal para el vídeo
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                temp_video_path = temp_video.name

                # Descargar el vídeo con timeout más largo
                print(f"Descargando vídeo desde: {video_url}")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(
                    video_url, stream=True, timeout=120, headers=headers
                )
                response.raise_for_status()

                # Guardar vídeo temporalmente con límite más alto
                total_size = 0
                max_size = 300 * 1024 * 1024  # 300MB límite
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_video.write(chunk)
                        total_size += len(chunk)
                        # Mostrar progreso cada 10MB
                        if total_size % (10 * 1024 * 1024) == 0:
                            print(f"Descargado: {total_size / (1024*1024):.1f} MB...")
                        # Limitar tamaño máximo del vídeo
                        if total_size > max_size:
                            print(
                                f"Vídeo demasiado grande ({total_size / (1024*1024):.1f} MB), abortando descarga"
                            )
                            return None

            print(f"Vídeo descargado: {total_size / (1024*1024):.1f} MB")

            # Crear archivo temporal para el GIF
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_gif:
                temp_gif_path = temp_gif.name

            # Procesar con moviepy
            video_clip = VideoFileClip(temp_video_path)
            duration = video_clip.duration

            print(f"Duración del vídeo: {duration:.2f} segundos")

            # Calcular el segmento de 5 segundos del medio
            if duration < 5:
                # Si el vídeo es menor a 5 segundos, usar todo
                start_time = 0
                end_time = duration
                print("Vídeo menor a 5 segundos, usando completo")
            else:
                # Extraer 5 segundos del medio
                middle = duration / 2
                start_time = max(0, middle - 2.5)
                end_time = min(duration, start_time + 5)
                print(f"Extrayendo desde {start_time:.1f}s hasta {end_time:.1f}s")

            # Crear el clip de 5 segundos
            clip = video_clip.subclip(start_time, end_time)

            # Redimensionar para optimizar el GIF
            # Mantener proporciones pero limitar ancho máximo
            if clip.w > 600:
                clip = clip.resize(width=600)
            elif clip.w < 300:
                clip = clip.resize(width=300)

            print(f"Dimensiones del GIF: {clip.w}x{clip.h}")

            # Convertir a GIF con configuración optimizada para MoviePy 1.0.3
            clip.write_gif(
                temp_gif_path,
                fps=15,  # FPS óptimo para balance tamaño/calidad
                program="imageio",  # Usar imageio como backend
                opt="nq",  # Sin optimización de cuantización (más rápido)
                verbose=False,
                logger=None,
            )

            # Cerrar clips para liberar memoria
            clip.close()
            video_clip.close()

            # Verificar que el GIF se creó correctamente
            if not os.path.exists(temp_gif_path) or os.path.getsize(temp_gif_path) == 0:
                print("Error: GIF no se generó correctamente")
                return None

            gif_size_mb = os.path.getsize(temp_gif_path) / (1024 * 1024)
            print(f"GIF generado: {gif_size_mb:.1f} MB")

            # Leer el GIF generado
            with open(temp_gif_path, "rb") as gif_file:
                gif_content = gif_file.read()

            # Generar nombre único para el archivo
            gif_filename = f"game_gifs/game_{game_id}_{uuid.uuid4().hex[:8]}.gif"

            # Guardar usando Django's storage system
            gif_path = default_storage.save(gif_filename, ContentFile(gif_content))

            print(f"GIF guardado en: {gif_path}")
            return gif_path

        except requests.RequestException as e:
            print(f"Error descargando vídeo: {e}")
            return None
        except Exception as e:
            print(f"Error procesando vídeo: {str(e)}")
            return None

        finally:
            # Limpiar recursos
            if video_clip:
                try:
                    video_clip.close()
                except:
                    pass

            # Limpiar archivos temporales
            for temp_path in [temp_video_path, temp_gif_path]:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

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
        """Procesar el juego seleccionado. Obtener detalles, screenshots, vídeo y GIF"""

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

        # Procesar vídeo y crear GIF
        if video_url:
            print("Procesando vídeo para crear GIF...")
            gif_path = self.download_and_convert_video_to_gif(video_url, game.id)
            if gif_path:
                game.gif_path = gif_path
                game.save(update_fields=["gif_path"])
                print(f"✅ GIF creado exitosamente para: {game.title}")
            else:
                print(f"❌ No se pudo crear GIF para: {game.title}")

        Screenshot.objects.filter(game=game).delete()

        for i, screenshot in enumerate(selected_screenshots, 1):
            Screenshot.objects.create(
                game=game, image_url=screenshot["image"], difficulty=i
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
