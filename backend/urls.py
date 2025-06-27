from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
import APIs
from APIs.urls import group_urls, community_urls
from APIs.urls.movie import movie_urls
from APIs.urls import movie as movie_urls_file
from APIs.views import movie as movie_views
from APIs.urls.user import user_urls
from APIs.urls.genres import genres_urls
from APIs.urls.watchlist import watchlist_urls
from APIs.urls.authenticate import auth_urls
from APIs.urls.user import admin_user_urls as admin_urls # Import admin URLs
from django.conf import settings
from django.conf.urls.static import static # New import

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
    url=settings.PUBLIC_API_URL,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include([
        path("auth/", include(auth_urls)),
        path("profile/", include(user_urls)),
        path("movies/", include([
            path("", include(movie_urls_file.movie_urls)),
            path("rate/", movie_views.rate_movie, name="rate-movie"),
        ])),
        path("genres/", include(genres_urls)),
        path("watchlist/", include(watchlist_urls)),
        path("admin/", include(admin_urls)),
        path("groups/", include(group_urls.urlpatterns)),
        path("communities/", include(community_urls.urlpatterns)),
    ])),
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

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
