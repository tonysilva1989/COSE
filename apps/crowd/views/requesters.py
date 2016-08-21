###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Views related to requesters in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render


def _check_if_requester(user):
    try:
        return user.get_profile().is_requester
    except:
        return False


@login_required
@user_passes_test(_check_if_requester)
def index(request):
    return render(request, 'crowd/requesters/index.html')
