# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models


depends_on = (
    ("default", "0001_initial"),
)


class Migration(DataMigration):

    def forwards(self, orm):
        # migrate from google to googleOAuth2
        try:
            for user in orm['default.usersocialauth'].objects.filter(provider='google'):
                user.provider = 'google-oauth2'
                user.save()
        except:
            pass

    def backwards(self, orm):
        try:
            for user in orm['default.usersocialauth'].objects.filter(provider='google-oauth2'):
                user.provider = 'google'
                user.save()
        except:
            pass

    models = {
        'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Institution']"}),
            'is_social_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
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
        'default.association': {
            'Meta': {'object_name': 'Association', 'db_table': "'social_auth_association'"},
            'assoc_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'handle': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issued': ('django.db.models.fields.IntegerField', [], {}),
            'lifetime': ('django.db.models.fields.IntegerField', [], {}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'server_url': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'default.code': {
            'Meta': {'unique_together': "(('email', 'code'),)", 'object_name': 'Code', 'db_table': "'social_auth_code'"},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'default.nonce': {
            'Meta': {'unique_together': "(('server_url', 'timestamp', 'salt'),)", 'object_name': 'Nonce', 'db_table': "'social_auth_nonce'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '65'}),
            'server_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'timestamp': ('django.db.models.fields.IntegerField', [], {})
        },
        'default.usersocialauth': {
            'Meta': {'unique_together': "(('provider', 'uid'),)", 'object_name': 'UserSocialAuth', 'db_table': "'social_auth_usersocialauth'"},
            'extra_data': ('social.apps.django_app.default.fields.JSONField', [], {'default': "'{}'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'social_auth'", 'to': "orm['auth.User']"})
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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'edumanage.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '80', 'db_column': "'contact_email'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_column': "'contact_name'"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '80', 'db_column': "'contact_phone'"})
        },
        'edumanage.institution': {
            'Meta': {'object_name': 'Institution'},
            'ertype': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '1', 'db_column': "'type'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'realmid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Realm']"})
        },
        'edumanage.name_i18n': {
            'Meta': {'object_name': 'Name_i18n'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'edumanage.realm': {
            'Meta': {'object_name': 'Realm'},
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'contact': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Contact']", 'symmetrical': 'False'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stype': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '1'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'edumanage.url_i18n': {
            'Meta': {'object_name': 'URL_i18n'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '180', 'db_column': "'URL'"}),
            'urltype': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_column': "'type'"})
        }
    }

    complete_apps = ['accounts']
    symmetrical = True
