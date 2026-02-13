from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="hot_topics_home"),
    path("category/<slug:slug>/", views.category_page, name="hot_topics_category"),
    path(
        "category/<slug:slug>/search/",
        views.category_search_partial,
        name="hot_topics_category_search_partial",
    ),
    path("api/hot-topics/", views.api_hot_landing, name="api_hot_topics_landing"),
    path(
        "api/category/<slug:slug>/search/",
        views.api_category_search,
        name="api_hot_topics_category_search",
    ),
]
