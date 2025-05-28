"""
URL configuration for virtual_interior_designer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from interior_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('upload/', views.upload_image, name='upload_image'),
    path('edit/', views.edit_image, name='edit_image'),
    path('api/segment/', views.segment_object, name='segment_object'),
    path('api/grabcut-rectangle/', views.grabcut_rectangle, name='grabcut_rectangle'),
    path('api/grabcut-strokes/', views.grabcut_strokes, name='grabcut_strokes'),
    path('api/refine-grabcut/', views.refine_grabcut_mask, name='refine_grabcut_mask'),
    path('api/inpaint/', views.inpaint_image, name='inpaint_image'),
    path('download/', views.download_result, name='download_result'),
    # Stable Diffusion APIs
    path('api/set-colab-url/', views.set_colab_url, name='set_colab_url'),
    path('api/check-colab-status/', views.check_colab_status, name='check_colab_status'),
    path('api/generate-furniture/', views.generate_furniture, name='generate_furniture'),
    path('api/furniture-suggestions/', views.get_furniture_suggestions, name='furniture_suggestions'),
    path('download-sd/', views.download_sd_result, name='download_sd_result'),
    # AI Image Analysis APIs
    path('api/upload-reference/', views.upload_reference_image, name='upload_reference_image'),
    path('api/analyze-reference/', views.analyze_reference_image, name='analyze_reference_image'),
    path('api/get-analysis/', views.get_analysis_result, name='get_analysis_result'),
]

# Thêm đường dẫn cho static và media files trong môi trường development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
