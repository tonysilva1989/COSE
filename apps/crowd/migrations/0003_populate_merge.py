# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

# ===========================
# Migration-specific imports
# ===========================

import os
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
from django.core.files.base import ContentFile
from helpers import dip as h_dip
from django.db.models.query_utils import Q
from PIL import Image
from django.core.files.storage import default_storage

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Don't use "from appname.models import ModelName". 
        # Use orm.ModelName to refer to models in this application,
        # and orm['appname.ModelName'] for models in other applications.
        for a in orm.Assignment.objects.all():
            a.merge = None
            if a.concluded:
                finished = a.sessions.filter(~Q(result=''))
                merge = None
                try:
                    merge = h_dip.merge_masks([s.result.path for s in finished])
                except:
                    #TODO log this error as a inconsistency problem: 
                    #number of masks is not equal to the number o sessions with results
                    pass
                merge = Image.fromarray(merge['merge_skel']) if merge else None
                if merge is not None:
                    tile_filename = os.path.splitext(os.path.split(a.tile.name)[1])[0]
                    merge_filename = '%s_merge.png' % (tile_filename)
                    
                    path = os.path.join(os.path.dirname(a.seg_prob.image.name), a.seg_prob.assignments.model.__name__.lower())
                    merge_path = os.path.join(path, merge_filename)
                    
                    output = StringIO()
                    merge.save(output, format='PNG')
                    #import pdb; pdb.set_trace()
                    merge_file = default_storage.save(merge_path, ContentFile(output.getvalue()))
                    a.merge = merge_file
                    a.save()
        

    def backwards(self, orm):
        "Write your backwards methods here."
        for a in orm.Assignment.objects.all():
            if a.merge: 
                a.merge.delete()
        
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'crowd.assignment': {
            'Meta': {'unique_together': "(('seg_prob', 'tile'),)", 'object_name': 'Assignment'},
            'concluded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merge': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True'}),
            'pre_seg': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'blank': 'True'}),
            'seg_prob': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': "orm['crowd.SegmentationProblem']"}),
            'tile': ('externals.thumbs.ImageWithThumbsField', [], {'max_length': '100', 'name': "'tile'", 'sizes': '[(50, 50), (150, 150), (100, 100)]'}),
            'tile_bbox_x0': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tile_bbox_x1': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tile_bbox_y0': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tile_bbox_y1': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'workable': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'})
        },
        'crowd.assignmentsession': {
            'Meta': {'object_name': 'AssignmentSession'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sessions'", 'to': "orm['crowd.Assignment']"}),
            'close_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expiration_deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments_sessions'", 'to': "orm['auth.User']"})
        },
        'crowd.segmentationproblem': {
            'Meta': {'object_name': 'SegmentationProblem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('externals.thumbs.ImageWithThumbsField', [], {'max_length': '100', 'name': "'image'", 'sizes': '[(80, 60), (267, 200), (133, 100)]'}),
            'notes_for_staff': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'seg_probs'", 'to': "orm['crowd.Task']"})
        },
        'crowd.segmentationproblemdetails': {
            'Meta': {'object_name': 'SegmentationProblemDetails'},
            'algorithm': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'assignments_timeout': ('django.db.models.fields.PositiveIntegerField', [], {'default': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_results_per_assignment': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5'}),
            'pre_seg': ('helpers.django_related.models.PreProcessImageField', [], {'max_upload_size': '1048576', 'max_length': '255', 'blank': 'True'}),
            'seg_prob': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'details'", 'unique': 'True', 'to': "orm['crowd.SegmentationProblem']"}),
            'tiles_border': ('django.db.models.fields.FloatField', [], {'default': '0.25'}),
            'tiles_dimension': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'tiles_overlap': ('django.db.models.fields.FloatField', [], {'default': '0.15'})
        },
        'crowd.task': {
            'Meta': {'unique_together': "(('title', 'category'),)", 'object_name': 'Task'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'on_delete': 'models.PROTECT', 'to': "orm['crowd.TaskCategory']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes_for_staff': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tasks'", 'to': "orm['auth.User']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'crowd.taskcategory': {
            'Meta': {'unique_together': "(('title', 'parent'),)", 'object_name': 'TaskCategory'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['crowd.TaskCategory']", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['crowd']
    symmetrical = True
