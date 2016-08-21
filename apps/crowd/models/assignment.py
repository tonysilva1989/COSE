###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Models related to assignments in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =====================
# Python stdlib imports
# =====================

import datetime
import os
import math

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

# ==============
# Django imports
# ==============

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# ================
# external imports
# ================

from PIL import Image
import fmetrics as fm

# ===============
# project imports
# ===============

import externals

from crowd.models.exceptions import InvalidStateError
from crowd.models.segprob import SegmentationProblem
from helpers import decorators as h_decs
from helpers import dip as h_dip
from helpers.django_related.models import get_db_datetime_now,\
    get_db_column, CountIf


class AssignmentManager(models.Manager):
    def get_public(self):
        return self.filter(workable=True, seg_prob__published=True)

    def get_available(self):
        """
        This method returns the available assignments
        
        Available assignments satisfy the following condition: n_active_sessions < n_sessions_until_conclusion
        """  
              
        active_cond = '(%(expiration_deadline)s >= "%(now)s" AND '\
                      '%(close_time)s IS NULL)' % {
                          'expiration_deadline': get_db_column(
                              AssignmentSession,
                              'expiration_deadline'),
                          'now': get_db_datetime_now(self.db),
                          'close_time': get_db_column(AssignmentSession,
                              'close_time')
                      }
                      
        w_result = "%(result)s <> ''" % {'result': get_db_column(AssignmentSession, 'result')}      
        
        not_concluded_assigns = self.get_public().filter(concluded=False)
        
        #Annotate with active_sess and w_result_sess
        annotated_assigns = not_concluded_assigns.annotate(
            active_sess=CountIf('sessions', condition=active_cond), 
            w_result_sess=CountIf('sessions', condition=w_result)).select_related(
            'seg_prob__details__min_results_per_assignment')
            
        #Filter n_active_sessions < n_sessions_until_conclusion
        available_assigns = annotated_assigns.filter(
            active_sess__lt=F('seg_prob__details__min_results_per_assignment') - F('w_result_sess'))
    
        return available_assigns

    def enforce_concluded(self):
        self.update(concluded=False)
        has_result_cond = '(%(result)s <> "")' % {
            'result': get_db_column(AssignmentSession, 'result')
        }
        active_cond = '(%(expiration_deadline)s >= "%(now)s" AND '\
                      '%(close_time)s IS NULL)' % {
                          'expiration_deadline': get_db_column(
                              AssignmentSession,
                              'expiration_deadline'),
                          'now': get_db_datetime_now(self.db),
                          'close_time': get_db_column(AssignmentSession,
                              'close_time')
                      }
        valid_sessions_cond = '(%s OR %s)' % (has_result_cond, active_cond)

        concluded = self.get_public().annotate(n_sessions=CountIf('sessions',
            condition=valid_sessions_cond)).select_related(
            'seg_prob__details__min_results_per_assignment').filter(
            n_sessions__ge=F('seg_prob__details__min_results_per_assignment'))
        for a in concluded:
            a.concluded = True
            a.save()



