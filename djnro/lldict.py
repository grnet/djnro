from django.conf import settings
from django.utils.functional import SimpleLazyObject
from six import python_2_unicode_compatible
from django.utils.encoding import smart_str
@python_2_unicode_compatible
class LazyLangDict(SimpleLazyObject):
    def __init__(self, *args, **kwargs):
        def _setupfunc():
            dct = dict(*args, **kwargs)
            for lang in list(dct):
                if lang not in dict(settings.LANGUAGES):
                    del dct[lang]
            return dct
        super(LazyLangDict, self).__init__(_setupfunc)
    def __str__(self):
        if len(self):
            k, v = next(iter(self.items()))
            return smart_str(v)
        else:
            return super(LazyLangDict, self).__str__()
