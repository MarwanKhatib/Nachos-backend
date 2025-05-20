from django.contrib import admin
from django.urls import include, path
from APIs.urls.user_urls import user_urls
urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include(user_urls)),
]
