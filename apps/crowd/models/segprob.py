###############################################################################
## Center for Advanced Computing Research
## California Institute of Technology
##
## Models related to segmentation problems in crowd app.
##
## Copyright 2012 Rafael Barreto <barreto@cacr.caltech.edu>
###############################################################################


# =====================
# Python stdlib imports
# =====================
from __future__ import with_statement
import logging
import os
import struct
import uuid
import tempfile

# ==============
# Django imports
# ==============
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

# ================
# external imports
# ================

from PIL import Image
from PIL import ImageMath
from backports import lzma

# ===============
# project imports
# ===============

import externals

from crowd.models.exceptions import InvalidStateError
from crowd.models.task import Task
from helpers import decorators as h_decs
from helpers import dip as h_dip
from helpers import filesystem as h_fs
from helpers import utils as h_utils
from helpers.django_related import models as h_mod
from helpers.django_related.utils import OverwriteStorage

import subprocess

debug_logger = logging.getLogger('debug')
internal_errors_logger = logging.getLogger('internal_errors')

class SegmentationProblem(models.Model):
    # ===============
    # class variables
    # ===============

    THUMB_SIZES = {
        'small': (80, 60),
        'medium': (133, 100),
        'large': (267, 200)
    }

    # ===============
    # private methods
    # ===============

    def _write_livevessel_preprocess_file(self, filename, costs, dimension, scales):
        with open(filename, 'wb') as f:
            n_scales = len(scales)

            f.write(struct.pack('iii', dimension, dimension, n_scales))
            f.write(struct.pack('%df' % n_scales, *scales))

            for scale in costs:
                for row in scale:
                    f.write(struct.pack('%dB' % len(row), *row))

    def _image_upload_to_fun(self, filename):
        task = self.task
        owner = task.owner

        task_model_name = h_utils.get_class_name(task)
        owner_model_name = h_utils.get_class_name(owner)
        seg_prob_model_name = h_utils.get_class_name(self)

        # IMPL_DETAIL this instead of instance.pk because we don't know that
        #             before saving
        unique_id = unicode(uuid.uuid4())

        return os.path.join(owner_model_name, unicode(owner.pk),
            task_model_name, unicode(task.pk), seg_prob_model_name, unique_id,
            'image' + os.path.splitext(filename)[1])

    # ================
    # model definition
    # ================

    task = models.ForeignKey(Task, verbose_name=_('task'),
        related_name='seg_probs', editable=False)

    # TODO change this to use 'sorl-thumbnail'
    #      (http://sorl-thumbnail.readthedocs.org/)
    image = externals.thumbs.ImageWithThumbsField(_('image'),
        upload_to=_image_upload_to_fun, sizes=THUMB_SIZES.values())

    notes_for_staff = models.TextField(_('notes for staff'), blank=True)

    # this has no practical effect if the segmentation problem does not have
    # assignments
    published = models.BooleanField(_('published?'), default=False, blank=True)

    class Meta:
        app_label = 'crowd'

        verbose_name = _('segmentation problem')
        verbose_name_plural = _('segmentation problems')

    # ==========
    # properties
    # ==========

    @property
    def has_assignments(self):
        return self.assignments.count() > 0

    @property
    def has_details(self):
        """True if it has enough information for the assignments to be
        created."""
        return hasattr(self, 'details')

    @property
    def root_rel_path(self):
        """Path where external resources for this segmentation problem are
        stored relative to storage server."""
        return os.path.dirname(self.image.name)

    @property
    def root_path(self):
        """Absolute path where external resources for this segmentation problem
        are stored."""
        return os.path.dirname(self.image.path)

    @property
    def assignments_root_rel_path(self):
        """Path where external resources for the associated assignments are
        stored relative to storage server."""
        return os.path.join(self.root_rel_path,
            self.assignments.model.__name__.lower())

    @property
    def assignments_root_path(self):
        """Absolute path where external resources for the associated
        assignments are stored."""
        return os.path.join(self.root_path,
            self.assignments.model.__name__.lower())

    # ==================
    # overridden methods
    # ==================

    def __unicode__(self):
        return u'%s %s (%s "%s")' % (self._meta.verbose_name, self.pk,
                                     self.task._meta.verbose_name, self.task)

    # ==============
    # public methods
    # ==============

    @staticmethod
    def read_file(filename):
        tmp_dir = tempfile.mkdtemp()
        tmp_file_path = os.path.join(tmp_dir, 'tempfile')

        try:
            with lzma.open(filename, 'rb') as xz_file:
                with open(tmp_file_path, 'wb') as tmp_file:
                    tmp_file.write(xz_file.read())

            costs = [[]]
            #scales = []
            with open(tmp_file_path, 'rb') as f:
                width, height, n_scales = struct.unpack('iii', f.read(12))
                scales = struct.unpack('%df' % n_scales, f.read(4*n_scales))

                #costs = [[]]
                i = 0
                count = 0
                a = f.read(width)
                while a != '':
                    costs[i].append(list(struct.unpack('%dB' % width, a)))
                    a = f.read(width)

                    count += 1
                    if count == height:
                        i += 1
                        count = 0
                        if i < 2:
                            costs.append([])
        finally:
            h_fs.rm(tmp_dir, ignore_errors=True)

        return {'costs': costs, 'scales': scales}

    def get_img_thumb_url(self, size):
        return getattr(self.image, 'url_%dx%d' % self.THUMB_SIZES[size])

    @h_decs.annotate(alters_data=True)
    def create_assignments(self):
        # a segmentation problem can only have assignments if details about how
        # the assignments should be created are provided
        h_utils.require(self.has_details,
            InvalidStateError(_('This segmentation problem is lacking '
                                'details.')))

        # clear any previous assignments for this segmentation problem
        self.clear_assignments()

        details = self.details
        try:
            tmp_dir = tempfile.mkdtemp()

            # generate the tiles for the assignments
            tiles_info = h_dip.generate_tiles(
                img_path=self.image.path,
                tiles_dim=details.tiles_dimension,
                overlap_rel=details.tiles_overlap,
                border_rel=details.tiles_border,
                dst_path=tmp_dir,
                workable_checker=h_dip.simple_content_detection()
            )[0]

            assignments = []
            for info in tiles_info:
                a = self.assignments.model(
                    seg_prob=self,
                    tile_bbox_x0=info['cropped_bbox'][0],
                    tile_bbox_y0=info['cropped_bbox'][1],
                    tile_bbox_x1=info['cropped_bbox'][2],
                    tile_bbox_y1=info['cropped_bbox'][3],
                    workable=info['workable']
                )
                with open(info['path'], 'rb') as f:
                    a.tile.save(os.path.basename(info['path']), File(f),
                        save=False)
                assignments.append(a)

            if details.algorithm == u'LIVEVESSEL':
                files_temp_path = []
                live_script_rel_path = '../externals/matlab/livevessel_pre_process/'
                livevessel_preprocess_script = h_fs.get_absolute_path(live_script_rel_path, settings.PROJECT_ROOT)
                processes = []
                for a in assignments:
                    tile_number = os.path.basename(os.path.splitext(a.tile.path)[0]).split('_')[1]
                    basedir = 'liv_preprocess_' + tile_number
                    temp_path = os.path.join(tmp_dir, basedir)
                    files_temp_path.append(temp_path)

                    code = "addpath(genpath('"+ livevessel_preprocess_script + "'));"
                    code = code + "offline('" + a.tile.path + "', '" + temp_path + "');"
                    code = code + "exit;"

                    processes.append(subprocess.Popen(
                        ["/usr/local/bin/matlab", "-nosplash", "-nodesktop", "-nojvm", "-r", code],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE))


                exit_code = [process.communicate() for process in processes]
                #print "next process"
                #out, err = process.communicate()

                index = 0
                for a in assignments:
                    compressed_file_path = files_temp_path[index] + '.xz'
                    with open(files_temp_path[index], 'rb') as f:
                        with lzma.open(compressed_file_path, 'wb') as xz_file:
                            xz_file.write(f.read())

                    with open(compressed_file_path, 'rb') as f:
                        basename = os.path.basename(compressed_file_path)
                        a.preprocess_file.save(basename, File(f), save=False)
                    index += 1



            if details.pre_seg:
                # generate pre segs. for the tiles
                pre_seg_tiles_info, border = h_dip.generate_tiles(
                    img_path=details.pre_seg.path,
                    tiles_dim=details.tiles_dimension,
                    overlap_rel=details.tiles_overlap,
                    border_rel=details.tiles_border,
                    dst_path=tmp_dir,
                    tiles_prefix='pre_seg_'
                )
                assert len(tiles_info) == len(pre_seg_tiles_info)
                for a, info in zip(assignments, pre_seg_tiles_info):
                    img = Image.open(info['path'])
                    img_w, img_h = img.size
                    img.crop((border, border, img_w - border,
                              img_h - border)).save(info['path'])
                    with open(info['path'], 'rb') as f:
                        a.pre_seg.save(os.path.basename(info['path']), File(f),
                            save=False)

            # effectively create the assignments
            try:
                self.assignments.bulk_create(assignments)
            except DatabaseError:
                debug_logger.exception('bulk creation of %d assignments '
                                       'failed... falling back to individual '
                                       'creation' % len(assignments))
                map(lambda a: a.save(), assignments)

            # in case of success, return the number of assignments created
            return len(assignments)
        except:
            # in case any thing goes wrong, undo and log the problem to the
            # administrators
            self.clear_assignments()
            internal_errors_logger.exception('assignments for segmentation '
                                             'problem %d could not be '
                                             'created' % self.pk)
        finally:
            h_fs.rm(tmp_dir, ignore_errors=True)

    @h_decs.annotate(alters_data=True)
    def clear_assignments(self):
        try:
            self.assignments.all().delete()
        except DatabaseError:
            debug_logger.exception('bulk deletion of assignments failed... '
                                   'falling back to individual deletion')
            map(lambda a: a.delete(), self.assignments.all())
        h_fs.rm(self.assignments_root_path, ignore_errors=True)

    @h_decs.annotate(alters_data=True)
    def merge_assignments(self):
        ret = Image.new('1', Image.open(self.image.path).size)
        if self.has_assignments:
            t_dim = self.details.tiles_dimension
            border_sz = int(t_dim * self.details.tiles_border)
            assignments = self.assignments.all()
            for a in assignments:
                a_mask = a.merge_results()
                if a_mask is None:
                    continue

                x0, y0 = a.tile_bbox_x0 + border_sz, a.tile_bbox_y0 + border_sz
                x1, y1 = a.tile_bbox_x1 - border_sz, a.tile_bbox_y1 - border_sz

                bbox = (x0, y0, x1, y1)
                ret.paste(ImageMath.eval('a | b', a = ret.crop(bbox),
                    b = a_mask), bbox)
        return ret


