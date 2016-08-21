###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Views related to workers in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =====================
# Python stdlib imports
# =====================

import urllib

from collections import OrderedDict
from apps.crowd.models.segprob import SegmentationProblem


try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# ==============
# Django imports
# ==============

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.context_processors import csrf
from django.core.cache import cache
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import simplejson, timezone

# ===============
# project imports
# ===============

from crowd.models.assignment import AssignmentSession, AssignmentSessionStats
from profiles.models import WorkerProfile
from helpers import dip as h_dip

def _check_if_worker(user):
    try:
        return user.get_profile().is_worker
    except:
        return False

@login_required
@user_passes_test(_check_if_worker)
def assignment_session_data(request):
    ret = {
        'csrfToken': str(csrf(request)['csrf_token'])
    }
    
    user = request.user
    session = AssignmentSession.objects.get_by_worker(user)
    wp = WorkerProfile.objects.get(user=user)

    if session is not None and session.expired:
        session.close()
        session.save()
        
        session = AssignmentSession.objects.get_by_worker(user)

    posted_session_id = request.POST.get('sessionId', None)
    result = request.POST.get('result', '')

    if session is not None and posted_session_id is not None:
        if unicode(session.pk) == posted_session_id:
            try:
                asstats, created = AssignmentSessionStats.objects.get_or_create(assignment_session=session,
                                mileage=None,
                                accuracy=None)

                session.close(StringIO(urllib.urlopen(result).read()))
                asstats.mileage = h_dip.count_foreground_pixels(session.result.path)

                asstats.save()
                
                wp.mileage_sum += asstats.mileage

                # Assign the score as if the accuracy were 1.0
                # The actual accuracy is accounted when the assignment is concluded.
                wp.score += asstats.mileage

                wp.save()
                
            except IOError:
                session.close()
                
            session.save()

            # If an assignment is concluded the accuracies of the sessions (workers)
            # must be computed using the assignment's merge image.
            # Hence, the users' score must be updated as well. 
            assignment = session.assignment
            if assignment.concluded:
                a_sessions = AssignmentSession.objects.get_w_result().filter(assignment=assignment)
                for a_session in a_sessions:
                    a_session.stats.update_accuracy()
                    a_session.stats.save()

                    wp = WorkerProfile.objects.get(user=a_session.worker)

                    # Score correction
                    wp.score -= a_session.stats.mileage
                    wp.score += a_session.stats.mileage*a_session.stats.accuracy

            session = AssignmentSession.objects.get_by_worker(user)

    if session is not None:
        assignment = session.assignment
        ret['sessionId'] = session.pk
        ret['assignmentId'] = assignment.pk
        ret['tileUrl'] = assignment.tile.url
        pre_seg = assignment.pre_seg
        if pre_seg:
            ret['preSegUrl'] = pre_seg.url
        preprocess = assignment.preprocess_file
        if preprocess:
            preprocess_data = SegmentationProblem.read_file(preprocess.path)
            ret['preprocessData'] = preprocess_data
        ret['tileBorder'] = session.assignment.seg_prob.details.tiles_border
        ret['algorithm'] = session.assignment.seg_prob.details.algorithm

    return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

@login_required
@user_passes_test(_check_if_worker)
def top_k(request, k):
    user = request.user

    ranking_keys = cache.get('ranking_keys')
    ranking_dict = cache.get('ranking_dict')

    if ranking_keys:
        ret = []
        user_in_topk = False
        counter = 1
        for key in ranking_keys:
            ret.append(ranking_dict[key])

            if user.id == key:
                user_in_topk = True

            if counter == int(k):
                break

            counter += 1

        if not user_in_topk:
            ret.append(ranking_dict[user.id])
    else:
        ret = None

    return HttpResponse(simplejson.dumps(ret), mimetype='application/json')
    #return render(request, 'crowd/workers/ranking.html', {'ranking_list': simplejson.dumps(ret)})
    #return render(request, 'crowd/workers/ranking.html', {'ranking_list': ret})

@login_required
@user_passes_test(_check_if_worker)
def index(request):
    return render(request, 'crowd/workers/index.html')

@login_required
@user_passes_test(_check_if_worker)
def ranking_index(request):
    return render(request, 'crowd/workers/ranking.html')


#definindo a pagina de profile inicial
def profile(request):
    return render(request, 'crowd/workers/profile.html')