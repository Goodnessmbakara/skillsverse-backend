"""skillsverse_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# from django_tus.views import TusUpload

urlpatterns = [
    path("admin/", admin.site.urls),
    # path("api/user/", include("user.urls")),
    path("api/job/", include("job.urls")),
    # path("upload/", TusUpload.as_view(), name="tus_upload"),
    # path("upload/<uuid:resource_id>", TusUpload.as_view(), name="tus_upload_chunks"),
]
