import requests
import random
import os
from django.conf import settings
from datetime import datetime, timedelta
from django.utils import timezone
from PIL import Image, ImageFilter, ImageEnhance
from io import BytesIO
import uuid
from guessityet.models import Game, Screenshot
import tempfile
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from moviepy.editor import VideoFileClip
import yt_dlp

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS


class IGDBService:
    BASE_URL = "https://api.igdb.com/v4"
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"

    def __init__(self):
        self.client_id = settings.IGDB_CLIENT_ID
        self.client_secret = settings.IGDB_CLIENT_SECRET
        self.access_token = None
        self.token_expires_at = None

    def get_access_token(self):
        """Obtener token de acceso OAuth de Twitch para IGDB"""

        if (
            self.access_token
            and self.token_expires_at
            and datetime.now() < self.token_expires_at
        ):
            return self.access_token

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        response = requests.post(self.TOKEN_URL, data=data)

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
            return self.access_token
        else:
            print(f"Error obteniendo token: {response.status_code}")
            return None

    def make_request(self, endpoint, query):
        """Realizar petición a IGDB con autenticación"""

        token = self.get_access_token()
        if not token:
            print("Error: No se pudo obtener token de acceso")
            return None

        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = f"{self.BASE_URL}/{endpoint}"

        print(f"Making request to: {url}")
        print(f"Query: {query.strip()}")

        response = requests.post(url, headers=headers, data=query)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error en petición IGDB: {response.status_code}")
            print(f"Response text: {response.text}")
            return None

    def search_games(self, query_text, limit=25):
        """Buscar juegos por nombre - aumentado para más resultados"""

        # Búsqueda principal
        query = f"""
        search "{query_text}";
        fields name, cover.url, first_release_date, genres.name, platforms.name;
        limit {limit};
        """

        results = self.make_request("games", query)

        if not results:
            return []

        if len(results) < 10 and len(query_text) > 3:
            alt_query = f"""
            search "{query_text}*";
            fields name, cover.url, first_release_date, genres.name, platforms.name;
            limit {limit - len(results)};
            """

            alt_results = self.make_request("games", alt_query)
            if alt_results:
                # Combinar resultados evitando duplicados
                seen_ids = {game["id"] for game in results}
                for game in alt_results:
                    if game["id"] not in seen_ids:
                        results.append(game)
                        seen_ids.add(game["id"])

        return results[:limit]

    def get_game_details(self, igdb_id):
        """Obtener detalles completos del juego"""

        query = f"""
        fields name, summary, cover.url, first_release_date, 
               genres.name, platforms.name, involved_companies.company.name,
               aggregated_rating, videos.video_id, screenshots.url,
               franchises.name, franchises.slug;
        where id = {igdb_id};
        """

        result = self.make_request("games", query)
        return result[0] if result else None

    def get_game_screenshots(self, igdb_id, max_screenshots=15):
        """Obtener capturas de pantalla del juego - aumentado para mejor selección"""

        query = f"""
        fields url, image_id;
        where game = {igdb_id};
        limit {max_screenshots};
        """

        screenshots = self.make_request("screenshots", query)

        if screenshots:
            formatted_screenshots = []
            for screenshot in screenshots:
                image_url = screenshot["url"].replace("t_thumb", "t_screenshot_big")
                if not image_url.startswith("http"):
                    image_url = f"https:{image_url}"
                formatted_screenshots.append({"image": image_url})

            print(f"Capturas obtenidas: {len(formatted_screenshots)}")
            return formatted_screenshots

        return []

    def get_game_videos(self, igdb_id):
        """Obtener videos del juego desde YouTube"""

        query = f"""
        fields video_id, name;
        where game = {igdb_id};
        """

        videos = self.make_request("game_videos", query)

        if videos:
            formatted_videos = []
            for video in videos:
                video_id = video.get("video_id", "")
                if video_id:
                    # Para mantener compatibilidad con el procesamiento existente
                    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                    formatted_videos.append(
                        {
                            "data": {"max": youtube_url},
                            "name": video.get("name", "Video"),
                        }
                    )

            return formatted_videos

        return []

    def check_video_size(self, video_url, max_size_mb=200, max_duration_minutes=10):
        """
        Verificar el tamaño y duración de un vídeo de YouTube
        """
        if "youtube.com" in video_url or "youtu.be" in video_url:
            try:
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    duration = info.get("duration", 0)
                    duration_minutes = duration / 60

                    print(
                        f"Vídeo de YouTube: {duration} segundos ({duration_minutes:.1f} minutos)"
                    )

                    # Filtrar por duración
                    if duration_minutes > max_duration_minutes:
                        print(
                            f"Vídeo demasiado largo ({duration_minutes:.1f} min > {max_duration_minutes} min)"
                        )
                        return False

                    # Filtrar vídeos muy cortos también
                    if duration < 30:
                        print(f"Vídeo demasiado corto ({duration} segundos)")
                        return False

                    print(f"Vídeo aceptable: {duration_minutes:.1f} minutos")
                    return True

            except Exception as e:
                print(f"Error verificando vídeo de YouTube: {e}")
                return False

        # Para otros videos, usar la lógica original
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

            return True

        except Exception as e:
            print(f"Error verificando tamaño del vídeo: {e}")
            return True

    def download_and_convert_video_to_gif(self, video_url, game_id):
        """
        Descarga un vídeo de YouTube y lo convierte a GIF
        """
        temp_video_path = None
        temp_gif_path = None
        video_clip = None

        try:
            if "youtube.com" in video_url or "youtu.be" in video_url:
                return self._process_youtube_video(video_url, game_id)
            else:
                # Para otros videos, usar la lógica original de RAWG
                return self._process_direct_video(video_url, game_id)

        except Exception as e:
            print(f"Error procesando vídeo: {str(e)}")
            return None

    def _process_youtube_video(self, video_url, game_id):
        """
        Procesar vídeo de YouTube específicamente
        """
        temp_video_path = None
        temp_gif_path = None
        video_clip = None

        try:
            print(f"Procesando vídeo de YouTube: {video_url}")

            # Verificar que yt-dlp esté disponible
            try:
                import yt_dlp

                print("yt-dlp importado correctamente")
            except ImportError:
                print("ERROR: yt-dlp no está instalado. Ejecuta: pip install yt-dlp")
                return None

            # Crear archivo temporal para el vídeo con nombre único
            import time

            timestamp = int(time.time())
            temp_video_file = tempfile.NamedTemporaryFile(
                suffix=f"_{timestamp}.mp4", delete=False
            )
            temp_video_path = temp_video_file.name
            temp_video_file.close()

            # Configuración de yt-dlp para descargar calidad media
            ydl_opts = {
                "format": "best[height<=720][ext=mp4]/best[ext=mp4]/best",
                "outtmpl": temp_video_path,
                "quiet": False,
                "no_warnings": False,
                "extractaudio": False,
                "embed_subs": False,
                "writesubtitles": False,
                "overwrites": True,
                "noplaylist": True,
            }

            # Descargar el vídeo
            print("Descargando vídeo de YouTube...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([video_url])
                    print("Descarga completada")
                except Exception as download_error:
                    print(f"Error en descarga: {download_error}")
                    return None

            # Verificar que se descargó
            if (
                not os.path.exists(temp_video_path)
                or os.path.getsize(temp_video_path) == 0
            ):
                print("Error: No se pudo descargar el vídeo")
                print(f"Archivo existe: {os.path.exists(temp_video_path)}")
                if os.path.exists(temp_video_path):
                    print(f"Tamaño archivo: {os.path.getsize(temp_video_path)} bytes")
                return None

            video_size_mb = os.path.getsize(temp_video_path) / (1024 * 1024)
            print(f"Vídeo descargado: {video_size_mb:.1f} MB")

            # Si es demasiado grande, cancelar
            if video_size_mb > 300:
                print("Vídeo demasiado grande después de descarga")
                return None

            # Resto del procesamiento igual...
            # (continúa con el código existente)

            # Si es demasiado grande, cancelar
            if video_size_mb > 300:
                print("Vídeo demasiado grande después de descarga")
                return None

            # Crear archivo temporal para el GIF
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_gif:
                temp_gif_path = temp_gif.name

            # Procesar con moviepy
            print("Analizando vídeo...")
            video_clip = VideoFileClip(temp_video_path)
            duration = video_clip.duration

            print(f"Duración del vídeo: {duration:.2f} segundos")

            # Determinar segmento a extraer
            if duration > 300:  # Más de 5 minutos
                print("Vídeo muy largo, usando segmento específico")
                start_time = min(30, duration * 0.2)
                end_time = min(start_time + 10, duration)
            elif duration < 10:
                start_time = 0
                end_time = duration
                print("Vídeo corto, usando completo")
            else:
                middle = duration / 2
                start_time = max(0, middle - 5)
                end_time = min(duration, start_time + 10)

            print(f"Extrayendo desde {start_time:.1f}s hasta {end_time:.1f}s")

            # Crear clip
            clip = video_clip.subclip(start_time, end_time)

            # Redimensionar
            original_width = clip.w
            original_height = clip.h
            print(f"Dimensiones originales: {original_width}x{original_height}")

            if original_width > 800:
                new_width = 400
            elif original_width > 600:
                new_width = 500
            elif original_width < 300:
                new_width = 300
            else:
                new_width = 600

            clip_resized = clip.resize(width=new_width)
            print(f"Redimensionado a: {clip_resized.w}x{clip_resized.h}")

            # Convertir a GIF
            print("Convirtiendo a GIF...")
            try:
                clip_resized.write_gif(
                    temp_gif_path,
                    fps=25,  # Ligeramente menos FPS para archivos más pequeños
                    program="imageio",
                    verbose=False,
                )
                print("GIF convertido exitosamente")
            except Exception as e:
                print(f"Error en conversión a GIF: {e}")
                try:
                    clip_resized.write_gif(temp_gif_path, fps=25)
                    print("GIF convertido con configuración básica")
                except Exception as e2:
                    print(f"Error en segundo intento: {e2}")
                    return None

            # Cerrar clips
            clip.close()
            clip_resized.close()
            video_clip.close()

            # Verificar GIF
            if not os.path.exists(temp_gif_path) or os.path.getsize(temp_gif_path) == 0:
                print("Error: GIF no se generó correctamente")
                return None

            gif_size_mb = os.path.getsize(temp_gif_path) / (1024 * 1024)
            print(f"GIF generado: {gif_size_mb:.1f} MB")

            if gif_size_mb > 50:
                print("GIF resultante demasiado grande")
                return None

            # Guardar GIF
            with open(temp_gif_path, "rb") as gif_file:
                gif_content = gif_file.read()

            gif_filename = f"game_gifs/game_{game_id}_{uuid.uuid4().hex[:8]}.gif"
            gif_path = default_storage.save(gif_filename, ContentFile(gif_content))

            print(f"GIF guardado en: {gif_path}")
            return gif_path

        except Exception as e:
            print(f"Error procesando vídeo de YouTube: {str(e)}")
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

    def _process_direct_video(self, video_url, game_id):
        """
        Procesar vídeos directos (no YouTube) - reutilizar lógica de RAWG
        """
        temp_video_path = None
        temp_gif_path = None
        video_clip = None

        try:
            print(f"Verificando vídeo desde: {video_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Verificar tamaño
            head_response = requests.head(video_url, headers=headers, timeout=30)
            if head_response.status_code == 200:
                content_length = head_response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    print(f"Tamaño del vídeo: {size_mb:.1f} MB")

                    if size_mb > 500:
                        print("Vídeo demasiado grande para procesar")
                        return None

            # Descargar vídeo
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                temp_video_path = temp_video.name

                print(f"Descargando vídeo...")
                response = requests.get(
                    video_url, stream=True, timeout=120, headers=headers
                )
                response.raise_for_status()

                total_size = 0
                max_size = 300 * 1024 * 1024
                for chunk in response.iter_content(chunk_size=32768):
                    if chunk:
                        temp_video.write(chunk)
                        total_size += len(chunk)
                        if total_size % (50 * 1024 * 1024) < 32768:
                            print(f"Descargado: {total_size / (1024*1024):.1f} MB...")
                        if total_size > max_size:
                            print(
                                f"Vídeo demasiado grande ({total_size / (1024*1024):.1f} MB), abortando"
                            )
                            return None

            print(f"Vídeo descargado: {total_size / (1024*1024):.1f} MB")

            # Procesar igual que YouTube
            with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as temp_gif:
                temp_gif_path = temp_gif.name

            # Resto del procesamiento igual que _process_youtube_video
            # (código duplicado simplificado por brevedad)

            return None  # Por ahora, implementar si necesitas vídeos directos

        except Exception as e:
            print(f"Error procesando vídeo directo: {str(e)}")
            return None

        finally:
            if video_clip:
                try:
                    video_clip.close()
                except:
                    pass

            for temp_path in [temp_video_path, temp_gif_path]:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

    def select_random_game(self, max_iterations=10):
        """
        Seleccionar juego aleatorio con análisis por tandas y priorización inteligente
        Adaptado de la lógica de RAWG pero usando IGDB
        """

        used_games_ids = set(
            Game.objects.filter(
                used_date__isnull=False, igdb_id__isnull=False
            ).values_list("igdb_id", flat=True)
        )

        print(f"Iniciando búsqueda de juego aleatorio...")
        print(f"Juegos ya utilizados: {len(used_games_ids)}")

        for iteration in range(max_iterations):
            print(f"\nIteración {iteration + 1}/{max_iterations}")

            # Generar parámetros aleatorios para IGDB
            start_year = random.randint(1980, 2020)
            end_year = start_year + random.randint(3, 7)

            # Convertir años a timestamps Unix
            start_timestamp = int(datetime(start_year, 1, 1).timestamp())
            end_timestamp = int(datetime(end_year, 12, 31).timestamp())

            query = f"""
            fields name, id, aggregated_rating, screenshots.url, videos.video_id,
                   first_release_date, genres.name, platforms.name, cover.url;
            where aggregated_rating >= 60 & aggregated_rating <= 100 & screenshots != null & 
                  first_release_date > {start_timestamp} & first_release_date < {end_timestamp};
            sort aggregated_rating desc;
            limit 50;
            offset {random.randint(0, 200)};
            """

            print(f"Buscando juegos: {start_year}-{end_year} (Rating: 60-100)")

            try:
                games = self.make_request("games", query)

                if not games:
                    print("Error en API o sin resultados")
                    continue

                print(f"Juegos encontrados: {len(games)}")

                # Mostrar muestra de ratings obtenidos
                if games:
                    ratings = [g.get("aggregated_rating", 0) for g in games[:5]]
                    print(f"Ratings de muestra: {ratings}")

                available_games = [g for g in games if g["id"] not in used_games_ids]

                if not available_games:
                    print("No hay juegos disponibles en esta búsqueda")
                    continue

                print(f"Juegos disponibles (no usados): {len(available_games)}")

                # Seleccionar juegos para analizar
                games_to_analyze = random.sample(
                    available_games, min(5, len(available_games))
                )

                print(f"Analizando {len(games_to_analyze)} juegos candidatos...")

                # Analizar cada juego
                candidates = self._analyze_game_candidates(games_to_analyze)

                if not candidates:
                    print("Ningún juego cumple los requisitos mínimos")
                    continue

                # Seleccionar el mejor candidato
                selected_game = self._select_best_candidate(candidates)

                if selected_game:
                    print(
                        f"Juego seleccionado: {selected_game['name']} (ID: {selected_game['id']})"
                    )
                    print(f"Capturas: {selected_game.get('screenshots_count', 0)}")
                    print(
                        f"Vídeos: {'Sí' if selected_game.get('has_videos') else 'No'}"
                    )
                    print(f"Rating: {selected_game.get('aggregated_rating', 'N/A')}")

                    return self.process_selected_game(selected_game["id"])

            except Exception as e:
                print(f"Error inesperado: {e}")
                continue

        print(f"No se encontró juego válido después de {max_iterations} iteraciones")
        return None

    def _analyze_game_candidates(self, games_data):
        """
        Analizar candidatos y obtener información detallada
        """
        candidates = []

        for game_data in games_data:
            igdb_id = game_data["id"]
            game_name = game_data.get("name", "Desconocido")

            print(f"  Analizando: {game_name} (ID: {igdb_id})")

            try:
                # Obtener detalles completos
                game_details = self.get_game_details(igdb_id)
                if not game_details:
                    print(f"    No se pudieron obtener detalles")
                    continue

                # Contar capturas - aumentar requisito mínimo
                screenshots_count = len(game_details.get("screenshots", []))
                rating = game_details.get("aggregated_rating")

                # Verificar requisitos mínimos - necesitamos al menos 8 para seleccionar 5 buenas
                if screenshots_count < 8:
                    print(f"    Solo {screenshots_count} capturas (mínimo 8)")
                    continue

                # Verificar vídeos
                videos = self.get_game_videos(igdb_id)
                has_videos = len(videos) > 0

                # Crear candidato
                candidate = {
                    **game_details,
                    "screenshots_count": screenshots_count,
                    "has_videos": has_videos,
                    "video_count": len(videos),
                    "priority_score": self._calculate_priority_score(
                        screenshots_count, has_videos, rating
                    ),
                }

                candidates.append(candidate)

                print(
                    f"    Válido - Capturas: {screenshots_count}, Vídeos: {len(videos)}, Rating: {rating}/100"
                )

            except Exception as e:
                print(f"    Error analizando {game_name}: {e}")
                continue

        print(f"Candidatos válidos encontrados: {len(candidates)}")
        return candidates

    def _calculate_priority_score(self, screenshots_count, has_videos, rating):
        """
        Calcular puntuación de prioridad para un juego
        Con énfasis en juegos de alta calidad (60-100 rating)
        """
        # Base mejorada: dar más peso a puntuaciones altas
        if rating and rating >= 80:
            score = rating + 20  # Bonus extra para juegos excelentes
        elif rating and rating >= 70:
            score = rating + 10  # Bonus moderado para juegos muy buenos
        else:
            score = rating or 60  # Mínimo 60 como baseline

        if has_videos:
            score += 200

        if screenshots_count > 8:
            score += (screenshots_count - 8) * 5  # Bonus por más capturas

        return score

    def _select_best_candidate(self, candidates):
        """
        Seleccionar el mejor candidato según priorización
        """
        if not candidates:
            return None

        # Separar por disponibilidad de vídeos
        with_videos = [c for c in candidates if c.get("has_videos", False)]
        without_videos = [c for c in candidates if not c.get("has_videos", False)]

        print(f"Candidatos con vídeos: {len(with_videos)}")
        print(f"Candidatos sin vídeos: {len(without_videos)}")

        # Priorizar juegos con vídeos
        if with_videos:
            with_videos.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
            best = with_videos[0]
            print(
                f"Seleccionado (con vídeos): {best['name']} - Score: {best.get('priority_score', 0)}"
            )
            return best

        # Fallback a juegos sin vídeos
        if without_videos:
            without_videos.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
            best = without_videos[0]
            print(
                f"Seleccionado (sin vídeos): {best['name']} - Score: {best.get('priority_score', 0)}"
            )
            return best

        return None

    def process_selected_game(self, igdb_id):
        """
        Procesar el juego seleccionado. Obtener detalles, screenshots, vídeo y GIF
        Adaptado de la lógica de RAWG
        """

        game_details = self.get_game_details(igdb_id)

        if not game_details:
            return None

        # Procesar vídeos
        videos = self.get_game_videos(igdb_id)
        video_url = ""
        has_video = False

        if videos:
            video_url = videos[0].get("data", {}).get("max", "")
            has_video = True
            print(f"Vídeo encontrado para {game_details['name']}")
        else:
            print(f"No hay vídeos disponibles para {game_details['name']}")

        # Obtener capturas - aumentado para mejor selección
        screenshots = self.get_game_screenshots(igdb_id, max_screenshots=15)
        print(f"Obtenidas {len(screenshots)} capturas de IGDB API")

        if not screenshots:
            print(f"No hay capturas disponibles para {game_details['name']}")
            return None

        # CAMBIO: 5 capturas con vídeo, 6 sin vídeo (captura extra como pista)
        if len(screenshots) < 8:
            print(
                f"Insuficientes capturas ({len(screenshots)}) para análisis de calidad"
            )
            return None

        max_screenshots = 5 if has_video else 6

        print(
            f"Analizando {len(screenshots)} capturas para seleccionar las {max_screenshots} mejores"
        )
        print(
            f"Configuración: {'5 capturas + vídeo' if has_video else '6 capturas sin vídeo (pista extra)'}"
        )

        # Crear o actualizar el juego
        game, created = Game.objects.update_or_create(
            igdb_id=game_details["id"],
            defaults={
                "title": game_details["name"],
                "developer": self.get_developer_name(game_details),
                "release_year": self.get_release_year(
                    game_details.get("first_release_date")
                ),
                "genres": self.format_genres(game_details.get("genres", [])),
                "platforms": self.format_platforms(game_details.get("platforms", [])),
                "metacritic": (
                    int(game_details.get("aggregated_rating", 0))
                    if game_details.get("aggregated_rating")
                    else None
                ),
                "franchise_name": self.get_franchise_name(game_details),
                "franchise_slug": self.get_franchise_slug(game_details),
                "video_url": video_url,
            },
        )

        # Procesar vídeo y crear GIF si está disponible
        if video_url:
            print("Procesando vídeo para crear GIF...")
            if self.check_video_size(video_url):
                gif_path = self.download_and_convert_video_to_gif(video_url, game.id)
                if gif_path:
                    game.gif_path = gif_path
                    game.save(update_fields=["gif_path"])
                    print(f"GIF creado exitosamente para: {game.title}")
                else:
                    print(f"No se pudo crear GIF para: {game.title}")
            else:
                print(f"Vídeo demasiado grande para {game.title}, saltando GIF")
        else:
            print(f"{game.title} solo tendrá capturas de pantalla (sin vídeo/GIF)")

        # Limpiar capturas anteriores
        Screenshot.objects.filter(game=game).delete()

        # Guardar TODAS las capturas para análisis con IA (15 capturas)
        temp_screenshots = []
        for i, screenshot in enumerate(screenshots, 1):
            screenshot_obj = Screenshot.objects.create(
                game=game,
                image_url=screenshot["image"],
                difficulty=i,  # Temporal, se actualizará con análisis de IA
            )
            temp_screenshots.append(screenshot_obj)

        print(
            f"Guardadas {len(temp_screenshots)} capturas (de 15 obtenidas) para análisis con IA"
        )

        # Procesar con IA - OBLIGATORIO para la selección
        try:
            from guessityet.services.image_analysis_service import GameDifficultyService

            print(
                f"Analizando {len(temp_screenshots)} capturas de {game.title} con IA..."
            )
            difficulty_service = GameDifficultyService()

            success = difficulty_service.select_and_organize_best_screenshots(
                game, max_screenshots=max_screenshots
            )

            if success:
                print(
                    f"Las {max_screenshots} mejores capturas seleccionadas y organizadas para: {game.title}"
                )
                if not has_video:
                    print("  → Captura #6 disponible como pista extra (sin vídeo)")
            else:
                print(f"Error en análisis IA para: {game.title}")
                # Sin IA, no podemos hacer una buena selección de 10->5/6, mejor fallar
                return None

        except ImportError:
            print("ERROR: Servicio de análisis de imágenes no disponible")
            print("Este servicio es obligatorio para IGDB que maneja más capturas")
            return None

        return game

    def _fallback_random_selection(self, game, screenshots_data, max_screenshots=5):
        """
        Método de respaldo: seleccionar capturas aleatorias
        NOTA: Este método ya no se usa en IGDB, el análisis IA es obligatorio
        max_screenshots puede ser 5 o 6 dependiendo de si hay vídeo
        """
        print("ADVERTENCIA: Método de respaldo no recomendado para IGDB")

        selected_screenshots = random.sample(
            screenshots_data, min(max_screenshots, len(screenshots_data))
        )

        Screenshot.objects.filter(game=game).delete()
        for i, screenshot in enumerate(selected_screenshots, 1):
            Screenshot.objects.create(
                game=game, image_url=screenshot["image"], difficulty=i
            )

    def get_release_year(self, timestamp):
        """Extraer año de lanzamiento desde timestamp Unix"""

        if not timestamp:
            return None

        try:
            return datetime.fromtimestamp(timestamp).year
        except (ValueError, OSError):
            return None

    def get_developer_name(self, game_details):
        """Obtener nombre del desarrollador"""

        companies = game_details.get("involved_companies", [])
        for company in companies:
            if company.get("developer", False):
                return company.get("company", {}).get("name")

        # Si no hay desarrollador específico, usar la primera compañía
        if companies:
            return companies[0].get("company", {}).get("name")

        return None

    def get_franchise_name(self, game_details):
        """Obtener nombre de la franquicia"""

        franchises = game_details.get("franchises", [])
        return franchises[0].get("name") if franchises else None

    def get_franchise_slug(self, game_details):
        """Obtener slug de la franquicia"""

        franchises = game_details.get("franchises", [])
        return franchises[0].get("slug") if franchises else None

    def format_genres(self, genres):
        """Formatear géneros como cadena"""

        return ", ".join([g.get("name", "") for g in genres if g.get("name")])

    def format_platforms(self, platforms):
        """Formatear plataformas como cadena"""

        return ", ".join([p.get("name", "") for p in platforms if p.get("name")])
