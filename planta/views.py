###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## planta project common views.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render


def index(request):
    if request.user.is_authenticated():
        user_profile = None
        try:
            user_profile = request.user.get_profile()
        except:
            pass

        if user_profile:
            if user_profile.is_requester:
                redirect_url = reverse('crowd:requesters_index')
            else:
                redirect_url = reverse('crowd:workers_index')

            return HttpResponseRedirect(redirect_url)

    return HttpResponseRedirect(reverse('auth_login'))


def about(request):
    return render(request, 'about.html')

def help(request):
    return render(request, 'help.html')