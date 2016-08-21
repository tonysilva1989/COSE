from django.conf.urls import url, patterns

# =============================
# URL configuration for workers
# =============================

urlpatterns = patterns('profiles.views',
    url('^workers/profile$', 'index', name='profile_index'),
    url('^workers/my_stats', 'worker_stats', name='worker_stats'),
    url('^workers/update_table', 'update_table', name='update_table'),
)
