# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Name_i18n'
        db.create_table('edumanage_name_i18n', (
            ('lang', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
        ))
        db.send_create_signal('edumanage', ['Name_i18n'])

        # Adding model 'Contact'
        db.create_table('edumanage_contact', (
            ('email', self.gf('django.db.models.fields.CharField')(max_length=80, db_column='contact_email')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=80, db_column='contact_phone')),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80, db_column='contact_name')),
        ))
        db.send_create_signal('edumanage', ['Contact'])

        # Adding model 'URL_i18n'
        db.create_table('edumanage_url_i18n', (
            ('url', self.gf('django.db.models.fields.CharField')(max_length=180, db_column='URL')),
            ('lang', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('urltype', self.gf('django.db.models.fields.CharField')(max_length=10, db_column='type')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('edumanage', ['URL_i18n'])

        # Adding model 'InstRealm'
        db.create_table('edumanage_instrealm', (
            ('priority', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=3)),
            ('realmexpr', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('instid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.Institution'])),
        ))
        db.send_create_signal('edumanage', ['InstRealm'])

        # Adding M2M table for field proxyto on 'InstRealm'
        db.create_table('edumanage_instrealm_proxyto', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('instrealm', models.ForeignKey(orm['edumanage.instrealm'], null=False, on_delete=models.CASCADE)),
            ('instserver', models.ForeignKey(orm['edumanage.instserver'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_instrealm_proxyto', ['instrealm_id', 'instserver_id'])

        # Adding model 'InstServer'
        db.create_table('edumanage_instserver', (
            ('ertype', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=1, db_column='type')),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('proto', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('instid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.Institution'])),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('host', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('retry', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2)),
            ('timeout', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=2)),
            ('status_server', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('acct_port', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=5)),
            ('port', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=5)),
        ))
        db.send_create_signal('edumanage', ['InstServer'])

        # Adding model 'InstRealmMon'
        db.create_table('edumanage_instrealmmon', (
            ('instid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.Institution'])),
            ('realm', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mon_type', self.gf('django.db.models.fields.CharField')(max_length=8)),
        ))
        db.send_create_signal('edumanage', ['InstRealmMon'])

        # Adding model 'MonProxybackClient'
        db.create_table('edumanage_monproxybackclient', (
            ('instrealmmonid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.InstRealmMon'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('proto', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('status_server', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('secret', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('host', self.gf('django.db.models.fields.CharField')(max_length=80)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('edumanage', ['MonProxybackClient'])

        # Adding model 'MonLocalEAPOLData'
        db.create_table('edumanage_monlocaleapoldata', (
            ('username', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('phase2', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('instrealmmonid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.InstRealmMon'])),
            ('eap_method', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('cert', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('exp_response', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('passwp', self.gf('django.db.models.fields.CharField')(max_length=24, db_column='pass')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('edumanage', ['MonLocalEAPOLData'])

        # Adding model 'ServiceLoc'
        db.create_table('edumanage_serviceloc', (
            ('address_city', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('transp_proxy', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('SSID', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('institutionid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.Institution'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=6)),
            ('wired', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('enc_level', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('NAT', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('IPv6', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=6)),
            ('port_restrict', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('address_street', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('AP_no', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=3)),
        ))
        db.send_create_signal('edumanage', ['ServiceLoc'])

        # Adding M2M table for field loc_name on 'ServiceLoc'
        db.create_table('edumanage_serviceloc_loc_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('serviceloc', models.ForeignKey(orm['edumanage.serviceloc'], null=False, on_delete=models.CASCADE)),
            ('name_i18n', models.ForeignKey(orm['edumanage.name_i18n'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_serviceloc_loc_name', ['serviceloc_id', 'name_i18n_id'])

        # Adding M2M table for field url on 'ServiceLoc'
        db.create_table('edumanage_serviceloc_url', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('serviceloc', models.ForeignKey(orm['edumanage.serviceloc'], null=False, on_delete=models.CASCADE)),
            ('url_i18n', models.ForeignKey(orm['edumanage.url_i18n'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_serviceloc_url', ['serviceloc_id', 'url_i18n_id'])

        # Adding M2M table for field contact on 'ServiceLoc'
        db.create_table('edumanage_serviceloc_contact', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('serviceloc', models.ForeignKey(orm['edumanage.serviceloc'], null=False, on_delete=models.CASCADE)),
            ('contact', models.ForeignKey(orm['edumanage.contact'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_serviceloc_contact', ['serviceloc_id', 'contact_id'])

        # Adding model 'Institution'
        db.create_table('edumanage_institution', (
            ('address_city', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('ertype', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=1, db_column='type')),
            ('number_user', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=6)),
            ('realmid', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['edumanage.Realm'])),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('oper_name', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('number_id', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=6)),
            ('address_street', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('edumanage', ['Institution'])

        # Adding M2M table for field org_name on 'Institution'
        db.create_table('edumanage_institution_org_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('institution', models.ForeignKey(orm['edumanage.institution'], null=False, on_delete=models.CASCADE)),
            ('name_i18n', models.ForeignKey(orm['edumanage.name_i18n'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_institution_org_name', ['institution_id', 'name_i18n_id'])

        # Adding M2M table for field url on 'Institution'
        db.create_table('edumanage_institution_url', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('institution', models.ForeignKey(orm['edumanage.institution'], null=False, on_delete=models.CASCADE)),
            ('url_i18n', models.ForeignKey(orm['edumanage.url_i18n'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_institution_url', ['institution_id', 'url_i18n_id'])

        # Adding M2M table for field contact on 'Institution'
        db.create_table('edumanage_institution_contact', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('institution', models.ForeignKey(orm['edumanage.institution'], null=False, on_delete=models.CASCADE)),
            ('contact', models.ForeignKey(orm['edumanage.contact'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_institution_contact', ['institution_id', 'contact_id'])

        # Adding model 'Realm'
        db.create_table('edumanage_realm', (
            ('address_city', self.gf('django.db.models.fields.CharField')(max_length=24)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('address_street', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stype', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, max_length=1)),
        ))
        db.send_create_signal('edumanage', ['Realm'])

        # Adding M2M table for field org_name on 'Realm'
        db.create_table('edumanage_realm_org_name', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('realm', models.ForeignKey(orm['edumanage.realm'], null=False, on_delete=models.CASCADE)),
            ('name_i18n', models.ForeignKey(orm['edumanage.name_i18n'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_realm_org_name', ['realm_id', 'name_i18n_id'])

        # Adding M2M table for field url on 'Realm'
        db.create_table('edumanage_realm_url', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('realm', models.ForeignKey(orm['edumanage.realm'], null=False, on_delete=models.CASCADE)),
            ('url_i18n', models.ForeignKey(orm['edumanage.url_i18n'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_realm_url', ['realm_id', 'url_i18n_id'])

        # Adding M2M table for field contact on 'Realm'
        db.create_table('edumanage_realm_contact', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('realm', models.ForeignKey(orm['edumanage.realm'], null=False, on_delete=models.CASCADE)),
            ('contact', models.ForeignKey(orm['edumanage.contact'], null=False, on_delete=models.CASCADE))
        ))
        db.create_unique('edumanage_realm_contact', ['realm_id', 'contact_id'])

        # Adding model 'RealmData'
        db.create_table('edumanage_realmdata', (
            ('number_SP', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=5)),
            ('number_user', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=9)),
            ('ts', self.gf('django.db.models.fields.DateTimeField')()),
            ('realmid', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['edumanage.Realm'], unique=True)),
            ('number_IdP', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=5)),
            ('number_IdPSP', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=5)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number_id', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=9)),
            ('number_inst', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=5)),
        ))
        db.send_create_signal('edumanage', ['RealmData'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Name_i18n'
        db.delete_table('edumanage_name_i18n')

        # Deleting model 'Contact'
        db.delete_table('edumanage_contact')

        # Deleting model 'URL_i18n'
        db.delete_table('edumanage_url_i18n')

        # Deleting model 'InstRealm'
        db.delete_table('edumanage_instrealm')

        # Removing M2M table for field proxyto on 'InstRealm'
        db.delete_table('edumanage_instrealm_proxyto')

        # Deleting model 'InstServer'
        db.delete_table('edumanage_instserver')

        # Deleting model 'InstRealmMon'
        db.delete_table('edumanage_instrealmmon')

        # Deleting model 'MonProxybackClient'
        db.delete_table('edumanage_monproxybackclient')

        # Deleting model 'MonLocalEAPOLData'
        db.delete_table('edumanage_monlocaleapoldata')

        # Deleting model 'ServiceLoc'
        db.delete_table('edumanage_serviceloc')

        # Removing M2M table for field loc_name on 'ServiceLoc'
        db.delete_table('edumanage_serviceloc_loc_name')

        # Removing M2M table for field url on 'ServiceLoc'
        db.delete_table('edumanage_serviceloc_url')

        # Removing M2M table for field contact on 'ServiceLoc'
        db.delete_table('edumanage_serviceloc_contact')

        # Deleting model 'Institution'
        db.delete_table('edumanage_institution')

        # Removing M2M table for field org_name on 'Institution'
        db.delete_table('edumanage_institution_org_name')

        # Removing M2M table for field url on 'Institution'
        db.delete_table('edumanage_institution_url')

        # Removing M2M table for field contact on 'Institution'
        db.delete_table('edumanage_institution_contact')

        # Deleting model 'Realm'
        db.delete_table('edumanage_realm')

        # Removing M2M table for field org_name on 'Realm'
        db.delete_table('edumanage_realm_org_name')

        # Removing M2M table for field url on 'Realm'
        db.delete_table('edumanage_realm_url')

        # Removing M2M table for field contact on 'Realm'
        db.delete_table('edumanage_realm_contact')

        # Deleting model 'RealmData'
        db.delete_table('edumanage_realmdata')
    
    
    models = {
        'edumanage.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.CharField', [], {'max_length': '80', 'db_column': "'contact_email'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'db_column': "'contact_name'"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '80', 'db_column': "'contact_phone'"})
        },
        'edumanage.institution': {
            'Meta': {'object_name': 'Institution'},
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'contact': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Contact']", 'symmetrical': 'False'}),
            'ertype': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '1', 'db_column': "'type'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '6'}),
            'number_user': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '6'}),
            'oper_name': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'org_name': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Name_i18n']", 'symmetrical': 'False'}),
            'realmid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Realm']"}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.URL_i18n']", 'symmetrical': 'False'})
        },
        'edumanage.instrealm': {
            'Meta': {'object_name': 'InstRealm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Institution']"}),
            'priority': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '3'}),
            'proxyto': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.InstServer']", 'symmetrical': 'False'}),
            'realmexpr': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'edumanage.instrealmmon': {
            'Meta': {'object_name': 'InstRealmMon'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Institution']"}),
            'mon_type': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'realm': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'edumanage.instserver': {
            'Meta': {'object_name': 'InstServer'},
            'acct_port': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5'}),
            'ertype': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '1', 'db_column': "'type'"}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Institution']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5'}),
            'proto': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'retry': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'status_server': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'timeout': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '2'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'edumanage.monlocaleapoldata': {
            'Meta': {'object_name': 'MonLocalEAPOLData'},
            'cert': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'eap_method': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'exp_response': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrealmmonid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.InstRealmMon']"}),
            'passwp': ('django.db.models.fields.CharField', [], {'max_length': '24', 'db_column': "'pass'"}),
            'phase2': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '24'})
        },
        'edumanage.monproxybackclient': {
            'Meta': {'object_name': 'MonProxybackClient'},
            'host': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instrealmmonid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.InstRealmMon']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'proto': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'status_server': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'edumanage.name_i18n': {
            'Meta': {'object_name': 'Name_i18n'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        'edumanage.realm': {
            'Meta': {'object_name': 'Realm'},
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'contact': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Contact']", 'symmetrical': 'False'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org_name': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Name_i18n']", 'symmetrical': 'False'}),
            'stype': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'max_length': '1'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.URL_i18n']", 'symmetrical': 'False'})
        },
        'edumanage.realmdata': {
            'Meta': {'object_name': 'RealmData'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_IdP': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5'}),
            'number_IdPSP': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5'}),
            'number_SP': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5'}),
            'number_id': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '9'}),
            'number_inst': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '5'}),
            'number_user': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '9'}),
            'realmid': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['edumanage.Realm']", 'unique': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {})
        },
        'edumanage.serviceloc': {
            'AP_no': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '3'}),
            'IPv6': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceLoc'},
            'NAT': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'SSID': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'address_city': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'address_street': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'contact': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Contact']", 'symmetrical': 'False'}),
            'enc_level': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'institutionid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['edumanage.Institution']"}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '6'}),
            'loc_name': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.Name_i18n']", 'symmetrical': 'False'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '6'}),
            'port_restrict': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'transp_proxy': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'ts': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['edumanage.URL_i18n']", 'symmetrical': 'False'}),
            'wired': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'edumanage.url_i18n': {
            'Meta': {'object_name': 'URL_i18n'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lang': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '180', 'db_column': "'URL'"}),
            'urltype': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_column': "'type'"})
        }
    }
    
    complete_apps = ['edumanage']
