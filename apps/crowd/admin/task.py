###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Django admin configuration for crowd.models.task models.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# ==============
# Django imports
# ==============

from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Count
from django.utils.html import linebreaks, escape
from django.utils.text import truncate_words
from django.utils.translation import ugettext_lazy as _

# ===============
# project imports
# ===============

from crowd.models.task import TaskCategory
from crowd.models.task import Task
from crowd.models.segprob import SegmentationProblem
from helpers import decorators as h_decs
from helpers.django_related import templates as h_tmpl


# =================
# utility functions
# =================

def _truncated_description_fun(max_words_allowed=10):
    fun = lambda o: truncate_words(o.description, max_words_allowed)
    fun.short_description = _('description')
    return fun


# ==========================================
# Admin configuration for TaskCategory model
# ==========================================

class TaskCategoryAdminForm(forms.models.ModelForm):
    class Meta:
        model = TaskCategory
        widgets = {
            'description': forms.widgets.Textarea
        }


class TaskInlineAdmin(admin.TabularInline):
    # =============
    # configuration
    # =============

    model = Task
    template = 'admin/inlines/tabular_wo_header.html'
    fields = ('_title', _truncated_description_fun(), 'created_on')
    readonly_fields = fields
    ordering = ('-created_on',)
    max_num = 0
    can_delete = False

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('title'), allow_tags=True)
    def _title(self, obj):
        url = reverse('admin:crowd_task_change', args=(obj.pk,))
        return h_tmpl.render_link(url, obj.title)


class TaskCategoryAdmin(admin.ModelAdmin):
    # =============
    # configuration
    # =============

    list_display = ('title', 'parent', _truncated_description_fun(),
                    '_n_tasks')
    search_fields = ('title', 'description')
    ordering = ('parent', 'title')

    form = TaskCategoryAdminForm
    inlines = (TaskInlineAdmin,)

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('no. of tasks'),
        admin_order_field='n_tasks')
    def _n_tasks(self, obj):
        return obj.n_tasks

    # ==================
    # overridden methods
    # ==================

    def queryset(self, request):
        return TaskCategory.objects.annotate(n_tasks=Count('tasks'))


# ==================================
# Admin configuration for Task model
# ==================================

class ViewSegmentationProblemInlineAdmin(admin.TabularInline):
    # =============
    # configuration
    # =============

    model = SegmentationProblem
    fields = ('_preview', '_notes_for_staff', '_has_assignments', 'published')
    readonly_fields = fields
    ordering = ('id',)
    max_num = 0

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('preview'), allow_tags=True)
    def _preview(self, obj):
        url = reverse('admin:crowd_segmentationproblem_change', args=(obj.pk,))
        thumb_src = getattr(obj.image, 'url_%dx%d' % obj.THUMB_SIZES['small'])
        return h_tmpl.render_linked_img(url, thumb_src)

    @h_decs.annotate(short_description=_('notes for staff'), allow_tags=True)
    def _notes_for_staff(self, obj):
        return linebreaks(escape(obj.notes_for_staff))

    @h_decs.annotate(short_description=_('has assignments?'),
        boolean=True)
    def _has_assignments(self, obj):
        return obj.has_assignments


class AddSegmentationProblemInlineAdmin(admin.TabularInline):
    # =============
    # configuration
    # =============

    model = SegmentationProblem
    fields = ('image', 'notes_for_staff')
    extra = 0
    max_num = None
    can_delete = False

    # ==================
    # overridden methods
    # ==================

    def queryset(self, request):
        return SegmentationProblem.objects.none()


class TaskAdmin(admin.ModelAdmin):
    # =============
    # configuration
    # =============

    list_display = ('title', _truncated_description_fun(max_words_allowed=10),
                    'category', 'created_on', '_owner')
    list_filter = ('owner', 'category')
    search_fields = ('title', 'description', 'category')
    date_hierarchy = 'created_on'
    ordering = ('-created_on',)

    # IMPL_DETAIL segmentation problems cannot change after creation. So,
    #             the inline for segmentation problems must provide just a view
    #             of the existing instances, without allowing changes. At the
    #             same time, new segmentation problems should be allowed to be
    #             added. Although this requirement could be implemented with
    #             just one inline, the complexity would not be justified for an
    #             admin front-end. Thus, the most practical solution is to
    #             create two inlines for the same model, each configured so as
    #             to achieve the desired behavior. This is not elegant, but
    #             does the job.
    inlines = (ViewSegmentationProblemInlineAdmin,
               AddSegmentationProblemInlineAdmin)

    fields = ('title', 'description', 'category', 'notes_for_staff',
              'created_on', '_owner')
    readonly_fields = ('created_on', '_owner')

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('owner'), admin_order_field='owner',
        allow_tags=True)
    def _owner(self, obj):
        url = reverse('admin:auth_user_change', args=(obj.owner.pk,))
        return h_tmpl.render_link(url, obj.owner)

    # ==================
    # overridden methods
    # ==================

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return TaskAdmin.readonly_fields
        return TaskAdmin.readonly_fields + ('title', 'category')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        obj.save()


# ===================================
# Registration of models in Admin app
# ===================================

admin.site.register(TaskCategory, TaskCategoryAdmin)
admin.site.register(Task, TaskAdmin)
