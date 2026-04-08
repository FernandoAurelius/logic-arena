import json
from pathlib import Path

from django.core.management.base import BaseCommand

from arena.api import api


class Command(BaseCommand):
    help = 'Exporta o schema OpenAPI para backend/openapi.json'

    def handle(self, *args, **options):
        schema = api.get_openapi_schema()
        output_path = Path(__file__).resolve().parents[3] / 'openapi.json'
        output_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'OpenAPI exportado em {output_path}'))
