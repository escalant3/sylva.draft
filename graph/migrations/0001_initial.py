# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Node'
        db.create_table('graph_node', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('node_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('graph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.GraphDB'])),
        ))
        db.send_create_signal('graph', ['Node'])

        # Adding model 'Media'
        db.create_table('graph_media', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['graph.Node'])),
            ('media_caption', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('media_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('media_file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
        ))
        db.send_create_signal('graph', ['Media'])


    def backwards(self, orm):
        
        # Deleting model 'Node'
        db.delete_table('graph_node')

        # Deleting model 'Media'
        db.delete_table('graph_media')


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
        'graph.media': {
            'Meta': {'object_name': 'Media'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media_caption': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'media_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'media_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['graph.Node']"})
        },
        'graph.node': {
            'Meta': {'object_name': 'Node'},
            'graph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.GraphDB']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'node_type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'schema.graphdb': {
            'Meta': {'unique_together': "(['order', 'owner'],)", 'object_name': 'GraphDB'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['graph']
