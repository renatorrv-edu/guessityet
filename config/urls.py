# config/urls.py - URLs principales del proyecto
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Administración de Django
    path("admin/", admin.site.urls),
    # path("cuentas/", include("django.contrib.auth.urls")),
    # Aplicación principal GuessItYet
    path("", include("guessityet.urls")),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # URLs adicionales para desarrollo
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Manejo de errores personalizados
handler404 = "guessityet.views.custom_404"
handler500 = "guessityet.views.custom_500"
