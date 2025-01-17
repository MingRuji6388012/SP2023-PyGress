from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.contrib.auth import views



urlpatterns = [
    url(
        r'^silk/',
        include('silk.urls', namespace='silk', app_name='silk')
        ),
    url(
        r'^example_app/',
        include('example_app.urls', namespace='example_app', app_name='example_app')
        ),
    url(r'^admin/', include(admin.site.urls)),
]



urlpatterns += [
    url(
        r'^login/$',
        views.login,
        {'template_name': 'example_app/login.html'}, name='login'),
]



urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
              static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
