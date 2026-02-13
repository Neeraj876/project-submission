import secrets

from django.core.management.base import BaseCommand, CommandError

from telemetry.models import AppClient


class Command(BaseCommand):
    help = "Create a telemetry client with API key and shared secret"

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True, help="Client name")

    def handle(self, *args, **options):
        name = options["name"].strip()
        if not name:
            raise CommandError("name cannot be empty")
        if AppClient.objects.filter(name=name).exists():
            raise CommandError(f"Client '{name}' already exists")

        api_key = secrets.token_hex(16)
        secret = secrets.token_hex(32)
        client = AppClient.objects.create(name=name, api_key=api_key, secret=secret)

        self.stdout.write(self.style.SUCCESS(f"Created client: {client.name}"))
        self.stdout.write(f"API key: {api_key}")
        self.stdout.write(f"Secret : {secret}")
