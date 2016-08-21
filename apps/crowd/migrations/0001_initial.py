# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TaskCategory'
        db.create_table('crowd_taskcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['crowd.TaskCategory'], null=True, blank=True)),
        ))
        db.send_create_signal('crowd', ['TaskCategory'])

        # Adding unique constraint on 'TaskCategory', fields ['title', 'parent']
        db.create_unique('crowd_taskcategory', ['title', 'parent_id'])

        # Adding model 'Task'
        db.create_table('crowd_task', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', on_delete=models.PROTECT, to=orm['crowd.TaskCategory'])),
            ('notes_for_staff', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tasks', to=orm['auth.User'])),
        ))
        db.send_create_signal('crowd', ['Task'])

        # Adding unique constraint on 'Task', fields ['title', 'category']
        db.create_unique('crowd_task', ['title', 'category_id'])

        # Adding model 'SegmentationProblem'
        db.create_table('crowd_segmentationproblem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('task', self.gf('django.db.models.fields.related.ForeignKey')(related_name='seg_probs', to=orm['crowd.Task'])),
            ('image', self.gf('externals.thumbs.ImageWithThumbsField')(max_length=100, name='image', sizes=[(80, 60), (267, 200), (133, 100)])),
            ('notes_for_staff', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('crowd', ['SegmentationProblem'])

        # Adding model 'SegmentationProblemDetails'
        db.create_table('crowd_segmentationproblemdetails', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seg_prob', self.gf('django.db.models.fields.related.OneToOneField')(related_name='details', unique=True, to=orm['crowd.SegmentationProblem'])),
            ('pre_seg', self.gf('helpers.django_related.models.PreProcessImageField')(max_upload_size=1048576, max_length=255, blank=True)),
            ('algorithm', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('tiles_dimension', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('tiles_overlap', self.gf('django.db.models.fields.FloatField')(default=0.15)),
            ('tiles_border', self.gf('django.db.models.fields.FloatField')(default=0.25)),
            ('min_results_per_assignment', self.gf('django.db.models.fields.PositiveIntegerField')(default=5)),
            ('assignments_timeout', self.gf('django.db.models.fields.PositiveIntegerField')(default=300)),
        ))
        db.send_create_signal('crowd', ['SegmentationProblemDetails'])

        # Adding model 'Assignment'
        db.create_table('crowd_assignment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('seg_prob', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', to=orm['crowd.SegmentationProblem'])),
            ('tile', self.gf('externals.thumbs.ImageWithThumbsField')(max_length=100, name='tile', sizes=[(50, 50), (150, 150), (100, 100)])),
            ('tile_bbox_x0', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('tile_bbox_y0', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('tile_bbox_x1', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('tile_bbox_y1', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('pre_seg', self.gf('django.db.models.fields.files.ImageField')(max_length=255, blank=True)),
            ('workable', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
            ('concluded', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('crowd', ['Assignment'])

        # Adding unique constraint on 'Assignment', fields ['seg_prob', 'tile']
        db.create_unique('crowd_assignment', ['seg_prob_id', 'tile'])

        # Adding model 'AssignmentSession'
        db.create_table('crowd_assignmentsession', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sessions', to=orm['crowd.Assignment'])),
            ('start_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('close_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('expiration_deadline', self.gf('django.db.models.fields.DateTimeField')()),
            ('result', self.gf('django.db.models.fields.files.ImageField')(max_length=255, blank=True)),
            ('worker', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments_sessions', to=orm['auth.User'])),
        ))
        db.send_create_signal('crowd', ['AssignmentSession'])


    def backwards(self, orm):
        # Removing unique constraint on 'Assignment', fields ['seg_prob', 'tile']
        db.delete_unique('crowd_assignment', ['seg_prob_id', 'tile'])

        # Removing unique constraint on 'Task', fields ['title', 'category']
        db.delete_unique('crowd_task', ['title', 'category_id'])

        # Removing unique constraint on 'TaskCategory', fields ['title', 'parent']
        db.delete_unique('crowd_taskcategory', ['title', 'parent_id'])

        # Deleting model 'TaskCategory'
        db.delete_table('crowd_taskcategory')

        # Deleting model 'Task'
        db.delete_table('crowd_task')

        # Deleting model 'SegmentationProblem'
        db.delete_table('crowd_segmentationproblem')

        # Deleting model 'SegmentationProblemDetails'
        db.delete_table('crowd_segmentationproblemdetails')

        # Deleting model 'Assignment'
        db.delete_table('crowd_assignment')

        # Deleting model 'AssignmentSession'
        db.delete_table('crowd_assignmentsession')


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