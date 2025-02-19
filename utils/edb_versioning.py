# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
import operator
from semantic_version import Version
from django.conf import settings
import six
from six import python_2_unicode_compatible
from django.utils.functional import SimpleLazyObject, new_method_proxy
from .functional import partialmethod

class EduroamDatabaseVersionDef(object):
    version_1 = Version('1.0.0')
    version_2 = Version('2.0.0')

class DelegateVersion(type):
    @staticmethod
    def wrap_property(func):
        def _wrap(method, pass_args):
            if method is None:
                return method
            if pass_args:
                return lambda self, *args: partialmethod(
                    method, self.version)(*args)
            return lambda self: partialmethod(method, self.version)()
        return property(*(
            _wrap(fx, has_args)
            for fx, has_args in (
                (func.fget, False), (func.fset, True),
                (func.fdel, False), (func.__doc__, False)
            )
        ))
    @staticmethod
    def wrap_method(func):
        def _wrap(self, *args, **kwargs):
            delegate = lambda obj: obj.version if \
                isinstance(obj, EduroamDatabaseVersion) else obj
            args = tuple(delegate(arg) for arg in args)
            kwargs = {k: delegate(kwargs[k]) for k in kwargs}
            return getattr(self.version, func)(*args, **kwargs)
        return _wrap
    def __new__(cls, name, bases, dct):
        def _wrapper(attr):
            _func = getattr(Version, attr)
            if isinstance(_func, property):
                return DelegateVersion.wrap_property(_func)
            return DelegateVersion.wrap_method(attr)
        default_attrs = [
            m for m in dir(object)
            if len(m.strip('_')) != 2 # exclude comparisons: eq, ne, gt...
            and m.strip('_') != 'hash'
        ]
        for attr in dir(Version):
            if attr in default_attrs or attr in dct:
                continue
            dct[attr] = _wrapper(attr)
        return super(DelegateVersion, cls).__new__(cls, name, bases, dct)

@python_2_unicode_compatible
class EduroamDatabaseVersion(six.with_metaclass(DelegateVersion,
                                                EduroamDatabaseVersionDef)):
    def __init__(self, version):
        def to_version_obj(ver):
            if isinstance(ver, Version):
                return ver
            if isinstance(ver, dict):
                return Version(**ver)
            return Version.coerce(ver)

        self.default_version = to_version_obj(
            settings.EDUROAM_DATABASE_VERSIONS['default']
        )

        self.allowed_versions = [
            to_version_obj(ver)
            for ver in settings.EDUROAM_DATABASE_VERSIONS['allowed']
        ]

        self.version = to_version_obj(version)

        if self.version not in self.allowed_versions:
            raise ValueError('Version not allowed')

    def __repr__(self):
        return repr(self.version).replace(
            self.version.__class__.__name__,
            self.__class__.__name__
        )
    def __str__(self):
        return six.text_type(self.version)

    @property
    def is_default_version(self):
        return self == self.default_version
    @property
    def is_version_1(self):
        return self == self.version_1
    @property
    def is_version_2(self):
        return self == self.version_2
    @property
    def ge_version_2(self):
        return self >= self.version_2

class LazyEDBVersion(SimpleLazyObject):
    def __init__(self, obj, getter):
        super(LazyEDBVersion, self).__init__(
            lambda: EduroamDatabaseVersion(getter(obj)))
    # def __repr__(self):
    #     return repr(self._wrapped)
    __lt__ = new_method_proxy(operator.lt)
    __le__ = new_method_proxy(operator.le)
    __gt__ = new_method_proxy(operator.gt)
    __ge__ = new_method_proxy(operator.ge)
    __hash__ = new_method_proxy(operator.methodcaller('__hash__'))

DEFAULT_EDUROAM_DATABASE_VERSION = LazyEDBVersion(
    settings, lambda x: x.EDUROAM_DATABASE_VERSIONS['default']
)

class EDBVersionFromRequestException(Exception):
    pass

def edb_version_from_request(request, version=None, resource=None):
    versions = {}
    if version is not None:
        versions['path'] = EduroamDatabaseVersion(version)
    if request.GET.get('version', None):
        versions['parameter'] = EduroamDatabaseVersion(request.GET['version'])
    if resource is not None:
        versions['resource'] = edb_version_fromto_resource(resource)

    if not versions:
        return DEFAULT_EDUROAM_DATABASE_VERSION
    _key, _ver = versions.popitem()
    for key in versions:
        if versions[key] != _ver:
            raise EDBVersionFromRequestException(
                "Conflicting versions ({} vs. {})".format(_key, key)
            )
    return _ver

def edb_version_fromto_resource(res_or_edbv):
    resource_to_version = {
        "realm": EduroamDatabaseVersionDef.version_1,
        "ro": EduroamDatabaseVersionDef.version_2,
    }

    if not isinstance(res_or_edbv, EduroamDatabaseVersion):
        res = res_or_edbv
        try:
            version = resource_to_version[res]
        except KeyError:
            raise ValueError("Invalid resource")
        return EduroamDatabaseVersion(version)

    edbv = res_or_edbv
    version_to_resource = {
        resource_to_version[k]: k
        for k in resource_to_version
    }
    if edbv in version_to_resource:
        return version_to_resource[edbv]
    for version in sorted(version_to_resource, reverse=True):
        if edbv > version:
            return version_to_resource[version]
    raise ValueError("Could not determine resource from version")
