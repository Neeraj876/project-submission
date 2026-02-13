import random

from django.core.management.base import BaseCommand
from django.utils import timezone

from hot_topics.models import Category, Post, Topic


class Command(BaseCommand):
    help = "Seed sample categories/topics/posts for hot topics demo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing hot topics data before seeding",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            Post.objects.all().delete()
            Topic.objects.all().delete()
            Category.objects.all().delete()

        sample = {
            "Technology": [
                "AI Tools",
                "Web Development",
                "Cloud Infrastructure",
            ],
            "Sports": [
                "Football Analysis",
                "Cricket Trends",
                "Basketball Strategy",
            ],
            "Finance": [
                "Personal Finance",
                "Stock Market",
                "Startup Funding",
            ],
        }

        post_count = 0
        now = timezone.now()
        for cat_name, topics in sample.items():
            category, _ = Category.objects.get_or_create(name=cat_name)
            for topic_name in topics:
                topic, _ = Topic.objects.get_or_create(category=category, name=topic_name)
                for i in range(1, 21):
                    # Keep spread over recent hours so recency impacts score.
                    created_at = now - timezone.timedelta(hours=random.randint(0, 72))
                    post = Post.objects.create(
                        topic=topic,
                        title=f"{topic_name} post {i}",
                        body=f"Discussion thread {i} about {topic_name}.",
                        likes=random.randint(10, 1500),
                        comments=random.randint(5, 500),
                        shares=random.randint(1, 300),
                        views=random.randint(100, 50000),
                    )
                    # Adjust created_at after create because auto_now_add sets it.
                    Post.objects.filter(id=post.id).update(created_at=created_at)
                    post_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seeded categories/topics with {post_count} posts")
        )
