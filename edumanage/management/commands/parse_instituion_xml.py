# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
from django.core.management.base import BaseCommand, CommandError
from edumanage.models import *
import urllib
from xml.etree import ElementTree as ET
from django.conf import settings

class Command(BaseCommand):
    args = ''
    help = 'Fetches the kml from eduroam.org and updates cache'

    def handle(self, *args, **options):
        file = settings.INST_XML_FILE
        self.parseAndCreate(file)
    
    def parseAndCreate(self, file):
        doc = ET.parse(file)
        realmid = Realm.objects.get(pk=1)
        root = doc.getroot()
        institutions = []
        institutions = root.getchildren()
        for institution in institutions:
            createdInstDetails = False
            instcontactslist = []
            realmslist = []
            for instdetails in institution:
                self.stdout.write('Parsing: %s\n' %(instdetails.tag))
                if instdetails.tag == 'country':
                    
                    country = instdetails.text
                    continue
                if instdetails.tag == 'type':
                    type = instdetails.text
                    institutionObj = Institution(realmid=realmid, ertype = int(type))
                    institutionObj.save()
                    self.stdout.write('Created inst %s\n' %institutionObj.pk)
                    continue
                if instdetails.tag == 'inst_realm':
                    inst_realm = instdetails.text
                    instRealmObj = InstRealm(realm=inst_realm, instid=institutionObj)
                    instRealmObj.save()
                    continue
                if instdetails.tag == 'org_name':
                    org_name_lang = instdetails.items()[0][1]
                    org_name = instdetails.text
                    t = Name_i18n(content_object=institutionObj, name=org_name, lang=org_name_lang)
                    t.save()
                    continue
                if instdetails.tag == 'address':
                    for address in instdetails.getchildren():
                        if address.tag == 'street':
                            street = address.text
                        if address.tag == 'city':
                            city = address.text
                    continue
                if instdetails.tag == 'contact':            
                    for contact in instdetails.getchildren():
                        if contact.tag == 'name':
                            contact_name = contact.text
                        if contact.tag == 'email':
                            contact_email = contact.text
                        if contact.tag == 'phone':
                            contact_phone = contact.text
                    contactObj = Contact(name=contact_name, email=contact_email, phone=contact_phone)
                    contactObj.save()
                    instcontactslist.append(contactObj)
                    institutionContactObj = InstitutionContactPool(contact=contactObj, institution=institutionObj)
                    institutionContactObj.save()
                    continue
                
                if not createdInstDetails:
                    #instcontactsObjs = institutionContactObj.objects.filter(institution=institutionObj)
                    instdetsObj = InstitutionDetails(institution = institutionObj, address_street=street, address_city=city, number_id=1)
                    print instcontactslist
                    instdetsObj.save()
                    instdetsObj.contact = instcontactslist
                    instdetsObj.save()
                    createdInstDetails = True
                    
                
                if instdetails.tag == 'info_URL':
                    info_URL_lang = instdetails.items()[0][1]
                    info_URL = instdetails.text
                    u = URL_i18n(content_object=instdetsObj, urltype='info', lang=info_URL_lang, url= info_URL)
                    u.save()
                    continue
                if instdetails.tag == 'policy_URL':
                    policy_URL_lang = instdetails.items()[0][1]
                    policy_URL = instdetails.text
                    u = URL_i18n(content_object=instdetsObj, urltype='policy', lang=policy_URL_lang, url= policy_URL)
                    u.save()
                    continue
                
                if instdetails.tag == 'location':
                    locationNamesList = []
                    locationAddressList = []
                    parsedLocation = False
                    for locationdets in instdetails.getchildren():
                        if locationdets.tag == 'longitude':
                            location_long = locationdets.text
                            continue
                        if locationdets.tag == 'latitude':
                            location_lat = locationdets.text
                            continue
                        if locationdets.tag == 'loc_name':
                            locNameDict = {}
                            loc_name_lang = locationdets.items()[0][1]
                            loc_name = locationdets.text
                            locNameDict['name'] = loc_name
                            locNameDict['lang'] = loc_name_lang
                            locationNamesList.append(locNameDict)
                            continue
                        if locationdets.tag == 'address':
                            locAddrDict = {}
                            for locaddress in locationdets.getchildren():
                                if locaddress.tag == 'street':
                                    locstreet = locaddress.text
                                    locAddrDict['street'] = locstreet
                                if locaddress.tag == 'city':
                                    loccity = locaddress.text
                                    locAddrDict['city'] = loccity
                            locationAddressList.append(locAddrDict)
                            continue
                        if locationdets.tag == 'SSID':
                            loc_SSID = locationdets.text
                            continue
                        if locationdets.tag == 'enc_level':
                            loc_enc_level = locationdets.text
                            continue
                        if locationdets.tag == 'port_restrict':
                            loc_port_restrict_txt = locationdets.text
                            loc_port_restrict = False
                            if loc_port_restrict_txt in ('true', '1'):
                                loc_port_restrict = True
                            continue
                        if locationdets.tag == 'transp_proxy':
                            loc_transp_proxy_txt = locationdets.text
                            loc_transp_proxy = False
                            if loc_transp_proxy_txt in ('true', '1'):
                                loc_transp_proxy = True
                            continue
                        if locationdets.tag == 'IPv6':
                            loc_IPv6_txt = locationdets.text
                            loc_IPv6 = False
                            if loc_IPv6_txt in ('true', '1'):
                                loc_IPv6 = True
                            continue
                        if locationdets.tag == 'NAT':
                            loc_NAT_txt = locationdets.text
                            loc_NAT = False
                            if loc_NAT_txt in ('true', '1'):
                                loc_NAT = True
                            continue
                        if locationdets.tag == 'AP_no':
                            loc_AP_no= int(locationdets.text)
                            continue
                        if locationdets.tag == 'wired':
                            loc_wired_txt = locationdets.text
                            loc_wired = False
                            if loc_wired_txt in ('true', '1'):
                                loc_wired = True                            
                        if not parsedLocation:
                            self.stdout.write('Creating location:\n')
                            try:
                                serviceloc = ServiceLoc(institutionid=institutionObj, longitude=location_long, latitude=location_lat, address_street=locstreet, address_city=loccity, SSID=loc_SSID, enc_level=loc_enc_level, port_restrict=loc_port_restrict, transp_proxy=loc_transp_proxy, IPv6=loc_IPv6, NAT=loc_NAT, AP_no=loc_AP_no, wired=loc_wired)
                                serviceloc.save()
                                for locatName in locationNamesList:
                                    t = Name_i18n(content_object=serviceloc, name=locatName['name'], lang=locatName['lang'])
                                    t.save()
                                parsedLocation = True
                            except Exception as e:
                                self.stdout.write('ERROR: %s\n'%e)
                    continue
                                    
                            
                                                        
        
       
        return True
    
