# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'WorkerProfile.accumulated_accuracy'
        db.add_column('profiles_workerprofile', 'accumulated_accuracy',
                      self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=6, decimal_places=5),
                      keep_default=False)

        # Adding field 'WorkerProfile.mileage_sum'
        db.add_column('profiles_workerprofile', 'mileage_sum',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'WorkerProfile.last_time_worked'
        db.add_column('profiles_workerprofile', 'last_time_worked',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'WorkerProfile.accumulated_accuracy'
        db.delete_column('profiles_workerprofile', 'accumulated_accuracy')

        # Deleting field 'WorkerProfile.mileage_sum'
        db.delete_column('profiles_workerprofile', 'mileage_sum')

        # Deleting field 'WorkerProfile.last_time_worked'
        db.delete_column('profiles_workerprofile', 'last_time_worked')


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
        'profiles.requesterprofile': {
            'Meta': {'object_name': 'RequesterProfile', '_ormbases': ['profiles.UserProfile']},
            'account_balance': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'userprofile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['profiles.UserProfile']", 'unique': 'True', 'primary_key': 'True'})
        },
        'profiles.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'primary_key': 'True', 'to': "orm['auth.User']"})
        },
        'profiles.workerprofile': {
            'Meta': {'object_name': 'WorkerProfile', '_ormbases': ['profiles.UserProfile']},
            'accumulated_accuracy': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '6', 'decimal_places': '5'}),
            'last_time_worked': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'mileage_sum': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'score': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'userprofile_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['profiles.UserProfile']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['profiles']