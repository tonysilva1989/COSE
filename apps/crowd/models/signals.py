###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Signal handling for models in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =====================
# Python stdlib imports
# =====================

import logging

# ==============
# Django imports
# ==============

from django.contrib.auth import user_logged_out
from django.db.models.signals import post_delete, pre_save, pre_delete, \
    post_save
from django.dispatch.dispatcher import receiver

# ===============
# project imports
# ===============

import helpers

from crowd.models.assignment import AssignmentSession
from crowd.models.segprob import SegmentationProblem
from crowd.models.segprob import SegmentationProblemDetails
from crowd.models.task import Task
from crowd.models.task import TaskCategory
from helpers.django_related.signals import disable_for_loaddata


debug_logger = logging.getLogger('debug')


@receiver(post_delete, sender=SegmentationProblem,
    dispatch_uid='7b1cfbbd-09db-4a7d-a649-c91d0a57af28')
def _seg_prob_post_delete(sender, **kwargs):
    instance = kwargs['instance']
    helpers.filesystem.rm(instance.root_path, ignore_errors=True)
    debug_logger.debug('%s "%s" post delete triggered' % (sender.__name__,
                                                          instance))


@receiver(pre_save, sender=SegmentationProblemDetails,
    dispatch_uid='93e523ba-a09d-44d7-ba1f-baf453b36e9b')
@receiver(pre_delete, sender=SegmentationProblemDetails,
    dispatch_uid='4d9d2f45-d278-47ec-b311-37a703bf788f')
@disable_for_loaddata
def _seg_prob_details_pre_change(sender, **kwargs):
    instance = kwargs['instance']
    instance.seg_prob.clear_assignments()
    debug_logger.debug('%s "%s" pre change (pre_save | pre_delete) triggered' %
                       (sender.__name__, instance))


@receiver(pre_save, sender=Task,
    dispatch_uid='da4151d5-23ce-490b-b13d-ba4ab6e24156')
@receiver(pre_save, sender=TaskCategory,
    dispatch_uid='9230a094-c84f-46bb-b365-388b6f08fbc1')
@receiver(pre_save, sender=AssignmentSession,
    dispatch_uid='39bec173-c188-492c-9f02-3958e233783f')
@receiver(pre_save, sender=SegmentationProblemDetails,
    dispatch_uid='216ace28-915c-4b1d-bcc8-635d7c4f2175')
@disable_for_loaddata
def _force_full_clean_before_saving(sender, **kwargs):
    instance = kwargs['instance']
    instance.full_clean()
    debug_logger.debug('full clean forced for %s "%s"' %
                       (sender.__name__, instance))


@receiver(user_logged_out, dispatch_uid='062d9807-c809-4637-ac6f-f5c920b7f08c')
def _cancel_last_worker_session(sender, **kwargs):
    user = kwargs['user']
    if not user:
        return
    session = AssignmentSession.objects.get_by_worker(user)
    if session is not None:
        session.cancel()


@receiver(post_save, sender=AssignmentSession,
    dispatch_uid='77d49629-1034-4fac-b6ef-35239f38c348')
def _check_assignment_conclusion(sender, **kwargs):
    a_session = kwargs['instance']
    a = a_session.assignment
    if not a.concluded and a.n_sessions_until_conclusion == 0:
        a.concluded = True
        a.merge_results()
        a.save()
