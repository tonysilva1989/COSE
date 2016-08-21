###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## crowd app URLconf.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


from django.conf.urls import url, patterns


# ============================
# URL configuration for admins
# ============================

urlpatterns = patterns('crowd.views.admin',
    url('^report/$', 'report', name='report'),
)

# ================================
# URL configuration for requesters
# ================================

urlpatterns += patterns('crowd.views.requesters',
    url('^requesters/$', 'index', name='requesters_index'),
)

# =============================
# URL configuration for workers
urlpatterns += patterns('crowd.views.workers',
    url('^workers/$', 'index', name='workers_index'),
    url('^workers/session$', 'assignment_session_data'),
    url('^workers/rank/$', 'ranking_index', name='ranking_index'),
    url('^workers/rank/(\d+)$', 'top_k', name='ranking_view'),
    url('^workers/profile$','profile',name='profile_index') #definindo a pagina de profile
#    url('^workers/my_stats$', 'worker_stats'),
#    url('^workers/rank/(\d+)$', 'workers_top_k'),
#    url('^workers/top_10$', 'workers_top_k', {'k': 10})
)
# =============================

