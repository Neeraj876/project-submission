import math

from django.utils import timezone

from .models import Category, HotPost, Post


GLOBAL_CATEGORY_LIMIT = 20
CATEGORY_HOT_LIMIT = 20


def trending_score(post, now=None):
    if now is None:
        now = timezone.now()
    age_hours = max((now - post.created_at).total_seconds() / 3600.0, 0.0)
    engagement = (
        post.likes
        + (2.0 * post.comments)
        + (3.0 * post.shares)
        + (0.05 * math.log1p(post.views))
    )
    return (engagement + 1.0) / (1.0 + (age_hours / 6.0))


def _top_ranked(posts, limit, now):
    scored = [(trending_score(post, now=now), post) for post in posts]
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:limit]


def rebuild_hot_posts():
    now = timezone.now()
    all_active_posts = list(
        Post.objects.filter(is_active=True).select_related("topic", "topic__category")
    )

    HotPost.objects.all().delete()
    to_create = []

    global_top = _top_ranked(all_active_posts, GLOBAL_CATEGORY_LIMIT, now)
    for idx, (score, post) in enumerate(global_top, start=1):
        to_create.append(HotPost(category=None, post=post, score=score, rank=idx))

    for category in Category.objects.all():
        cat_posts = [p for p in all_active_posts if p.topic.category_id == category.id]
        cat_top = _top_ranked(cat_posts, CATEGORY_HOT_LIMIT, now)
        for idx, (score, post) in enumerate(cat_top, start=1):
            to_create.append(
                HotPost(category=category, post=post, score=score, rank=idx)
            )

    HotPost.objects.bulk_create(to_create, batch_size=500)
    return {
        "global_count": len(global_top),
        "category_count": len(to_create) - len(global_top),
        "computed_at": now,
    }