class SegmentationProblemDetails(models.Model):
    # ===============
    # private methods
    # ===============

    def _pre_seg_upload_to_fun(self, filename):
        return os.path.join(self.seg_prob.root_rel_path,
            'pre_seg' + os.path.splitext(filename)[1])

    # ===============
    # class variables
    # ===============

    ALGORITHMS = (
        ('MANUAL', _('Manual segmentation')),
        ('WATERSHED', _('Watershed')),
        ('LIVEWIRE', _('LiveWire')),
        ('LIVEVESSEL', _('LiveVessel')),
        )

    MIN_TILES_DIMENSION = 30

    DEFAULT_TILES_OVERLAP = 0.15
    MAX_TILES_OVERLAP = 0.3

    DEFAULT_TILES_BORDER = 0.25
    MAX_TILES_BORDER = 0.5

    DEFAULT_MIN_RESULTS_PER_ASSIGNMENT = 5
    DEFAULT_ASSIGNMENTS_TIMEOUT = 300  # 5 minutes

    # ================
    # model definition
    # ================

    seg_prob = models.OneToOneField(SegmentationProblem,
        verbose_name=_('segmentation problem'), related_name='details',
        editable=False)

    # TODO this must be validated so as to the width/height be equal to that
    # of the Segmentation Problem
    pre_seg = h_mod.PreProcessImageField(_('pre seg.'), max_length=255,
        storage=OverwriteStorage(), blank=True,
        upload_to=_pre_seg_upload_to_fun, max_upload_size=1048576,
        pre_process_fun=h_dip.pre_seg_pre_process_fun)

    # TODO probably the algorithms choices should come from a model on its own
    algorithm = models.CharField(_('algorithm'), max_length=10,
        choices=ALGORITHMS)

    tiles_dimension = models.PositiveIntegerField(_('tiles dimension'),
        validators=[MinValueValidator(MIN_TILES_DIMENSION)])
    tiles_overlap = models.FloatField(_('tiles overlap'),
        default=DEFAULT_TILES_OVERLAP,
        validators=[MinValueValidator(0.0),
                    MaxValueValidator(MAX_TILES_OVERLAP)])
    tiles_border = models.FloatField(_('tiles border'),
        default=DEFAULT_TILES_BORDER,
        validators=[MinValueValidator(0.0),
                    MaxValueValidator(MAX_TILES_BORDER)])

    min_results_per_assignment = models.PositiveIntegerField(
        _('min. results per assignment'),
        default=DEFAULT_MIN_RESULTS_PER_ASSIGNMENT,
        validators=[MinValueValidator(1)])
    assignments_timeout = models.PositiveIntegerField(_('assignments timeout'),
        default=DEFAULT_ASSIGNMENTS_TIMEOUT)

    class Meta:
        app_label = 'crowd'

        verbose_name = _('segmentation problem details')
        verbose_name_plural = _('segmentation problems details')

    # ==================
    # overridden methods
    # ==================

    def __unicode__(self):
        return _('defails of %s') % self.seg_prob
