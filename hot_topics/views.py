from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from .models import Category, HotPost, Post


def _category_search_results(category, q, limit=25):
    if not q:
        return []
    return list(
        Post.objects.filter(topic__category=category, is_active=True)
        .filter(
            Q(title__icontains=q)
            | Q(body__icontains=q)
            | Q(topic__name__icontains=q)
        )
        .select_related("topic")
        .order_by("-created_at")[:limit]
    )


def home(request):
    global_hot = list(
        HotPost.objects.filter(category__isnull=True)
        .select_related("post", "post__topic", "post__topic__category")
        .order_by("rank")[:20]
    )

    category_sections = []
    for category in Category.objects.order_by("name"):
        top_posts = list(
            HotPost.objects.filter(category=category)
            .select_related("post")
            .order_by("rank")[:5]
        )
        category_sections.append({"category": category, "top_posts": top_posts})

    return render(
        request,
        "hot_topics/home.html",
        {
            "global_hot": global_hot,
            "category_sections": category_sections,
        },
    )


def category_page(request, slug):
    category = get_object_or_404(Category, slug=slug)
    hot_posts = list(
        HotPost.objects.filter(category=category)
        .select_related("post", "post__topic")
        .order_by("rank")[:20]
    )

    q = request.GET.get("q", "").strip()
    search_results = _category_search_results(category, q, limit=25)

    return render(
        request,
        "hot_topics/category.html",
        {
            "category": category,
            "hot_posts": hot_posts,
            "q": q,
            "search_results": search_results,
        },
    )


def category_search_partial(request, slug):
    category = get_object_or_404(Category, slug=slug)
    q = request.GET.get("q", "").strip()
    search_results = _category_search_results(category, q, limit=25)
    return render(
        request,
        "hot_topics/_search_results.html",
        {
            "category": category,
            "q": q,
            "search_results": search_results,
        },
    )


def api_hot_landing(request):
    global_hot = (
        HotPost.objects.filter(category__isnull=True)
        .select_related("post", "post__topic", "post__topic__category")
        .order_by("rank")[:20]
    )
    return JsonResponse(
        {
            "count": len(global_hot),
            "items": [
                {
                    "rank": item.rank,
                    "score": round(item.score, 4),
                    "post_id": item.post_id,
                    "title": item.post.title,
                    "topic": item.post.topic.name,
                    "category": item.post.topic.category.name,
                    "likes": item.post.likes,
                    "comments": item.post.comments,
                    "shares": item.post.shares,
                    "views": item.post.views,
                    "created_at": item.post.created_at.isoformat(),
                }
                for item in global_hot
            ],
        }
    )


def api_category_search(request, slug):
    category = get_object_or_404(Category, slug=slug)
    q = request.GET.get("q", "").strip()
    qs = Post.objects.filter(topic__category=category, is_active=True)
    if q:
        qs = qs.filter(
            Q(title__icontains=q) | Q(body__icontains=q) | Q(topic__name__icontains=q)
        )
    results = qs.select_related("topic").order_by("-created_at")[:50]
    return JsonResponse(
        {
            "category": category.name,
            "query": q,
            "count": len(results),
            "items": [
                {
                    "post_id": p.id,
                    "title": p.title,
                    "topic": p.topic.name,
                    "likes": p.likes,
                    "comments": p.comments,
                    "shares": p.shares,
                    "views": p.views,
                    "created_at": p.created_at.isoformat(),
                }
                for p in results
            ],
        }
    )
