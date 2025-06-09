from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = "Configura el Site para el entorno actual"

    def add_arguments(self, parser):
        parser.add_argument(
            "--domain",
            type=str,
            help="Dominio del site",
        )
        parser.add_argument(
            "--name",
            type=str,
            default="Guess It Yet?",
            help="Nombre del site",
        )

    def handle(self, *args, **options):
        domain = options["domain"]
        name = options["name"]

        if not domain:
            if settings.DEBUG:
                domain = "localhost:8000"
            else:
                domain = input("Introduce el dominio de producción: ")

        try:
            site = Site.objects.get(id=1)
            site.domain = domain
            site.name = name
            site.save()
            self.stdout.write(
                self.style.SUCCESS(f"Site actualizado: {domain} - {name}")
            )
        except Site.DoesNotExist:
            site = Site.objects.create(id=1, domain=domain, name=name)
            self.stdout.write(self.style.SUCCESS(f"Site creado: {domain} - {name}"))
