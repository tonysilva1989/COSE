###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Forms for profiles app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# ==============
# Django imports
# ==============

from django import forms
from django.utils.translation import ugettext_lazy as _

# ================
# external imports
# ================

from registration.forms import RegistrationForm
from registration.signals import user_registered

# ===============
# project imports
# ===============

from profiles.models import RequesterProfile, WorkerProfile


class RegistrationForm(RegistrationForm):
    as_requester = forms.BooleanField(required=False, initial=False,
        label=_('As requester?'))


def _user_registered_handler(sender, user, request, **kwargs):
    form = RegistrationForm(request.POST)
    if 'as_requester' in form.data:
        profile = RequesterProfile(user=user)
    else:
        profile = WorkerProfile(user=user)
    profile.save()


user_registered.connect(_user_registered_handler)
