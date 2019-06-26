# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab

# Copyright © 2011-2015 Greek Research and Technology Network (GRNET S.A.)
#
# Developed by Leonidas Poulopoulos (leopoul-at-noc-dot-grnet-dot-gr),
# Zenon Mousmoulas (zmousm-at-noc-dot-grnet-dot-gr) and Stavros Kroustouris
# (staurosk-at-noc-dot-grnet-dot-gr), GRNET NOC
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHORS DISCLAIM ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR
# CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.
from django.core.management.base import BaseCommand
import time
from django.conf import settings
from django.core.cache import cache
from django.utils import six
from xml.etree import ElementTree
import json
import bz2


class Command(BaseCommand):
    args = ''
    help = 'Fetches the kml from eduroam.org and updates cache'

    def handle(self, *args, **options):
        if int(options['verbosity']) > 0:
            write = self.stdout.write
        else:
            write = lambda *args: None
        eduroam_kml_url = settings.EDUROAM_KML_URL
        rnd = int(time.time()*1000)
        eduroam_kml_url = "%s?gmaprnd=%s" % (eduroam_kml_url, rnd)
        write('Fetching data from %s...\n'%eduroam_kml_url)
        file = settings.KML_FILE
        six.moves.urllib.request.urlretrieve(eduroam_kml_url, file)
        write('Done fetching!\n')
        write('Updating cache\n')
        self.refresh_cache(file)
        write('Done updating cache\n')
        write('Finished!\n')

    def refresh_cache(self, file):
        point_list = []
        doc = ElementTree.parse(file)
        root = doc.getroot()
        r = root.getchildren()[0]
        for (counter, i) in enumerate(r.getchildren()):
            if "id" in i.keys():
                j = i.getchildren()
                pointname = j[0].text
                point = j[2].getchildren()[0].text
                pointlng, pointlat, pointele = point.split(',')
                point_list.append(
                    {
                        "name": pointname,
                        "lat": pointlat,
                        "lng": pointlng,
                        "text": j[1].text
                    }
                )
        points = json.dumps(point_list)
        if six.PY3:
            # python3: convert string as bytestring
            points = points.encode('utf-8')
        cache.set('points', bz2.compress(points), 60 * 3600 * 24)
        return True
