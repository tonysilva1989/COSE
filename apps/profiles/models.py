###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Models for profile app..
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################

# =============
# Python stdlib
# =============

from decimal import Decimal
import datetime

# ==============
# Django imports
# ==============

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import default

# ===============
# project imports
# ===============


class UserProfile(models.Model):
    # ================
    # model definition
    # ================

    user = models.OneToOneField(User, primary_key=True, verbose_name=_('user'),
        related_name='+')
    
    # Save last login. It's a walkaround to the last_login behavior when it's a saved session
    #last_seen_on = models.DateTimeField(null=False)

    class Meta:
        app_label = 'profiles'

    # ==========
    # properties
    # ==========

    @property
    def is_requester(self):
        return hasattr(self, 'requesterprofile')

    @property
    def is_worker(self):
        return hasattr(self, 'workerprofile')

    # ==================
    # overridden methods
    # ==================

    def __unicode__(self):
        return self.user.__unicode__()


class RequesterProfile(UserProfile):
    # ================
    # model definition
    # ================

    # TODO create some meaningful profile for Requesters. These are just dummy
    #      fields for testing purposes.
    account_balance = models.IntegerField(default=0)

    class Meta:
        app_label = 'profiles'

        verbose_name = _('requester profile')
        verbose_name_plural = _('requesters profiles')


class WorkerProfileManager(models.Manager):
    def all_ordered_by_score(self):
        """
        Return a RawQuery of all WorkerProfile's
        ordered by score.

        Each element of the RawQuery has the attributes
        userprofile_ptr_id and score.
        """

        sql_query_string = """
        SELECT user.username, wp.userprofile_ptr_id, wp.score, mileage_sum, accumulated_accuracy
        FROM profiles_workerprofile AS wp, auth_user AS user
        WHERE user.id = wp.userprofile_ptr_id
        ORDER BY score DESC;
        """

        return self.raw(sql_query_string)


    def penalize_by_time(self, now, allowed_inactive_time, penalty):
        for wp in self.all():
            if now - wp.last_time_worked > allowed_inactive_time:
                wp.score -= penalty


class WorkerProfile(UserProfile):
    """
    This model keeps the values needed to draw a worker profile.
    Its attributes values summarizes the overall performance of the worker.
    """
    
    # ================
    # model definition
    # ================

    # TODO create some meaningful profile for Workers. These are just dummy
    #      fields for testing purposes.
    score = models.PositiveIntegerField(default=0)
    
    # alpha' - value between 0 and 1 representing the overall worker accuracy.
    accumulated_accuracy = models.DecimalField(_('accuracy'), max_digits=6, decimal_places=5, default=Decimal('0'))
    
    # sum(Ti) - sum of marked pixels of all the tiles that worker has done. 
    # Ti is the number of pixels marked in the i-th tile.
    mileage_sum = models.PositiveIntegerField(_('mileage sum'), default=0)
    
    # Refers to last time the worker user worked.
    last_time_worked = models.DateTimeField(_('last time worked'), null=True)

    objects = WorkerProfileManager()

    @property
    def bonus_points(self):
        pass
    
    @property
    def time_factor(self):
        pass
    
    @property
    def ranking_position(self):
        pass

    class Meta:
        app_label = 'profiles'

        verbose_name = _('worker profile')
        verbose_name_plural = _('workers profiles')
