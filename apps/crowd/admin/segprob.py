###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Django admin configuration for crowd.models.segprob models.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# ==============
# Django imports
# ==============

from django.conf.urls import patterns, url
from django.contrib import admin, messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.html import escape, linebreaks
from django.utils.translation import ugettext_lazy as _

# ===============
# project imports
# ===============

from crowd.models.segprob import SegmentationProblem
from crowd.models.segprob import SegmentationProblemDetails
from helpers import decorators as h_decs
from helpers.django_related import templates as h_tmpl

from PIL import Image


# =================================================
# Admin configuration for SegmentationProblem model
# =================================================

class SegmentationProblemDetailsInlineAdmin(admin.StackedInline):
    model = SegmentationProblemDetails
    template = 'admin/crowd/segmentationproblemdetails/inline.html'
    fields = ('algorithm', 'pre_seg',
              ('tiles_dimension', 'tiles_overlap', 'tiles_border'),
              'min_results_per_assignment',
              'assignments_timeout')


class SegmentationProblemAdmin(admin.ModelAdmin):
    # =============
    # configuration
    # =============

    list_display = ('id', '_medium_preview', '_has_details',
                    '_has_assignments', 'published', '_task')
    list_editable = ('published',)
    list_display_links = ('_medium_preview',)
    list_filter = ('task', 'published')
    ordering = ('-id',)
    actions = ('_create_assignments_action', '_clear_assignments_action', '_publish_action', '_unpublish_action')

    fieldsets = (
        (None, {
            'fields': ('id', '_large_preview', '_task')
        }),
        (_('Status'), {
            'fields': ('_has_details', '_assignments', '_result', 'published')
        }),
        (_('Notes for staff'), {
            'fields': ('_seg_prob_notes_for_staff', '_task_notes_for_staff'),
            'classes': ('collapse',)
        })
        )
    readonly_fields = ('id', '_large_preview', '_task', '_has_details',
                       '_result', '_assignments', '_seg_prob_notes_for_staff',
                       '_task_notes_for_staff')
    save_on_top = True
    inlines = (SegmentationProblemDetailsInlineAdmin,)

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('preview'), allow_tags=True)
    def _medium_preview(self, obj):
        return h_tmpl.render_img(obj.get_img_thumb_url('medium'))

    @h_decs.annotate(short_description=_('has details?'), boolean=True)
    def _has_details(self, obj):
        return obj.has_details

    @h_decs.annotate(short_description=_('has assignments?'), boolean=True)
    def _has_assignments(self, obj):
        return obj.has_assignments

    @h_decs.annotate(short_description=_('task'),
        admin_order_field='task__created_on', allow_tags=True)
    def _task(self, obj):
        url = reverse('admin:crowd_task_change', args=(obj.task.pk,))
        return h_tmpl.render_link(url, obj.task)

    @h_decs.annotate(short_description=_('preview'), allow_tags=True)
    def _large_preview(self, obj):
        return h_tmpl.render_linked_img(obj.image.url,
            obj.get_img_thumb_url('large'), link_attrs={'target': '_blank'})

    @h_decs.annotate(short_description=_("assignments"), allow_tags=True)
    def _assignments(self, obj):
        if obj.has_assignments:
            chg_lst_url = reverse('admin:crowd_assignment_changelist')
            chg_lst_url = '%s?seg_prob__id__exact=%d' % (chg_lst_url, obj.pk)
            chg_lst_link = h_tmpl.render_link(chg_lst_url,
                _('%d assignment(s)') % obj.assignments.count())

            clear_url = reverse(
                'admin:crowd_segmentationproblem_clearassignments',
                args=(obj.pk,))
            clear_link = h_tmpl.render_link(clear_url, _('clear'))

            return '%s (%s)' % (chg_lst_link, clear_link)
        elif obj.has_details:
            return h_tmpl.render_link(
                reverse('admin:crowd_segmentationproblem_createassignments',
                    args=(obj.pk,)), _('Create'))
        else:
            return _('None')

    @h_decs.annotate(short_description=_('result'), allow_tags=True)
    def _result(self, obj):
        if obj.has_assignments:
            url = reverse(
                'admin:crowd_segmentationproblem_mergeassignments_overlay',
                args=(obj.pk,))
            url_wo_overlay = reverse(
                'admin:crowd_segmentationproblem_mergeassignments',
                args=(obj.pk,))
            link = h_tmpl.render_link(url, _('Merge assignments'),
                {'target': '_blank'})
            link_wo_overlay = h_tmpl.render_link(url_wo_overlay,
                _('wo/ overlay'), {'target': '_blank'})
            return '%s (%s)' % (link, link_wo_overlay)
        return _('N/A')

    @h_decs.annotate(short_description=_('from seg. prob.'), allow_tags=True)
    def _seg_prob_notes_for_staff(self, obj):
        return linebreaks(escape(obj.notes_for_staff))

    @h_decs.annotate(short_description=_("from task"), allow_tags=True)
    def _task_notes_for_staff(self, obj):
        return linebreaks(escape(obj.task.notes_for_staff))

    # =======
    # actions
    # =======

    @h_decs.annotate(short_description=_('Create assignments'))
    def _create_assignments_action(self, request, queryset):
        for p in queryset:
            if p.has_assignments:
                messages.warning(request, _('Seg. prob. %(id)d has '
                                            'assignments already.') % {
                    'id': p.id})
            elif p.has_details:
                p.create_assignments()
                if p.has_assignments:
                    messages.success(request, _('Assignments for seg. prob. '
                                                '%(id)d were created.') % {
                        'id': p.id})
                else:
                    messages.error(request, _('Internal error during '
                                              'assignments creation for seg. '
                                              'prob. %(id)d.') % {'id': p.id})
            else:
                messages.warning(request, _('Details for seg. prob. %(id)d '
                                            'are lacking.') % {'id': p.id})

    @h_decs.annotate(short_description=_('Clear assignments'))
    def _clear_assignments_action(self, request, queryset):
        for p in queryset:
            if p.has_assignments:
                p.clear_assignments()
                if p.has_assignments:
                    messages.error(request, _('Internal error during '
                                              'assignments clearing for seg. '
                                              'prob. %(id)d.') % {'id': p.id})
                else:
                    messages.success(request, _('Assignments for seg. prob. '
                                                '%(id)d were cleared.') % {
                        'id': p.id})
            else:
                messages.warning(request, _('Seg. prob. %(id)d doesn\'t '
                                            'have any assignment.') % {
                    'id': p.id})
    
    @h_decs.annotate(short_description=_('Publish'))
    def _publish_action(self, request, queryset):
        queryset.update(published=True)
    
    @h_decs.annotate(short_description=_('Unpublish'))
    def _unpublish_action(self, request, queryset):
        queryset.update(published=False)

    # ============
    # custom views
    # ============

    def _assignments_handling_view(self, request, pk, create=True):
        queryset = SegmentationProblem.objects.filter(pk=pk)
        if create:
            self._create_assignments_action(request, queryset)
        else:
            self._clear_assignments_action(request, queryset)
        return HttpResponseRedirect(request.GET.get('next',
            reverse('admin:crowd_segmentationproblem_change', args=(pk,))))

    def _merge_assignments_view(self, request, pk, overlay=False):
        seg_prob = get_object_or_404(SegmentationProblem, pk=pk)
        merge = seg_prob.merge_assignments()
        if merge:
            if overlay:
                ret = Image.open(seg_prob.image.path).convert('RGBA')
                ret.paste((255, 0, 0), None, merge)
            else:
                ret = merge
            response = HttpResponse(content_type='image/png')
            ret.save(response, format='PNG')
            return response
        raise Http404

    # ==================
    # overridden methods
    # ==================

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        assignments_handling_view = self.admin_site.admin_view(
            self._assignments_handling_view)
        merge_assignments_view = self.admin_site.admin_view(
            self._merge_assignments_view)

        custom_urls = patterns('',
            url(r'^(?P<pk>\d+)/create_assignments/$',
                assignments_handling_view,
                name='crowd_segmentationproblem_createassignments'),
            url(r'^(?P<pk>\d+)/clear_assignments/$',
                assignments_handling_view, {'create': False},
                name='crowd_segmentationproblem_clearassignments'),

            url(r'^(?P<pk>\d+)/merge_assignments/overlay/$',
                merge_assignments_view, {'overlay': True},
                'crowd_segmentationproblem_mergeassignments_overlay')
            ,
            url(r'^(?P<pk>\d+)/merge_assignments/$', merge_assignments_view,
                name='crowd_segmentationproblem_mergeassignments')
        )

        return custom_urls + super(SegmentationProblemAdmin, self).get_urls()


# ===================================
# Registration of models in Admin app
# ===================================

admin.site.register(SegmentationProblem, SegmentationProblemAdmin)
