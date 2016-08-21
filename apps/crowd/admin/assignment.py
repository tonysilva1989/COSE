###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Django admin configuration for crowd.models.assignment models.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# ==============
# Django imports
# ==============

from django.conf.urls import patterns, url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

# ================
# external imports
# ================

from PIL import Image

# ===============
# project imports
# ===============

from crowd.models.assignment import Assignment
from crowd.models.assignment import AssignmentSession
from helpers import decorators as h_decs
from helpers.django_related import templates as h_tmpl


# ========================================
# Admin configuration for Assignment model
# ========================================

class AssignmentAdmin(admin.ModelAdmin):
    # =============
    # configuration
    # =============

    list_display = ('id', '_medium_preview', 'workable', '_sessions',
                    'concluded', '_result', '_seg_prob', '_task')
    list_display_links = ('_medium_preview',)
    list_editable = ('workable',)
    list_filter = ('workable', 'concluded', 'seg_prob__task', 'seg_prob')
    ordering = ('-id',)
    actions = ('_mark_as_workable_action', '_mark_as_non_workable_action')

    fieldsets = (
        (None, {
            'fields': ('id', ('_large_preview', 'workable'), '_seg_prob',
                       '_sessions', '_pre_seg', '_result')
        }),
        (_('Stats'), {
            'fields': ('_n_sessions_until_conclusion', '_n_active_sessions',
                       '_n_skipped_sessions', '_n_sessions_w_result')
        })
        )
    readonly_fields = ('id', '_large_preview', '_seg_prob', '_sessions',
                       '_result', '_pre_seg', '_n_sessions_until_conclusion',
                       '_n_active_sessions', '_n_skipped_sessions',
                       '_n_sessions_w_result')

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('preview'), allow_tags=True)
    def _medium_preview(self, obj):
        return h_tmpl.render_img(obj.get_tile_thumb_url('medium'))

    @h_decs.annotate(short_description=_('task'),
        admin_order_field='seg_prob__task__created_on', allow_tags=True)
    def _task(self, obj):
        task_pk = obj.seg_prob.task.pk
        url = reverse('admin:crowd_task_change', args=(task_pk,))
        return h_tmpl.render_link(url, obj.seg_prob.task)

    @h_decs.annotate(short_description=_('segmentation problem'),
        admin_order_field='id', allow_tags=True)
    def _seg_prob(self, obj):
        url = reverse('admin:crowd_segmentationproblem_change',
            args=(obj.seg_prob.pk,))
        thumb_src = getattr(obj.seg_prob.image,
            'url_%dx%d' % obj.seg_prob.THUMB_SIZES['medium'])
        return h_tmpl.render_linked_img(url, thumb_src)

    @h_decs.annotate(short_description=_('sessions'), allow_tags=True)
    def _sessions(self, obj):
        n_sessions = obj.sessions.count()
        if n_sessions > 0:
            chg_lst_url = reverse('admin:crowd_assignmentsession_changelist')
            chg_lst_url = '%s?assignment__id__exact=%d' % (chg_lst_url, obj.pk)
            chg_lst_link = h_tmpl.render_link(chg_lst_url,
                _('%d sessions(s)') % n_sessions)
            return chg_lst_link
        return _('N/A')

    @h_decs.annotate(short_description=_('Pre seg.'), allow_tags=True)
    def _pre_seg(self, obj):
        if obj.pre_seg:
            return h_tmpl.render_link(obj.pre_seg.url, _('See'),
                    {'target': '_blank'})
        return _('N/A')

    @h_decs.annotate(short_description=_('result'), allow_tags=True)
    def _result(self, obj):
        if obj.has_results > 0:
            url = reverse('admin:crowd_assignment_mergeresults_overlay',
                args=(obj.pk,))
            url_wo_overlay = reverse('admin:crowd_assignment_mergeresults',
                args=(obj.pk,))
            link = h_tmpl.render_link(url, _('Merge from %d session(s)') %
                                           obj.n_sessions_w_result,
                    {'target': '_blank'})
            link_wo_overlay = h_tmpl.render_link(url_wo_overlay,
                _('wo/ overlay'), {'target': '_blank'})
            return '%s (%s)' % (link, link_wo_overlay)
        return _('N/A')

    @h_decs.annotate(short_description=_('preview'), allow_tags=True)
    def _large_preview(self, obj):
        return h_tmpl.render_linked_img(obj.tile.url,
            obj.get_tile_thumb_url('large'))

    @h_decs.annotate(short_description=_('# sessions until conclusion'))
    def _n_sessions_until_conclusion(self, obj):
        return obj.n_sessions_until_conclusion

    @h_decs.annotate(short_description=_('# active sessions'))
    def _n_active_sessions(self, obj):
        return obj.n_active_sessions

    @h_decs.annotate(short_description=_('# skipped sessions'))
    def _n_skipped_sessions(self, obj):
        return obj.n_skipped_sessions

    @h_decs.annotate(short_description=_('# sessions w/ result'))
    def _n_sessions_w_result(self, obj):
        return obj.n_sessions_w_result

    # =======
    # actions
    # =======

    @h_decs.annotate(short_description=_('Mark as workable'))
    def _mark_as_workable_action(self, request, queryset):
        queryset.update(workable=True)

    @h_decs.annotate(short_description=_('Mark as non-workable'))
    def _mark_as_non_workable_action(self, request, queryset):
        queryset.update(workable=False)

    # ============
    # custom views
    # ============

    def _merge_results_view(self, request, pk, overlay=False):
        assignment = get_object_or_404(Assignment, pk=pk)
        merge = assignment.merge_results()
        if merge:
            if overlay:
                tile = Image.open(assignment.tile.path).convert('RGBA')
                i0 = (tile.size[0] - merge.size[0]) / 2
                i1 = i0 + merge.size[0]
                ret = tile.crop((i0, i0, i1, i1))
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

    def get_actions(self, request):
        actions = super(AssignmentAdmin, self).get_actions(request)
        # WARNING ugly workaround to remove 'delete' action
        del actions['delete_selected']
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_list_display(self, request):
        list_display = list(super(AssignmentAdmin, self).get_list_display(
            request))
        # WARNING ugly, very ugly and very fragile, but I don't know how to do
        #         it differently right now =/.
        if request.method == 'GET':
            for k, _ in request.GET.items():
                try:
                    if k.find('seg_prob__id') != -1:
                        list_display.remove('_seg_prob')
                        list_display.remove('_task')
                    elif k.find('task__id') != -1:
                        list_display.remove('_task')
                except:
                    pass
        return list_display

    def get_urls(self):
        merge_results_view = self.admin_site.admin_view(
            self._merge_results_view)

        custom_urls = patterns('',
            url(r'^(?P<pk>\d+)/merge_results/overlay/$', merge_results_view,
                    {'overlay': True}, 'crowd_assignment_mergeresults_overlay')
            ,
            url(r'^(?P<pk>\d+)/merge_results/$', merge_results_view,
                name='crowd_assignment_mergeresults')
        )

        return custom_urls + super(AssignmentAdmin, self).get_urls()


