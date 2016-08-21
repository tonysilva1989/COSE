###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Models related to tasks in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# ==============
# Django imports
# ==============

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class TaskCategory(models.Model):
    # ================
    # model definition
    # ================

    title = models.CharField(_('title'), max_length=30)
    description = models.CharField(_('description'), max_length=300)
    parent = models.ForeignKey('self', verbose_name=_('parent'), null=True,
        blank=True)

    class Meta:
        app_label = 'crowd'

        verbose_name = _('task category')
        verbose_name_plural = _('task categories')

        unique_together = ('title', 'parent')

    # ==================
    # overridden methods
    # ==================

    def clean(self):
        # NOTE for some obscure reason, the database backend does not enforce
        #      the unique_together meta when one of the fields is null. For
        #      this reason, it's necessary to enforce this validation
        #      independently of the database.
        #      * This is code duplication, so it's NOT good. *
        # TODO check if this shouldn't be handled in Model.validate_unique

        qs = TaskCategory.objects.exclude(pk=self.pk).filter(title=self.title,
            parent=self.parent)
        if qs.count() > 0:
            raise ValidationError(
                self.unique_error_message(TaskCategory, ('title', 'parent')))

    def __unicode__(self):
        MAX_PARENTS_TO_CONSIDER = 3

        titles = [self.title]
        for idx, parent in enumerate(self.get_parents()):
            if idx >= MAX_PARENTS_TO_CONSIDER:
                titles.append(u'...')
                break
            titles.append(parent.title)
        return u' / '.join(reversed(titles))

    # ==============
    # public methods
    # ==============

    def get_parents(self):
        """
        Returns an iterator for the parents hierarchy of this task category.

        WARNING: each iteration implies a database hit, so be careful when
        using it.
        """

        curr_parent = self.parent
        while curr_parent is not None:
            yield curr_parent
            curr_parent = curr_parent.parent


class Task(models.Model):
    # ================
    # model definition
    # ================

    title = models.CharField(_('title'), max_length=50)
    description = models.TextField(_('description'))
    category = models.ForeignKey(TaskCategory, verbose_name=_('category'),
        related_name='tasks', on_delete=models.PROTECT)
    notes_for_staff = models.TextField(_('notes for staff'), blank=True)

    created_on = models.DateTimeField(_('created on'), editable=False)

    owner = models.ForeignKey(User, verbose_name=_('owner'),
        related_name='tasks', editable=False)

    class Meta:
        app_label = 'crowd'

        verbose_name = _('task')
        verbose_name_plural = _('tasks')

        get_latest_by = 'created_on'
        unique_together = ('title', 'category')

    # ==================
    # overridden methods
    # ==================

    def clean(self):
        qs = Task.objects.filter(pk=self.pk)
        if not qs.count() > 0:
            self.created_on = timezone.now()

    def __unicode__(self):
        return self.title
