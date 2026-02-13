from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Topic(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"], name="unique_topic_name_per_category"
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category.name} / {self.name}"


class Post(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=220)
    body = models.TextField()
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["topic", "created_at"]),
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self):
        return self.title


class HotPost(models.Model):
    # category=None means global hot list for landing page.
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="hot_posts",
        null=True,
        blank=True,
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="hot_entries")
    score = models.FloatField()
    rank = models.PositiveIntegerField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "rank"]),
            models.Index(fields=["computed_at"]),
        ]

    def __str__(self):
        scope = "global" if self.category_id is None else self.category.name
        return f"{scope}#{self.rank}: {self.post_id}"