class Assignment(models.Model):
    # ===============
    # class variables
    # ===============

    THUMB_SIZES = {
        'small': (50, 50),
        'medium': (100, 100),
        'large': (150, 150)
    }
    # ===============
    # private methods
    # ===============

    def _img_upload_to_fun(self, filename):
        return os.path.join(self.seg_prob.assignments_root_rel_path, filename)

    # ================
    # model definition
    # ================

    seg_prob = models.ForeignKey(SegmentationProblem,
        verbose_name=_('seg. problem'), related_name='assignments',
        editable=False)

    merge = models.ImageField(_('merge'), max_length=255,
        upload_to=_img_upload_to_fun, editable=False, null=True)

    # merge_thumbnail = externals.thumbs.ImageWithThumbsField(
    #     _('merge'), max_length=255, upload_to=_img_upload_to_fun,
    #     editable=False, null=True, sizes=THUMB_SIZES.values())
    
    # TODO change this to PreProcessImageField (w/ thumbnails)
    tile = externals.thumbs.ImageWithThumbsField(_('tile'),
        upload_to=_img_upload_to_fun, sizes=THUMB_SIZES.values(),
        editable=False)
    tile_bbox_x0 = models.PositiveIntegerField(
        _('tile bbox.x0'), editable=False)
    tile_bbox_y0 = models.PositiveIntegerField(
        _('tile bbox.y0'), editable=False)
    tile_bbox_x1 = models.PositiveIntegerField(
        _('tile bbox.x1'), editable=False)
    tile_bbox_y1 = models.PositiveIntegerField(
        _('tile bbox.y1'), editable=False)

    # TODO change this to PreProcessImageField
    pre_seg = models.ImageField(_('pre seg.'), max_length=255,
        upload_to=_img_upload_to_fun, blank=True, editable=False)

    preprocess_file = models.FileField(_('pre process'), max_length=255,
        upload_to=_img_upload_to_fun, null=True)

    workable = models.NullBooleanField(_('workable?'), null=True, default=True)
    concluded = models.BooleanField(_('concluded?'), default=False,
        editable=False)

    objects = AssignmentManager()

    class Meta:
        app_label = 'crowd'

        verbose_name = _('assignment')
        verbose_name_plural = _('assignments')
        unique_together = ('seg_prob', 'tile')

    # ==========
    # properties
    # ==========

    @property
    def n_sessions_until_conclusion(self):
        """The minimum number of sessions that must be created in order to
        complete this assignment."""
        return max(0, self.seg_prob.details.min_results_per_assignment -\
                      self.n_sessions_w_result)

    @property
    def n_active_sessions(self):
        return self.sessions.get_active().count()

    def n_expired_sessions(self):
        return self.sessions.get_expired().count()

    @property
    def n_skipped_sessions(self):
        return self.sessions.get_skipped().count()

    @property
    def n_sessions_w_result(self):
        return self.sessions.get_w_result().count()

    @property
    def has_results(self):
        return self.n_sessions_w_result > 0

    @property
    def has_merge(self):
        ret = False
        if self.merge:
            ret = True
        return ret

    # ==================
    # overridden methods
    # ==================

    def __unicode__(self):
        return u'%s %d of %s' % (self._meta.verbose_name, self.pk,
                                 self.seg_prob)

    # ==============
    # public methods
    # ==============

    def get_tile_thumb_url(self, size):
        return getattr(self.tile, 'url_%dx%d' % self.THUMB_SIZES[size])

    def merge_results(self):
        finished = self.sessions.get_w_result()
        merge = None
        alpha = float(2.0)
        
        try:
            merge = h_dip.merge_masks([s.result.path for s in finished], alpha)
        except:
            #TODO log this error as a inconsistency problem: 
            #number of masks is not equal to the number o sessions with results
            pass

        # merge_skel = Image.fromarray(merge['merge_skel']) if merge else None
        merge_skel = Image.fromarray(merge['merge']) if merge else None

        if not self.merge and merge_skel is not None:
            tile_filename = os.path.splitext(os.path.split(self.tile.name)[1])[0]
            merge_filename = '%s_merge.png' % (tile_filename)

            output = StringIO()
            merge_skel.save(output, format='PNG')
            self.merge.save(merge_filename, ContentFile(output.getvalue()))

        return merge_skel



class AssignmentSessionManager(models.Manager):
    def get_by_worker(self, worker):
        # Return any session already open for that user.
        # If there is an old session which has not expired but had
        # its segmentation problem turned to unpublished, it must be closed.
        try:
            public_session = self.get(worker=worker, close_time__isnull=True, assignment__seg_prob__published=True)
            return public_session
        except AssignmentSession.DoesNotExist:
            try:
                old_session = self.get(worker=worker, close_time__isnull=True)
                old_session.close()
                old_session.save()
            except AssignmentSession.DoesNotExist:
                pass

        # get any pending assignment excluding those in which the user already
        # worked on, ordering by task creation date
        assignments = Assignment.objects.get_available().exclude(
            sessions__worker=worker).order_by('seg_prob__id', 'id')
        if assignments.count():
            #myass = random.choice(assignments[0:40])
            return self.create(assignment=assignments[0], worker=worker)
        
        return None

    def get_active(self):
        return self.filter(close_time__isnull=True,
            expiration_deadline__gte=timezone.now())

    def get_expired(self):
        # those sessions whose expiration deadlines are in the past respective
        # to now (if it's still open) or to the close_time
        return self.filter(
            Q(close_time__isnull=True,
                expiration_deadline__lt=timezone.now()) |\
            Q(close_time__isnull=False,
                expiration_deadline__lt=F('close_time')))

    def get_skipped(self):
        # those sessions that were closed no later than the expiration deadline
        # without results
        return self.filter(close_time__isnull=False,
            close_time__lte=F('expiration_deadline'), result='')

    def get_w_result(self):
        return self.filter(~Q(result=''))

    def n_sessions_expired_for(self, user):
        return self.get_expired().filter(worker=user).count()

    def n_sessions_skipped_by(self, user):
        return self.get_skipped().filter(worker=user).count()


