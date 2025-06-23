from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from APIs.urls.movie_urls import movie_urls
from APIs.urls.user_urls import user_urls

schema_view = get_schema_view(
    openapi.Info(
        title="Nachos API",
        default_version="v1",
        description="API documentation for Nachos backend",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@nachos.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url="https://nachos-backend-production.up.railway.app",
    schemes=["https", "http"],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include(user_urls)),
    path("movies/", include(movie_urls)),
    # Swagger documentation URLs
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
