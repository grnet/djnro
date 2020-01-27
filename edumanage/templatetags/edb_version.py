from django import template
from utils.edb_versioning import (
    edb_version_fromto_resource,
    DEFAULT_EDUROAM_DATABASE_VERSION
)

register = template.Library()

@register.simple_tag(name='edb_realm_resource')
def realm_resource_from_edb_version(version=DEFAULT_EDUROAM_DATABASE_VERSION):
    return edb_version_fromto_resource(version)
