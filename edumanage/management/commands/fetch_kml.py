# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import warnings
warnings.simplefilter("ignore", DeprecationWarning)
from django.core.management.base import BaseCommand, CommandError
import time
from django.conf import settings
import urllib
from django.core.cache import cache
from xml.etree import ElementTree as ET
import json, bz2

class Command(BaseCommand):
    args = ''
    help = 'Fetches the kml from eduroam.org and updates cache'

    def handle(self, *args, **options):
        eduroam_kml_url = settings.EDUROAM_KML_URL
        rnd = int(time.time()*1000)
        eduroam_kml_url = "%s?gmaprnd=%s" %(eduroam_kml_url, rnd)
        self.stdout.write('Fetching data from %s...\n'%eduroam_kml_url)
        file = settings.KML_FILE
        urllib.urlretrieve(eduroam_kml_url, file)
        self.stdout.write('Done fetching!\n')
        self.stdout.write('Updating cache\n')
        self.refreshCache(file)
        self.stdout.write('Done updating cache\n')
        self.stdout.write('Finished!\n')
        
    
    def refreshCache(self, file):
        point_list = []
        doc = ET.parse(file)
        root = doc.getroot()
        r = root.getchildren()[0]
        for (counter, i) in enumerate(r.getchildren()):
            if "id" in i.keys():
                j = i.getchildren()
                pointname = j[0].text
                point = j[2].getchildren()[0].text
                pointlng, pointlat, pointele = point.split(',')
                Marker = {"name": pointname, "lat": pointlat, "lng": pointlng, "text": j[1].text}
                point_list.append(Marker);
        points = json.dumps(point_list)
        cache.set('points', bz2.compress(points), 60 * 3600 * 24)
        return True