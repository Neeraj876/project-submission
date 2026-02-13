from django.contrib import admin

from .models import Category, HotPost, Post, Topic


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug")
    list_filter = ("category",)
    search_fields = ("name", "slug")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "topic",
        "likes",
        "comments",
        "shares",
        "views",
        "created_at",
        "is_active",
    )
    list_filter = ("topic__category", "topic", "is_active")
    search_fields = ("title", "body")


@admin.register(HotPost)
class HotPostAdmin(admin.ModelAdmin):
    list_display = ("category", "rank", "post", "score", "computed_at")
    list_filter = ("category", "computed_at")

# Register your models here.
