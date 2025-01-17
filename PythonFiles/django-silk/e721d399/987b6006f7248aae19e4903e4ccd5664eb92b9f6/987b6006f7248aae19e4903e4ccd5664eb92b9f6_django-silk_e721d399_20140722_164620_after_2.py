from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       url(r'^silk/', include('silk.urls', namespace='silk', app_name='silk')),
                       url(r'^example_app/', include('example_app.urls', namespace='example_app', app_name='example_app')),
                       url(r'^admin/', include(admin.site.urls)),

)

urlpatterns += patterns('',
                       url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'example_app/login.html'}, name='login'),
                       )