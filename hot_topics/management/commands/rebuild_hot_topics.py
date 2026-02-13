from django.core.management.base import BaseCommand

from hot_topics.services import rebuild_hot_posts


class Command(BaseCommand):
    help = "Recompute global/category hot topic rankings"

    def handle(self, *args, **options):
        summary = rebuild_hot_posts()
        self.stdout.write(
            self.style.SUCCESS(
                "Rebuilt hot topics. "
                f"Global={summary['global_count']} CategoryEntries={summary['category_count']}"
            )
        )