class AssignmentSession(models.Model):
    # ===============
    # private methods
    # ===============

    def _result_upload_to_fun(self, filename):
        return '%s_session_%d.png' % (os.path.splitext(
            self.assignment.tile.name)[0], self.pk)

    def _preprocess_result(self, result):
        dim = self.assignment.seg_prob.details.tiles_dimension
        output = StringIO()
        Image.open(result).resize((dim, dim)).split()[-1].point(
            lambda u: 255 if u > 0 else 0).save(output, format='PNG')
        return ContentFile(output.getvalue())

    # ================
    # model definition
    # ================

    assignment = models.ForeignKey(Assignment, verbose_name=_('assignment'),
        editable=False, related_name='sessions')

    start_time = models.DateTimeField(_('start time'), editable=False)
    close_time = models.DateTimeField(_('close time'), null=True, blank=True,
        editable=False)

    expiration_deadline = models.DateTimeField(_('expiration deadline'),
        editable=False)

    # TODO change this to PreProcessImageField
    result = models.ImageField(_('result'), max_length=255,
        upload_to=_result_upload_to_fun, blank=True, editable=False)

    # result_thumbnail = externals.thumbs.ImageWithThumbsField(
    #     _('result'), max_length=255, upload_to=_result_upload_to_fun,
    #     blank=True, editable=False, sizes=THUMB_SIZES.values())

    worker = models.ForeignKey(User, verbose_name=_('worker'),
        related_name='assignments_sessions', editable=False)

    objects = AssignmentSessionManager()

    class Meta:
        app_label = 'crowd'

    # ==========
    # properties
    # ==========

    @property
    def timeout(self):
        return self.expiration_deadline - self.start_time

    @property
    def elapsed_time(self):
        """Amount of time this session remain(s|ed) opened."""
        return (self.close_time or timezone.now()) - self.start_time

    @property
    def remaining_time(self):
        """Remaining time until expiration."""
        return max(self.expiration_deadline - timezone.now(),
            datetime.timedelta(0))

    @property
    def closed(self):
        return self.close_time is not None

    @property
    def expired(self):
        return self.elapsed_time > self.timeout

    @property
    def active(self):
        return not self.closed and not self.expired

    @property
    def skipped(self):
        """Is session closed no later than the expiration deadline without
        results?"""
        return self.closed and not self.expired and not self.has_result

    @property
    def has_result(self):
        return self.result

    # ==================
    # overridden methods
    # ==================

    @h_decs.annotate(alters_data=True)
    def clean(self):
        # this guarantees that a user cannot work on two sessions at the same
        # time
        worker_busy_already = AssignmentSession.objects.exclude(
            pk=self.pk).filter(worker=self.worker,
            close_time__isnull=True).count() > 0
        if worker_busy_already:
            raise ValidationError(_('The worker assigned for this session '
                                    'already has another one opened.'))

        # if the session is not closed, but somehow there's a result attached,
        # throw a validation error
        if not self.closed and self.has_result:
            raise ValidationError(_('This session has associated result but '
                                    'it\'s not closed.'))

        if AssignmentSession.objects.filter(pk=self.pk).exists():
            # close this session if it's open but expired
            if not self.closed and self.expired:
                self.close()
        else:
            timeout = self.assignment.seg_prob.details.assignments_timeout
            self.start_time = timezone.now()
            self.expiration_deadline = self.start_time +\
                                       datetime.timedelta(seconds=timeout)

    def __unicode__(self):
        return u'Session for assignment #%d - Remaining: %s' %\
               (self.assignment.id, self.remaining_time)

    # ==============
    # public methods
    # ==============

    @h_decs.annotate(alters_data=True)
    def close(self, result=None):
        if self.closed:
            raise InvalidStateError(_('This session is already closed.'))
        self.close_time = timezone.now()
        if not self.expired and result is not None:
            self.result.save('', self._preprocess_result(result),
                save=False)

    @h_decs.annotate(alters_data=True)
    def cancel(self):
        if self.active:
            self.delete()
            
class AssignmentSessionStatsManager(models.Manager):
    def get_by_worker(self, worker):
        return self.filter(assignment_session__worker=worker)
    
    def get_by_assignment(self, assignment):
        return self.filter(assignment_session__assignment__id=assignment)
#    @h_decs.annotate(alters_data=True)
#    def update_accuracy_by_assignment(self, assignment):
#        sessions = AssignmentSession.objects.filter(assignment=assignment)
#        if assignment.has_result():
#            rads = range(2,10)
#            n_radii = len(rads)
#            workers = set()
#            for s in sessions:
#                metrics = fm.fmeasure(assignment.merge.path, [asession.result.path], rads)
#                sum = 0
#                for radius in metrics[0]:
#                    sum = sum + radius[2]
#                accuracy = sum/n_radii
#                    
#                if math.isnan(accuracy):
#                    accuracy = None
#                    
#                s.stats.accuracy = accuracy
#                s.save()
#                workers.add(s.worker)
#                
#        return list(workers)
                
    

class AssignmentSessionStats(models.Model):
    """
    This model keeps the values of mileage and 
    accuracy for a given session.
    """
    
    # ================
    # model definition
    # ================
    assignment_session = models.OneToOneField(AssignmentSession, related_name='stats', editable=False, null=False)
    
    # Number of points marked in the related assignment.
    mileage = models.PositiveIntegerField(_('mileage'), null=True)
    
    # Value between 0 and 1 representing the worker 
    # accuracy for the related assignment. 
    accuracy = models.DecimalField(_('accuracy'), max_digits=6, decimal_places=5, null=True)
    
    objects = AssignmentSessionStatsManager()
    
    class Meta:
        app_label = 'crowd'
       
    #def update_mileage(self, image_content):
     #   self.mileage = h_dip.count_foreground_pixels(image_content)
       
    def update_accuracy(self):
        rads = range(2,10)
        n_radii = len(rads)
        
        metrics = fm.fmeasure(self.assignment_session.assignment.merge.path
                              , [self.assignment_session.result.path], rads)
        sum = 0
        for radius in metrics[0]:
            sum = sum + radius[2]
        accuracy = sum/n_radii
            
        if math.isnan(accuracy):
            accuracy = 0
            
        self.accuracy = accuracy
