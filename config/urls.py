"""
URL configuration for config project.

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
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap, index as sitemap_index
from .sitemaps import StaticViewSitemap, ServiceSitemap
from .views import homepage_view
from apps.site_config.views import (
    about_page,
    contact_page,
    terms_page,
    privacy_page,
)
from . import admin_dashboard  # noqa: F401 — patches AdminSite.index on import

sitemaps = {
    "static": StaticViewSitemap,
    "services": ServiceSitemap,
}

urlpatterns = [
    path('', homepage_view, name='homepage'),
    # Static site pages
    path('about/', about_page, name='about'),
    path('contact/', contact_page, name='contact'),
    path('terms/', terms_page, name='terms'),
    path('privacy/', privacy_page, name='privacy'),
    path('services/', include('apps.services.urls', namespace='services')),
    path('bookings/', include('apps.bookings.urls', namespace='bookings')),
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path('i18n/', include('django.conf.urls.i18n')),

    # ── Technical SEO (ARCHITECTURAL_PRINCIPLES §9.5) ──────────
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain',
        extra_context={'sitemap_url': '/sitemap.xml'},
    ), name='robots'),
    path('sitemap.xml', sitemap_index, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.index'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

# to serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)