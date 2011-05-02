# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'GraphDB'
        db.create_table('schema_graphdb', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=30, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('schema', ['GraphDB'])

        # Adding unique constraint on 'GraphDB', fields ['order', 'owner']
        db.create_unique('schema_graphdb', ['order', 'owner_id'])

        # Adding model 'NodeType'
        db.create_table('schema_nodetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=30, db_index=True)),
            ('graph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.GraphDB'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('schema', ['NodeType'])

        # Adding unique constraint on 'NodeType', fields ['name', 'graph']
        db.create_unique('schema_nodetype', ['name', 'graph_id'])

        # Adding model 'EdgeType'
        db.create_table('schema_edgetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=30, db_index=True)),
            ('graph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.GraphDB'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('schema', ['EdgeType'])

        # Adding unique constraint on 'EdgeType', fields ['name', 'graph']
        db.create_unique('schema_edgetype', ['name', 'graph_id'])

        # Adding model 'ValidRelation'
        db.create_table('schema_validrelation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('node_from', self.gf('django.db.models.fields.related.ForeignKey')(related_name='node_from', to=orm['schema.NodeType'])),
            ('relation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.EdgeType'])),
            ('node_to', self.gf('django.db.models.fields.related.ForeignKey')(related_name='node_to', to=orm['schema.NodeType'])),
            ('graph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.GraphDB'])),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('arity', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('schema', ['ValidRelation'])

        # Adding model 'NodeProperty'
        db.create_table('schema_nodeproperty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('default', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('datatype', self.gf('django.db.models.fields.CharField')(default=u'u', max_length=1)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.NodeType'])),
        ))
        db.send_create_signal('schema', ['NodeProperty'])

        # Adding unique constraint on 'NodeProperty', fields ['order', 'node']
        db.create_unique('schema_nodeproperty', ['order', 'node_id'])

        # Adding model 'EdgeProperty'
        db.create_table('schema_edgeproperty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('default', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('datatype', self.gf('django.db.models.fields.CharField')(default=u'u', max_length=1)),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('order', self.gf('django.db.models.fields.IntegerField')()),
            ('edge', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.EdgeType'])),
        ))
        db.send_create_signal('schema', ['EdgeProperty'])

        # Adding unique constraint on 'EdgeProperty', fields ['order', 'edge']
        db.create_unique('schema_edgeproperty', ['order', 'edge_id'])

        # Adding model 'SylvaPermission'
        db.create_table('schema_sylvapermission', (
            ('permission_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.Permission'], unique=True, primary_key=True)),
            ('graph', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schema.GraphDB'])),
        ))
        db.send_create_signal('schema', ['SylvaPermission'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'EdgeProperty', fields ['order', 'edge']
        db.delete_unique('schema_edgeproperty', ['order', 'edge_id'])

        # Removing unique constraint on 'NodeProperty', fields ['order', 'node']
        db.delete_unique('schema_nodeproperty', ['order', 'node_id'])

        # Removing unique constraint on 'EdgeType', fields ['name', 'graph']
        db.delete_unique('schema_edgetype', ['name', 'graph_id'])

        # Removing unique constraint on 'NodeType', fields ['name', 'graph']
        db.delete_unique('schema_nodetype', ['name', 'graph_id'])

        # Removing unique constraint on 'GraphDB', fields ['order', 'owner']
        db.delete_unique('schema_graphdb', ['order', 'owner_id'])

        # Deleting model 'GraphDB'
        db.delete_table('schema_graphdb')

        # Deleting model 'NodeType'
        db.delete_table('schema_nodetype')

        # Deleting model 'EdgeType'
        db.delete_table('schema_edgetype')

        # Deleting model 'ValidRelation'
        db.delete_table('schema_validrelation')

        # Deleting model 'NodeProperty'
        db.delete_table('schema_nodeproperty')

        # Deleting model 'EdgeProperty'
        db.delete_table('schema_edgeproperty')

        # Deleting model 'SylvaPermission'
        db.delete_table('schema_sylvapermission')


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
        'schema.edgeproperty': {
            'Meta': {'unique_together': "(['order', 'edge'],)", 'object_name': 'EdgeProperty'},
            'datatype': ('django.db.models.fields.CharField', [], {'default': "u'u'", 'max_length': '1'}),
            'default': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'edge': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.EdgeType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'schema.edgetype': {
            'Meta': {'unique_together': "(('name', 'graph'),)", 'object_name': 'EdgeType'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'graph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.GraphDB']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '30', 'db_index': 'True'})
        },
        'schema.graphdb': {
            'Meta': {'unique_together': "(['order', 'owner'],)", 'object_name': 'GraphDB'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'schema.nodeproperty': {
            'Meta': {'unique_together': "(['order', 'node'],)", 'object_name': 'NodeProperty'},
            'datatype': ('django.db.models.fields.CharField', [], {'default': "u'u'", 'max_length': '1'}),
            'default': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.NodeType']"}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'schema.nodetype': {
            'Meta': {'unique_together': "(('name', 'graph'),)", 'object_name': 'NodeType'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'graph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.GraphDB']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '30', 'db_index': 'True'})
        },
        'schema.sylvapermission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'object_name': 'SylvaPermission', '_ormbases': ['auth.Permission']},
            'graph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.GraphDB']"}),
            'permission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Permission']", 'unique': 'True', 'primary_key': 'True'})
        },
        'schema.validrelation': {
            'Meta': {'object_name': 'ValidRelation'},
            'arity': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'graph': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.GraphDB']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node_from': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'node_from'", 'to': "orm['schema.NodeType']"}),
            'node_to': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'node_to'", 'to': "orm['schema.NodeType']"}),
            'relation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['schema.EdgeType']"})
        }
    }

    complete_apps = ['schema']
