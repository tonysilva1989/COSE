###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## planta project URLconf.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# ==============
# Django imports
# ==============

from django.conf.urls import include, patterns, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# ===============
# project imports
# ===============

import apps
import settings


# ==================================
# URL configuration for project apps
# ==================================

urlpatterns = patterns('',
    url(r'^crowd/', include('apps.crowd.urls', namespace='crowd', app_name='crowd')),
    url(r'^profiles/', include('apps.profiles.urls', namespace='profiles', app_name='profiles'))
)

# ==============================================
# URL configuration for registration application
# ==============================================

from registration.views import register


urlpatterns += patterns('',
    url(r'^account/register/$', register, {
        'backend': 'registration.backends.default.DefaultBackend',
        'form_class': apps.profiles.forms.RegistrationForm
    }, name='registration_register'),
    url(r'^account/', include('registration.backends.default.urls'))
)

# =======================================
# URL configuration for admin application
# =======================================

admin.autodiscover()

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls))
)

# ========================
# Others URL configuration
# ========================

urlpatterns += patterns('',
    url(r'^$', 'planta.views.index', name='index'),
    url(r'^$', 'planta.views.about', name='about'),
    url(r'^crowd/workers/about.html', 'planta.views.about', name='about'),
    url(r'^crowd/workers/help.html', 'planta.views.help', name='help')
)

# Media files serving
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Static files serving
urlpatterns += staticfiles_urlpatterns()
