import requests
import random
import os
from django.conf import settings
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
from io import BytesIO
import uuid
from guessityet.models import Game, Screenshot
import tempfile
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import json
import base64
from typing import List, Tuple, Dict
import numpy as np
from collections import Counter


class ImageAnalysisService:
    """
    Servicio para analizar capturas de pantalla y determinar su nivel de revelación
    usando análisis de contenido y características visuales + OpenAI Vision
    """

    def __init__(self):
        # Palabras clave que indican contenido revelador en videojuegos
        self.revealing_keywords = {
            "high": [
                "logo",
                "title",
                "menu",
                "hud",
                "interface",
                "ui",
                "text",
                "character name",
                "health bar",
            ],
            "medium": [
                "character",
                "weapon",
                "vehicle",
                "building",
                "landscape",
                "environment",
            ],
            "low": [
                "abstract",
                "pattern",
                "texture",
                "background",
                "sky",
                "ground",
                "shadow",
            ],
        }

        # Configuración para OpenAI Vision API
        self.openai_api_key = getattr(settings, "OPENAI_API_KEY", None)

    def analyze_screenshot_revelation_level(self, image_url: str) -> Dict:
        """
        Analiza una captura de pantalla y determina qué tan reveladora es
        Retorna un diccionario con el score y análisis
        """
        try:
            # Descargar la imagen
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            image = Image.open(BytesIO(response.content))

            # Análisis visual básico
            visual_score = self._analyze_visual_features(image)

            # Análisis de contenido con IA (si está disponible)
            ai_score = self._analyze_with_ai(image) if self.openai_api_key else 0

            # Combinar puntuaciones - dar más peso a IA si está disponible
            if ai_score > 0:
                final_score = visual_score * 0.3 + ai_score * 0.7  # IA tiene más peso
                print(
                    f"Scores - Visual: {visual_score:.1f}, IA: {ai_score:.1f}, Final: {final_score:.1f}"
                )
            else:
                final_score = visual_score
                print(f"Score solo visual: {final_score:.1f}")

            return {
                "revelation_score": final_score,  # 0-100, donde 100 = muy revelador
                "visual_score": visual_score,
                "ai_score": ai_score,
                "analysis": self._get_analysis_description(final_score),
                "method_used": "AI + Visual" if ai_score > 0 else "Visual only",
            }

        except Exception as e:
            print(f"Error analizando imagen {image_url}: {e}")
            return {
                "revelation_score": 50,  # Score por defecto
                "visual_score": 50,
                "ai_score": 0,
                "analysis": "Error en análisis - score por defecto",
                "method_used": "Error",
            }

    def _analyze_visual_features(self, image: Image.Image) -> float:
        """
        Análisis visual básico de características que pueden ser reveladoras
        """
        score = 0

        # Convertir a RGB si es necesario
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Análisis de colores dominantes
        color_score = self._analyze_color_complexity(image)

        # Análisis de bordes y detalles
        edge_score = self._analyze_edge_density(image)

        # Análisis de contraste
        contrast_score = self._analyze_contrast(image)

        # Análisis de texto/UI elements
        ui_score = self._detect_ui_elements(image)

        # Combinar puntuaciones
        score = (
            color_score * 0.2 + edge_score * 0.3 + contrast_score * 0.2 + ui_score * 0.3
        )

        return min(100, max(0, score))

    def _analyze_color_complexity(self, image: Image.Image) -> float:
        """
        Analiza la complejidad de colores - más colores únicos = más revelador
        """
        # Reducir resolución para análisis rápido
        small_image = image.resize((100, 100))
        pixels = list(small_image.getdata())

        # Contar colores únicos (agrupados)
        color_groups = []
        for pixel in pixels:
            # Agrupar colores similares
            grouped_color = tuple(c // 32 * 32 for c in pixel)
            color_groups.append(grouped_color)

        unique_colors = len(set(color_groups))

        # Normalizar (más colores = más revelador)
        return min(100, (unique_colors / 50) * 100)

    def _analyze_edge_density(self, image: Image.Image) -> float:
        """
        Analiza la densidad de bordes - más detalles = más revelador
        """
        # Convertir a escala de grises
        gray_image = image.convert("L")

        # Aplicar filtro de detección de bordes
        edges = gray_image.filter(ImageFilter.FIND_EDGES)

        # Contar píxeles de borde
        edge_pixels = sum(1 for pixel in edges.getdata() if pixel > 50)
        total_pixels = edges.width * edges.height

        edge_density = (edge_pixels / total_pixels) * 100

        return min(100, edge_density * 2)  # Amplificar para mejor rango

    def _analyze_contrast(self, image: Image.Image) -> float:
        """
        Analiza el contraste - mayor contraste puede indicar elementos de UI
        """
        gray_image = image.convert("L")
        pixels = list(gray_image.getdata())

        if not pixels:
            return 50

        # Calcular histograma
        histogram = [0] * 256
        for pixel in pixels:
            histogram[pixel] += 1

        # Encontrar percentiles
        total_pixels = len(pixels)
        cumulative = 0
        p5, p95 = 0, 255

        for i, count in enumerate(histogram):
            cumulative += count
            percentage = cumulative / total_pixels

            if percentage >= 0.05 and p5 == 0:
                p5 = i
            if percentage >= 0.95:
                p95 = i
                break

        # Contraste como diferencia entre percentiles
        contrast = p95 - p5

        return min(100, (contrast / 255) * 100)

    def _detect_ui_elements(self, image: Image.Image) -> float:
        """
        Detecta elementos de interfaz de usuario que son muy reveladores
        """
        score = 0

        # Buscar regiones rectangulares sólidas (típicas de UI)
        score += self._detect_rectangular_regions(image) * 40

        # Buscar gradientes horizontales/verticales (barras de vida, menús)
        score += self._detect_gradients(image) * 30

        # Buscar patrones repetitivos (iconos, botones)
        score += self._detect_repetitive_patterns(image) * 30

        return min(100, score)

    def _detect_rectangular_regions(self, image: Image.Image) -> float:
        """
        Detecta regiones rectangulares que podrían ser elementos de UI
        """
        # Simplificado: buscar regiones de color sólido
        small_image = image.resize((50, 50))
        pixels = list(small_image.getdata())

        # Buscar líneas horizontales de color similar
        horizontal_lines = 0
        for y in range(small_image.height - 1):
            row1 = pixels[y * small_image.width : (y + 1) * small_image.width]
            row2 = pixels[(y + 1) * small_image.width : (y + 2) * small_image.width]

            if self._colors_similar(row1, row2):
                horizontal_lines += 1

        return min(1.0, horizontal_lines / (small_image.height * 0.3))

    def _detect_gradients(self, image: Image.Image) -> float:
        """
        Detecta gradientes que podrían indicar barras de progreso, menús, etc.
        """
        gray_image = image.convert("L").resize((50, 50))
        pixels = list(gray_image.getdata())

        gradient_score = 0

        # Buscar gradientes horizontales
        for y in range(gray_image.height):
            row = pixels[y * gray_image.width : (y + 1) * gray_image.width]
            if self._is_gradient(row):
                gradient_score += 1

        return min(1.0, gradient_score / (gray_image.height * 0.2))

    def _detect_repetitive_patterns(self, image: Image.Image) -> float:
        """
        Detecta patrones repetitivos que podrían ser iconos o elementos de UI
        """
        # Simplificado: buscar bloques de color similar
        small_image = image.resize((20, 20))
        pixels = list(small_image.getdata())

        # Dividir en bloques de 2x2 y buscar similitudes
        blocks = []
        for y in range(0, small_image.height - 1, 2):
            for x in range(0, small_image.width - 1, 2):
                block = [
                    pixels[y * small_image.width + x],
                    pixels[y * small_image.width + x + 1],
                    pixels[(y + 1) * small_image.width + x],
                    pixels[(y + 1) * small_image.width + x + 1],
                ]
                blocks.append(tuple(block))

        # Contar bloques similares
        block_counts = Counter(blocks)
        repeated_blocks = sum(1 for count in block_counts.values() if count > 1)

        return min(1.0, repeated_blocks / len(blocks))

    def _colors_similar(
        self, colors1: List, colors2: List, threshold: int = 30
    ) -> bool:
        """
        Determina si dos listas de colores son similares
        """
        if len(colors1) != len(colors2):
            return False

        differences = []
        for c1, c2 in zip(colors1, colors2):
            if isinstance(c1, tuple) and isinstance(c2, tuple):
                diff = sum(abs(a - b) for a, b in zip(c1, c2)) / len(c1)
            else:
                diff = abs(c1 - c2)
            differences.append(diff)

        avg_diff = sum(differences) / len(differences)
        return avg_diff < threshold

    def _is_gradient(self, values: List[int], min_change: int = 5) -> bool:
        """
        Determina si una lista de valores forma un gradiente
        """
        if len(values) < 3:
            return False

        # Calcular diferencias consecutivas
        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]

        # Buscar tendencia consistente
        positive_diffs = sum(1 for d in diffs if d > min_change)
        negative_diffs = sum(1 for d in diffs if d < -min_change)

        # Es gradiente si más del 60% de las diferencias van en la misma dirección
        total_significant_diffs = positive_diffs + negative_diffs
        if total_significant_diffs == 0:
            return False

        return (
            positive_diffs / total_significant_diffs > 0.6
            or negative_diffs / total_significant_diffs > 0.6
        )

    def _analyze_with_ai(self, image: Image.Image) -> float:
        """
        Análisis avanzado con OpenAI Vision API
        """
        if not self.openai_api_key:
            print("OpenAI API key no configurada, usando solo análisis visual básico")
            return 0

        try:
            # Redimensionar imagen para optimizar costos
            max_size = 1024
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Convertir imagen a base64
            buffer = BytesIO()
            # Convertir a RGB si es necesario
            if image.mode in ("RGBA", "LA"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background

            image.save(buffer, format="JPEG", quality=85)
            image_b64 = base64.b64encode(buffer.getvalue()).decode()

            # Prompt especializado para videojuegos
            prompt = """Analyze this video game screenshot and rate from 0-100 how revealing/identifying it is for guessing the specific game.

SCORING GUIDE:
- 90-100: Game title/logo visible, distinctive UI, main characters clearly shown, unique game elements
- 70-89: Recognizable characters, distinctive environments, game-specific UI elements, weapon/item icons
- 50-69: Generic game environments, common UI elements, general gameplay scenes
- 30-49: Landscapes, textures, backgrounds without distinctive features
- 10-29: Very generic elements, could be from any game
- 0-9: Abstract patterns, textures, or unclear images

Consider: UI elements, text, logos, character designs, distinctive art styles, recognizable locations, HUD elements.

Return ONLY a number between 0-100."""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}",
            }

            payload = {
                "model": "gpt-4o-mini",  # Más económico que gpt-4-vision-preview
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                    "detail": "low",  # Reduce costos
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.1,
            }

            print("Consultando OpenAI Vision API...")
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()

                # Extraer número del resultado
                import re

                numbers = re.findall(r"\b\d+(?:\.\d+)?\b", content)
                if numbers:
                    score = float(numbers[0])
                    print(f"OpenAI Score: {score}")
                    return min(100, max(0, score))
                else:
                    print(f"No se pudo extraer score de: {content}")
                    return 50
            else:
                print(f"Error OpenAI API: {response.status_code} - {response.text}")
                return 0

        except Exception as e:
            print(f"Error en análisis con OpenAI: {e}")
            return 0

    def _get_analysis_description(self, score: float) -> str:
        """
        Retorna una descripción del nivel de revelación
        """
        if score >= 80:
            return "Muy revelador - Contiene elementos de UI, texto o características distintivas"
        elif score >= 60:
            return "Bastante revelador - Muestra personajes o entornos reconocibles"
        elif score >= 40:
            return "Moderadamente revelador - Algunas pistas visuales disponibles"
        elif score >= 20:
            return "Poco revelador - Principalmente paisajes o elementos genéricos"
        else:
            return "Muy poco revelador - Abstracto o muy genérico"

    def create_zoomed_versions(
        self, image_url: str, game_id: int, difficulty_level: int
    ) -> List[str]:
        """
        Crea versiones con zoom de una imagen para diferentes niveles de dificultad
        ACTUALIZADO: Solo zoom en niveles 1-3, niveles 4+ sin zoom
        """
        try:
            # Descargar imagen original
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            original_image = Image.open(BytesIO(response.content))

            # Nueva configuración de zoom - SOLO para los primeros 3 niveles
            zoom_configs = {
                1: {
                    "zoom": 3.0,
                    "focus": "corner",
                    "description": "Muy difícil - esquina con mucho zoom",
                },
                2: {
                    "zoom": 2.5,
                    "focus": "edge",
                    "description": "Difícil - borde con zoom alto",
                },
                3: {
                    "zoom": 2.0,
                    "focus": "interesting",
                    "description": "Medio - área interesante con zoom medio",
                },
                # CAMBIO: Niveles 4+ sin zoom, solo imagen completa
                4: {
                    "zoom": 1.0,
                    "focus": "full",
                    "description": "Fácil - imagen completa sin zoom",
                },
                5: {
                    "zoom": 1.0,
                    "focus": "full",
                    "description": "Muy fácil - imagen completa sin zoom",
                },
                6: {
                    "zoom": 1.0,
                    "focus": "full",
                    "description": "Súper fácil - imagen completa sin zoom",
                },
            }

            config = zoom_configs.get(difficulty_level, zoom_configs[3])

            print(f"Nivel {difficulty_level}: {config['description']}")

            if config["zoom"] == 1.0:
                # Imagen completa - aplicar solo filtros muy sutiles o ninguno
                if difficulty_level >= 5:
                    # Niveles 5 y 6: imagen completamente original
                    processed_image = original_image.copy()
                    print(f"  → Imagen original sin modificaciones")
                else:
                    # Nivel 4: filtro muy sutil
                    processed_image = self._apply_minimal_filter(original_image)
                    print(f"  → Filtro mínimo aplicado")
            else:
                # Crear versión con zoom (niveles 1-3)
                processed_image = self._create_zoomed_crop(
                    original_image, config["zoom"], config["focus"]
                )
                print(
                    f"  → Zoom {config['zoom']}x aplicado con enfoque '{config['focus']}'"
                )

            # Guardar imagen procesada
            processed_path = self._save_processed_image(
                processed_image, game_id, difficulty_level, f"level_{difficulty_level}"
            )

            return [processed_path] if processed_path else []

        except Exception as e:
            print(f"Error creando versión para nivel {difficulty_level}: {e}")
            return []

    def _apply_minimal_filter(self, image: Image.Image) -> Image.Image:
        """
        Aplica filtros mínimos solo para el nivel 4 (para diferenciarlo ligeramente de los niveles 5-6)
        """
        # Solo un desenfoque muy ligero para suavizar píxeles pero mantener todos los detalles
        filtered = image.filter(ImageFilter.GaussianBlur(radius=0.3))

        # Reducir el contraste muy ligeramente
        enhancer = ImageEnhance.Contrast(filtered)
        filtered = enhancer.enhance(0.95)

        return filtered

    def _apply_subtle_filter(self, image: Image.Image) -> Image.Image:
        """
        DEPRECADO: Ya no se usa, reemplazado por _apply_minimal_filter
        Mantenido para compatibilidad
        """
        return self._apply_minimal_filter(image)

    def _create_zoomed_crop(
        self, image: Image.Image, zoom_factor: float, focus_type: str
    ) -> Image.Image:
        """
        Crea un recorte con zoom de la imagen
        """
        width, height = image.size

        # Calcular dimensiones del área a recortar
        crop_width = int(width / zoom_factor)
        crop_height = int(height / zoom_factor)

        # Determinar punto de enfoque según el tipo
        focus_points = {
            "corner": (crop_width // 4, crop_height // 4),
            "edge": (crop_width // 2, crop_height // 4),
            "center": (width // 2, height // 2),
            "interesting": self._find_interesting_point(image, crop_width, crop_height),
        }

        focus_x, focus_y = focus_points.get(focus_type, focus_points["center"])

        # Calcular coordenadas del recorte
        left = max(0, focus_x - crop_width // 2)
        top = max(0, focus_y - crop_height // 2)
        right = min(width, left + crop_width)
        bottom = min(height, top + crop_height)

        # Ajustar si se sale de los límites
        if right - left < crop_width:
            left = max(0, right - crop_width)
        if bottom - top < crop_height:
            top = max(0, bottom - crop_height)

        # Recortar y redimensionar
        cropped = image.crop((left, top, right, bottom))

        # Redimensionar a tamaño estándar manteniendo proporción
        target_size = (800, 600)
        cropped_resized = cropped.resize(target_size, Image.Resampling.LANCZOS)

        return cropped_resized

    def _find_interesting_point(
        self, image: Image.Image, crop_width: int, crop_height: int
    ) -> Tuple[int, int]:
        """
        Encuentra un punto interesante en la imagen usando análisis de bordes
        """
        # Convertir a escala de grises y aplicar detección de bordes
        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)

        # Dividir imagen en grid y encontrar área con más actividad
        grid_size = 8
        max_activity = 0
        best_x, best_y = image.width // 2, image.height // 2

        for i in range(grid_size):
            for j in range(grid_size):
                x = int((i + 0.5) * image.width / grid_size)
                y = int((j + 0.5) * image.height / grid_size)

                # Verificar que el recorte quepa
                if (
                    x - crop_width // 2 >= 0
                    and x + crop_width // 2 <= image.width
                    and y - crop_height // 2 >= 0
                    and y + crop_height // 2 <= image.height
                ):

                    # Calcular actividad en esta región
                    region = edges.crop(
                        (
                            x - crop_width // 4,
                            y - crop_height // 4,
                            x + crop_width // 4,
                            y + crop_height // 4,
                        )
                    )

                    activity = sum(pixel for pixel in region.getdata() if pixel > 50)

                    if activity > max_activity:
                        max_activity = activity
                        best_x, best_y = x, y

        return best_x, best_y

    def _apply_subtle_filter(self, image: Image.Image) -> Image.Image:
        """
        Aplica filtros sutiles a la imagen completa para el nivel más fácil
        """
        # Aplicar un ligero desenfoque para suavizar detalles muy obvios
        filtered = image.filter(ImageFilter.GaussianBlur(radius=0.5))

        # Reducir ligeramente el contraste
        enhancer = ImageEnhance.Contrast(filtered)
        filtered = enhancer.enhance(0.9)

        return filtered

    def _save_processed_image(
        self, image: Image.Image, game_id: int, difficulty: int, suffix: str
    ) -> str:
        """
        Guarda una imagen procesada y retorna la ruta
        """
        try:
            # Crear buffer para la imagen
            buffer = BytesIO()

            # Guardar con calidad optimizada
            if image.mode in ("RGBA", "LA"):
                # Convertir transparencia a blanco
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(
                    image, mask=image.split()[-1] if image.mode == "RGBA" else None
                )
                image = background

            image.save(buffer, format="JPEG", quality=85, optimize=True)
            image_content = buffer.getvalue()

            # Generar nombre único
            filename = f"processed_screenshots/game_{game_id}_diff_{difficulty}_{suffix}_{uuid.uuid4().hex[:8]}.jpg"

            # Guardar usando Django storage
            saved_path = default_storage.save(filename, ContentFile(image_content))

            return saved_path

        except Exception as e:
            print(f"Error guardando imagen procesada: {e}")
            return None


class GameDifficultyService:
    """
    Servicio principal para organizar las capturas por dificultad
    """

    def __init__(self):
        self.image_analyzer = ImageAnalysisService()

    def select_and_organize_best_screenshots(
        self, game: Game, max_screenshots: int = 5
    ) -> bool:
        """
        Analiza todas las capturas disponibles, selecciona las mejores y las organiza por dificultad
        """
        try:
            screenshots = list(game.screenshot_set.all())

            if len(screenshots) == 0:
                print(f"Juego {game.title} no tiene capturas")
                return False

            print(
                f"Analizando {len(screenshots)} capturas para seleccionar las {max_screenshots} mejores..."
            )

            # Analizar cada captura
            analyzed_screenshots = []
            for i, screenshot in enumerate(screenshots, 1):
                print(f"Analizando captura {i}/{len(screenshots)}...")

                analysis = self.image_analyzer.analyze_screenshot_revelation_level(
                    screenshot.image_url
                )

                analyzed_screenshots.append(
                    {
                        "screenshot": screenshot,
                        "revelation_score": analysis["revelation_score"],
                        "analysis": analysis,
                        "quality_score": self._calculate_quality_score(analysis),
                    }
                )

                print(
                    f"  Score revelación: {analysis['revelation_score']:.1f} - {analysis['analysis']}"
                )

            # Seleccionar las mejores capturas basándose en diversidad y calidad
            best_screenshots = self._select_best_diverse_screenshots(
                analyzed_screenshots, max_screenshots
            )

            print(f"Seleccionadas {len(best_screenshots)} mejores capturas")

            # Limpiar capturas existentes
            Screenshot.objects.filter(game=game).delete()

            # Ordenar las seleccionadas por score de revelación (menor = más difícil)
            best_screenshots.sort(key=lambda x: x["revelation_score"])

            # Crear las capturas finales con niveles de dificultad y zoom
            for i, item in enumerate(best_screenshots, 1):
                screenshot_data = item["screenshot"]
                difficulty = i  # 1 = más difícil, 5 = más fácil

                # Crear nueva captura con dificultad asignada
                new_screenshot = Screenshot.objects.create(
                    game=game,
                    image_url=screenshot_data.image_url,
                    difficulty=difficulty,
                )

                # Crear versión procesada con zoom
                processed_paths = self.image_analyzer.create_zoomed_versions(
                    screenshot_data.image_url, game.id, difficulty
                )

                if processed_paths:
                    new_screenshot.local_path = processed_paths[0]
                    new_screenshot.save(update_fields=["local_path"])

                print(
                    f"Captura {i}: Dificultad {difficulty}, Score: {item['revelation_score']:.1f}"
                )

            return True

        except Exception as e:
            print(f"Error seleccionando y organizando capturas para {game.title}: {e}")
            return False

    def _calculate_quality_score(self, analysis: dict) -> float:
        """
        Calcula un score de calidad general de la captura
        Combina factores como revelación, características visuales, etc.
        """
        revelation_score = analysis.get("revelation_score", 50)
        visual_score = analysis.get("visual_score", 50)

        # Penalizar capturas extremadamente reveladoras (logos, menús obvios)
        if revelation_score > 90:
            revelation_penalty = (revelation_score - 90) * 2
        else:
            revelation_penalty = 0

        # Penalizar capturas extremadamente poco reveladoras (muy abstractas)
        if revelation_score < 10:
            abstract_penalty = (10 - revelation_score) * 1.5
        else:
            abstract_penalty = 0

        # Score de calidad balanceado
        quality_score = (
            revelation_score * 0.6  # Importancia de revelación
            + visual_score * 0.4  # Importancia de características visuales
            - revelation_penalty  # Penalizar demasiado obvio
            - abstract_penalty  # Penalizar demasiado abstracto
        )

        return max(0, min(100, quality_score))

    def _select_best_diverse_screenshots(
        self, analyzed_screenshots: list, max_count: int
    ) -> list:
        """
        Selecciona las mejores capturas asegurando diversidad en niveles de revelación
        """
        if len(analyzed_screenshots) <= max_count:
            return analyzed_screenshots

        # Ordenar por score de calidad
        analyzed_screenshots.sort(key=lambda x: x["quality_score"], reverse=True)

        # Seleccionar con diversidad
        selected = []
        revelation_ranges = [
            (0, 20),  # Muy poco revelador
            (20, 40),  # Poco revelador
            (40, 60),  # Moderado
            (60, 80),  # Bastante revelador
            (80, 100),  # Muy revelador
        ]

        # Intentar seleccionar al menos una captura de cada rango
        for min_score, max_score in revelation_ranges:
            if len(selected) >= max_count:
                break

            # Buscar la mejor captura en este rango que no esté ya seleccionada
            candidates = [
                item
                for item in analyzed_screenshots
                if min_score <= item["revelation_score"] < max_score
                and item not in selected
            ]

            if candidates:
                # Tomar la de mejor calidad en este rango
                best_in_range = max(candidates, key=lambda x: x["quality_score"])
                selected.append(best_in_range)

        # Si aún necesitamos más capturas, tomar las mejores restantes
        while len(selected) < max_count and len(selected) < len(analyzed_screenshots):
            remaining = [item for item in analyzed_screenshots if item not in selected]
            if not remaining:
                break
            best_remaining = max(remaining, key=lambda x: x["quality_score"])
            selected.append(best_remaining)

        print(f"Diversidad de capturas seleccionadas:")
        for i, item in enumerate(selected, 1):
            print(
                f"   {i}. Score revelación: {item['revelation_score']:.1f}, Calidad: {item['quality_score']:.1f}"
            )

        return selected
