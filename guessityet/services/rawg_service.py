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

# Parche para compatibilidad con Pillow >= 10.0.0
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS


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

    def get_game_screenshots(self, rawg_id, max_screenshots=20):
        """
        Obtener capturas de pantalla del juego seleccionado por ID
        NOTA: Hay una pequeña discrepancia con las capturas que tiene almacenadas la API de RAWG.io y
        las que muestra públicamente. Parece ser una limitación conocida: aunque haya más imágenes disponibles
        solo se puede acceder a seis de ellas. Mi objetivo inicial era trabajar con un mayor volumen de imágenes.
        """

        print(f"Obteniendo capturas para juego {rawg_id}...")

        endpoint = f"{self.BASE_URL}/games/{rawg_id}/screenshots"
        params = {"key": self.api_key, "page_size": 10}

        try:
            response = requests.get(endpoint, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                screenshots = data.get("results", [])
                api_total = data.get("count", 0)

                print(f"Capturas obtenidas: {len(screenshots)}")
                print(f"Total según API: {api_total}")

                # Mostrar la discrepancia si existe
                if api_total > len(screenshots):
                    print(
                        f"Limitación API: {api_total - len(screenshots)} capturas no accesibles"
                    )

                return screenshots

            else:
                print(f"Error obteniendo capturas: Status {response.status_code}")
                return []

        except Exception as e:
            print(f"Error en petición de capturas: {e}")
            return []

    def get_game_videos(self, rawg_id):
        endpoint = f"{self.BASE_URL}/games/{rawg_id}/movies"
        params = {"key": self.api_key}
        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            return response.json().get("results", [])

        return []

    def check_video_size(self, video_url, max_size_mb=200):
        """
        Verificar el tamaño de un vídeo sin descargarlo
        Retorna True si es procesable, False si es demasiado grande
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.head(video_url, headers=headers, timeout=10)
            if response.status_code == 200:
                content_length = response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    print(f"Tamaño del vídeo: {size_mb:.1f} MB")
                    return size_mb <= max_size_mb

            # Si no podemos obtener el tamaño, intentamos procesarlo
            return True

        except Exception as e:
            print(f"Error verificando tamaño del vídeo: {e}")
            return True  # En caso de duda, intentamos procesarlo

    def download_and_convert_video_to_gif(self, video_url, game_id):
        """
        Descarga un vídeo, extrae 5 segundos del medio y lo convierte a GIF
        Optimizado para MoviePy 1.0.3 con streaming inteligente
        """
        temp_video_path = None
        temp_gif_path = None
        video_clip = None

        try:
            # Intentar obtener info del vídeo sin descargarlo completo
            print(f"Verificando vídeo desde: {video_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Hacer una petición HEAD para obtener el tamaño
            head_response = requests.head(video_url, headers=headers, timeout=30)
            if head_response.status_code == 200:
                content_length = head_response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    print(f"Tamaño del vídeo: {size_mb:.1f} MB")

                    if size_mb > 500:  # Más de 500MB
                        print("Vídeo demasiado grande para procesar")
                        return None

            # Crear archivo temporal para el vídeo
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                temp_video_path = temp_video.name

                # Descargar el vídeo con límite más inteligente
                print(f"Descargando vídeo...")
                response = requests.get(
                    video_url, stream=True, timeout=120, headers=headers
                )
                response.raise_for_status()

                # Guardar vídeo temporalmente con límite más alto
                total_size = 0
                max_size = 300 * 1024 * 1024  # 300MB límite
                for chunk in response.iter_content(
                    chunk_size=32768
                ):  # Chunks más grandes
                    if chunk:
                        temp_video.write(chunk)
                        total_size += len(chunk)
                        # Mostrar progreso cada 50MB
                        if total_size % (50 * 1024 * 1024) < 32768:
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

            # Procesar con moviepy - cargar solo los metadatos primero
            print("Analizando vídeo...")
            video_clip = VideoFileClip(temp_video_path)
            duration = video_clip.duration

            print(f"Duración del vídeo: {duration:.2f} segundos")

            # Si el vídeo es muy largo, ser más selectivo
            if duration > 300:  # Más de 5 minutos
                print("Vídeo muy largo, usando segmento más específico")
                # Para vídeos largos, usar un segmento más hacia el inicio
                start_time = min(30, duration * 0.2)  # 30 segundos o 20% del vídeo
                end_time = min(start_time + 10, duration)  # ← CAMBIADO: 10 segundos
            elif duration < 10:  # ← CAMBIADO: Si es menor a 10 segundos
                # Si el vídeo es menor a 10 segundos, usar todo
                start_time = 0
                end_time = duration
                print("Vídeo menor a 10 segundos, usando completo")
            else:
                # Extraer 10 segundos del medio
                middle = duration / 2
                start_time = max(0, middle - 5)
                end_time = min(duration, start_time + 10)

            print(f"Extrayendo desde {start_time:.1f}s hasta {end_time:.1f}s")

            # Crear el clip de 10 segundos
            clip = video_clip.subclip(start_time, end_time)

            # Redimensionar para optimizar el GIF
            original_width = clip.w
            original_height = clip.h
            print(f"Dimensiones originales: {original_width}x{original_height}")

            # Redimensionar más agresivamente para vídeos grandes
            if original_width > 800:
                new_width = 400  # Más pequeño para vídeos grandes
            elif original_width > 600:
                new_width = 500
            elif original_width < 300:
                new_width = 300
            else:
                new_width = 600

            clip_resized = clip.resize(width=new_width)
            print(f"Redimensionado a: {clip_resized.w}x{clip_resized.h}")

            # Convertir a GIF de forma simple y compatible con MoviePy 1.0.3
            print("Convirtiendo a GIF...")
            try:
                # Configuración optimizada para MoviePy 1.0.3
                clip_resized.write_gif(
                    temp_gif_path,
                    fps=20,
                    program="imageio",
                    verbose=False,
                )
                print("✓ GIF convertido exitosamente")
            except Exception as e:
                print(f"Error en conversión a GIF: {e}")
                # Segundo intento con configuración aún más básica
                try:
                    print("Intentando conversión básica...")
                    clip_resized.write_gif(temp_gif_path, fps=20)
                    print("✓ GIF convertido con configuración básica")
                except Exception as e2:
                    print(f"Error en segundo intento: {e2}")
                    return None

            # Cerrar clips para liberar memoria
            clip.close()
            clip_resized.close()
            video_clip.close()

            # Verificar que el GIF se creó correctamente
            if not os.path.exists(temp_gif_path) or os.path.getsize(temp_gif_path) == 0:
                print("Error: GIF no se generó correctamente")
                return None

            gif_size_mb = os.path.getsize(temp_gif_path) / (1024 * 1024)
            print(f"GIF generado: {gif_size_mb:.1f} MB")

            # Si el GIF es muy grande, rechazarlo
            if gif_size_mb > 50:  # Más de 50MB
                print("GIF resultante demasiado grande")
                return None

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
        """Seleccionar juego aleatorio con verificación optimizada"""

        endpoint = f"{self.BASE_URL}/games"
        used_games_ids = set(
            Game.objects.filter(used_date__isnull=False).values_list(
                "rawg_id", flat=True
            )
        )

        for _ in range(5):
            start_year = random.randint(1980, 2020)
            end_year = start_year + random.randint(3, 7)

            params = {
                "key": self.api_key,
                "page_size": 100,
                "page": random.randint(1, 10),
                "metacritic": "40,100",
                "dates": f"{start_year}-01-01,{end_year}-12-31",
            }

            response = requests.get(endpoint, params=params)

            if response.status_code == 200:
                games = response.json().get("results", [])
                available_games = [g for g in games if g["id"] not in used_games_ids]

                # Barajar para probar en orden aleatorio
                random.shuffle(available_games)

                for game_data in available_games[:10]:  # Solo probar primeros 10
                    rawg_id = game_data["id"]

                    print(f"Verificando juego: {game_data.get('name')} (ID: {rawg_id})")

                    # Verificación rápida: obtener detalles (1 llamada que nos da todo)
                    game_details = self.get_game_details(rawg_id)
                    if not game_details:
                        continue

                    screenshots_count = game_details.get("screenshots_count", 0)

                    if screenshots_count < 5:
                        print(f"  Descartado: solo {screenshots_count} capturas")
                        continue

                    # Verificar vídeos
                    videos = self.get_game_videos(rawg_id)
                    if not videos:
                        print(f"  Descartado: sin vídeos")
                        continue

                    print(
                        f"  Seleccionado: {screenshots_count} capturas, {len(videos)} vídeos"
                    )
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

        # Capturas de pantalla - Obtener hasta 20 para mejor análisis (solo llamar una vez)
        screenshots = self.get_game_screenshots(rawg_id, max_screenshots=20)
        print(f"🔍 Obtenidas {len(screenshots)} capturas de RAWG API")

        if not screenshots:
            return None

        # Limitar a máximo 10 capturas para análisis (seleccionará las mejores 5)
        screenshots_to_analyze = screenshots[:10]
        print(
            f"📸 Total capturas obtenidas: {len(screenshots)}, analizando: {len(screenshots_to_analyze)}"
        )

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

        # Procesar vídeo y crear GIF con verificación de tamaño
        if video_url:
            # Verificar si el vídeo es procesable
            if self.check_video_size(video_url):
                print("Procesando vídeo para crear GIF...")
                gif_path = self.download_and_convert_video_to_gif(video_url, game.id)
                if gif_path:
                    game.gif_path = gif_path
                    game.save(update_fields=["gif_path"])
                    print(f"✅ GIF creado exitosamente para: {game.title}")
                else:
                    print(f"❌ No se pudo crear GIF para: {game.title}")
            else:
                print(f"⚠️ Vídeo demasiado grande para {game.title}, saltando GIF")

        # Limpiar capturas anteriores
        Screenshot.objects.filter(game=game).delete()

        # Guardar TODAS las capturas para análisis (hasta 10)
        temp_screenshots = []
        for i, screenshot in enumerate(screenshots_to_analyze, 1):
            screenshot_obj = Screenshot.objects.create(
                game=game,
                image_url=screenshot["image"],
                difficulty=i,  # Temporal, se actualizará con el análisis de IA
            )
            temp_screenshots.append(screenshot_obj)

        print(f"📸 Guardadas {len(temp_screenshots)} capturas para análisis")

        # Importar y usar el servicio de análisis de imágenes
        try:
            from guessityet.services.image_analysis_service import GameDifficultyService

            print(
                f"🔍 Analizando {len(temp_screenshots)} capturas de {game.title} con IA..."
            )
            difficulty_service = GameDifficultyService()

            # Procesar capturas con IA para seleccionar las 5 mejores y organizarlas
            success = difficulty_service.select_and_organize_best_screenshots(
                game, max_screenshots=5
            )

            if success:
                print(
                    f"✅ Las 5 mejores capturas seleccionadas y organizadas para: {game.title}"
                )
            else:
                print(
                    f"⚠️ Error seleccionando capturas para: {game.title}, usando selección aleatoria"
                )
                self._fallback_random_selection(game, screenshots_to_analyze)

        except ImportError:
            print(
                "⚠️ Servicio de análisis de imágenes no disponible, usando capturas aleatorias"
            )
            self._fallback_random_selection(game, screenshots_to_analyze)

        return game

    def _fallback_random_selection(self, game, screenshots_data):
        """Método de respaldo: seleccionar 5 capturas aleatorias"""

        selected_screenshots = random.sample(
            screenshots_data, min(5, len(screenshots_data))
        )

        # Limpiar y recrear con selección aleatoria
        Screenshot.objects.filter(game=game).delete()
        for i, screenshot in enumerate(selected_screenshots, 1):
            Screenshot.objects.create(
                game=game, image_url=screenshot["image"], difficulty=i
            )

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
