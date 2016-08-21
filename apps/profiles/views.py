# =====================
# Python stdlib imports
# =====================



# ==============
# Django imports
# ==============

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.context_processors import csrf
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import simplejson, timezone

#===============
#project imports
#===============
from crowd.views.workers import _check_if_worker
from crowd.models.assignment import AssignmentSession
from profiles.models import WorkerProfile


def _check_if_worker(user):
    try:
        return user.get_profile().is_worker
    except:
        return False

@login_required
@user_passes_test(_check_if_worker)
def index(request):

    user = request.user
    sessions = AssignmentSession.objects.filter(worker=user)

    return render(request, 'profiles/index.html', {'lista': sessions})

@login_required
@user_passes_test(_check_if_worker)
def update_table(request):
    ret = {}
    user = request.user

    # ret = {
    #     "aaData": [
    #         [ "Trident", "Internet Explorer 4.0", "Win 95+", 4, "X" ],
    #         [ "Trident", "Internet Explorer 5.0", "Win 95+", 5, "C" ],
    #         [ "Trident", "Internet Explorer 5.5", "Win 95+", 5.5, "A" ],
    #         [ "Trident", "Internet Explorer 6.0", "Win 98+", 6, "A" ],
    #         [ "Trident", "Internet Explorer 7.0", "Win XP SP2+", 7, "A" ],
    #         [ "Gecko", "Firefox 1.5", "Win 98+ / OSX.2+", 1.8, "A" ],
    #         [ "Gecko", "Firefox 2", "Win 98+ / OSX.2+", 1.8, "A" ],
    #         [ "Gecko", "Firefox 3", "Win 2k+ / OSX.3+", 1.9, "A" ],
    #         [ "Webkit", "Safari 1.2", "OSX.3", 125.5, "A" ],
    #         [ "Webkit", "Safari 1.3", "OSX.3", 312.8, "A" ],
    #         [ "Webkit", "Safari 2.0", "OSX.4+", 419.3, "A" ],
    #         [ "Webkit", "Safari 3.0", "OSX.4+", 522.1, "A" ]
    #     ],
    #     "aoColumns": [
    #         { "sTitle": "Engine" },
    #         { "sTitle": "Browser" },
    #         { "sTitle": "Platform" },
    #         { "sTitle": "Version", "sClass": "center" },
    #         { "sTitle": "Grade", "sClass": "center" }
    #     ]
    # }

    # ret["aoColumns"] = [
    #     { "sTitle": "ID" },
    #     { "sTitle": "Status" },
    #     { "sTitle": "Accuracy" }
    #   ]

    user = request.user
    sessions = AssignmentSession.objects.filter(worker=user)

    table_content = []
    for session in sessions:
        status = ''
        accuracy = '-'

        done = False
        if session.expired:
            status = 'Expired'
        elif session.skipped:
            status = 'Skipped'
        elif session.has_result and session.assignment.concluded:
            status = 'Done'
            accuracy = str(session.stats.accuracy)
        elif session.has_result and not session.assignment.has_merge:
            status = 'No result available yet'

        table_content.append([session.id, status, accuracy])

    ret["aaData"] = table_content

    return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

@login_required
@user_passes_test(_check_if_worker)
def worker_stats(request):
    user = request.user
#    s_mgr = AssignmentSession.objects

    wp = WorkerProfile.objects.get(user=user)

    ret = {}
    ret['score'] = "{:,d}".format(wp.score)
    ranking = cache.get('ranking_dict')
    list = cache.get('profiles_list')
    if ranking:
        ret['position'] = ranking[user.id][2]

    return HttpResponse(simplejson.dumps(ret), mimetype='application/json')