# ===============================================
# Admin configuration for AssignmentSession model
# ===============================================

class AssignmentSessionAdmin(admin.ModelAdmin):
    # =============
    # configuration
    # =============

    list_display = ('id', '_assignment_preview', '_result', '_worker',
                    'start_time', '_remaining_time', '_active', '_expired',
                    '_skipped')
    ordering = ('-start_time',)

    # ================
    # auxiliary fields
    # ================

    @h_decs.annotate(short_description=_('assignment'), allow_tags=True)
    def _assignment_preview(self, obj):
        url = reverse('admin:crowd_assignment_change',
            args=(obj.assignment.pk,))
        thumb_src = obj.assignment.get_tile_thumb_url('small')
        return h_tmpl.render_linked_img(url, thumb_src)

    @h_decs.annotate(short_description=_('result'), allow_tags=True)
    def _result(self, obj):
        if not obj.has_result:
            return _('N/A')
        return h_tmpl.render_link(obj.result.url, _('See result'), {
            'target': '_blank'
        })

    @h_decs.annotate(short_description=_('worker'), admin_order_field='worker',
        allow_tags=True)
    def _worker(self, obj):
        url = reverse('admin:auth_user_change', args=(obj.worker.pk,))
        return h_tmpl.render_link(url, obj.worker)

    @h_decs.annotate(short_description=_('remaining time'),
        allow_tags=True)
    def _remaining_time(self, obj):
        if not obj.active:
            return _('N/A')
        return h_tmpl.render_progress(obj.remaining_time.total_seconds(),
            obj.timeout.total_seconds())

    @h_decs.annotate(short_description=_('active?'), boolean=True)
    def _active(self, obj):
        return obj.active

    @h_decs.annotate(short_description=_('expired?'), boolean=True)
    def _expired(self, obj):
        return obj.expired

    @h_decs.annotate(short_description=_('skipped?'), boolean=True)
    def _skipped(self, obj):
        return obj.skipped

    # ==================
    # overridden methods
    # ==================

    def get_actions(self, request):
        actions = super(AssignmentSessionAdmin, self).get_actions(request)
        # WARNING ugly workaround to remove 'delete' action
        del actions['delete_selected']
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ===================================
# Registration of models in Admin app
# ===================================

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(AssignmentSession, AssignmentSessionAdmin)
