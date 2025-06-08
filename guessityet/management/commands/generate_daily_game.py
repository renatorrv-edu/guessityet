from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from guessityet.models import DailyGame
from guessityet.services.igdb_service import IGDBService


class Command(BaseCommand):
    help = "Generar juego diario para una fecha específica"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forzar generación incluso si ya existe un juego",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Fecha específica (YYYY-MM-DD) para generar el juego",
        )

    def handle(self, *args, **options):
        if options["date"]:
            try:
                target_date = timezone.datetime.strptime(
                    options["date"], "%Y-%m-%d"
                ).date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR("Formato de fecha inválido. Usa YYYY-MM-DD")
                )
                return
        else:
            target_date = timezone.now().date() + timedelta(days=1)

        # Verificar si ya existe
        if DailyGame.objects.filter(date=target_date).exists() and not options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Ya existe un juego para {target_date}. Usa --force para sobreescribir."
                )
            )
            return

        # Si se está forzando, eliminar el existente
        if options["force"]:
            DailyGame.objects.filter(date=target_date).delete()
            self.stdout.write(f"Juego existente para {target_date} eliminado.")

        # Ejecutar la tarea directamente (no la programada)
        self.stdout.write(f"Generando juego diario para {target_date}...")

        try:
            # Llamar directamente al servicio en lugar de la tarea de Celery
            igdb_service = IGDBService()
            game = igdb_service.select_random_game()

            if not game:
                self.stdout.write(
                    self.style.ERROR("No se pudo seleccionar un juego usando IGDB.")
                )
                return

            # Crear el DailyGame directamente
            daily_game = DailyGame.objects.create(
                game=game,
                date=target_date,
            )

            # Marcar el juego como usado
            game.used_date = target_date
            game.save(update_fields=["used_date"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Juego para el {target_date} seleccionado correctamente: {game.title}"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            import traceback

            self.stdout.write(traceback.format_exc())
