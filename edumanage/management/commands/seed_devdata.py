from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User, UserProfile
from edumanage.models import (
    Address_i18n,
    Contact,
    Coordinates,
    Institution,
    InstitutionDetails,
    Name_i18n,
    Realm,
    ServiceLoc,
    URL_i18n,
)

PASSWORD = 'dev'

# name, ertype (1 IdP, 2 SP, 3 IdP+SP), (lat, lon), [(username, approved)]
INSTITUTIONS = [
    ('Example University', 3, ('59.8586', '17.6389'),
     [('alice', True), ('bob', True), ('carol', False)]),
    ('Example College', 1, ('57.7089', '11.9746'), [('dave', False)]),
    ('Example Hotspot', 2, ('55.6050', '13.0038'), [('erin', True)]),
]


class Command(BaseCommand):
    help = 'Create fake realm, institutions and users for development.'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Refusing to seed fake data with DEBUG = False.')
        realm = self.realm()
        rows = []
        for name, ertype, latlon, admins in INSTITUTIONS:
            inst = self.institution(realm, name, ertype, latlon)
            if ertype in (2, 3):
                self.service_loc(inst, name, latlon)
            for username, approved in admins:
                self.profile(username, inst, approved)
                rows.append((username, name, 'approved' if approved else 'pending'))
        nro = self.user('nro', is_staff=True, is_superuser=True)
        UserProfile.objects.get_or_create(
            user=nro,
            defaults={
                'institution': self.find_institution(INSTITUTIONS[0][0]),
                'is_social_active': True,
            })
        rows.append(('nro', INSTITUTIONS[0][0] + ' (staff)', 'approved'))
        self.user('frank')
        rows.append(('frank', '-', 'no institution yet'))

        self.stdout.write('\n%-10s %-34s %s' % ('username', 'institution', 'status'))
        for row in rows:
            self.stdout.write('%-10s %-34s %s' % row)
        self.stdout.write(
            '\nPassword for all users: %s\nLogin: http://localhost:8000/altlogin/'
            % PASSWORD)

    def attach_name(self, obj, name):
        ct = ContentType.objects.get_for_model(obj)
        Name_i18n.objects.get_or_create(
            content_type=ct, object_id=obj.pk, lang='en', defaults={'name': name})

    def find_institution(self, name):
        ct = ContentType.objects.get_for_model(Institution)
        names = Name_i18n.objects.filter(content_type=ct, name=name).first()
        return Institution.objects.filter(pk=names.object_id).first() if names else None

    def contact(self, name):
        contact, _ = Contact.objects.get_or_create(
            email='%s@example.org' % name.lower().replace(' ', '.'),
            defaults={'name': name, 'phone': '0000000000'})
        return contact

    def realm(self):
        realm, created = Realm.objects.get_or_create(
            country=settings.NRO_COUNTRY_CODE,
            defaults={'roid': settings.NRO_ROID})
        if created:
            self.attach_name(realm, 'Dev NRO')
            realm.contact.add(self.contact('Dev NRO'))
        return realm

    def institution(self, realm, name, ertype, latlon):
        inst = self.find_institution(name)
        if inst:
            return inst
        inst = Institution.objects.create(realmid=realm, ertype=ertype)
        self.attach_name(inst, name)
        details = InstitutionDetails.objects.create(
            institution=inst,
            coordinates=Coordinates.objects.create(
                latitude=latlon[0], longitude=latlon[1]),
        )
        details.contact.add(self.contact('%s Contact' % name))
        ct = ContentType.objects.get_for_model(details)
        Address_i18n.objects.create(
            content_type=ct, object_id=details.pk, lang='en',
            street='1 Campus Road', city='Exampleville')
        for urltype in ('info', 'policy'):
            URL_i18n.objects.create(
                content_type=ct, object_id=details.pk, lang='en',
                urltype=urltype, url='https://example.org/%s' % urltype)
        return inst

    def service_loc(self, inst, name, latlon):
        if ServiceLoc.objects.filter(institutionid=inst).exists():
            return
        loc = ServiceLoc.objects.create(institutionid=inst, SSID='eduroam')
        loc.coordinates.add(Coordinates.objects.create(
            latitude=latlon[0], longitude=latlon[1]))
        ct = ContentType.objects.get_for_model(loc)
        Name_i18n.objects.create(
            content_type=ct, object_id=loc.pk, lang='en', name='%s Main Site' % name)
        Address_i18n.objects.create(
            content_type=ct, object_id=loc.pk, lang='en',
            street='1 Campus Road', city='Exampleville')

    def user(self, username, **extra):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': '%s@example.org' % username, **extra})
        if created:
            user.set_password(PASSWORD)
            user.save()
        return user

    def profile(self, username, inst, approved):
        # Pending users stay is_active so they can log in locally and see
        # the pending page, as social-auth users do.
        UserProfile.objects.get_or_create(
            user=self.user(username),
            defaults={'institution': inst, 'is_social_active': approved})
