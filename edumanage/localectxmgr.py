# -*- coding: utf-8 -*- vim:encoding=utf-8:
# vim: tabstop=4:shiftwidth=4:softtabstop=4:expandtab
# http://stackoverflow.com/a/24070673
import locale
import threading
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

@contextmanager
def setlocale(l, l_cat=locale.LC_ALL):
    with LOCALE_LOCK:
        saved = locale.setlocale(l_cat)
        try:
            yield locale.setlocale(l_cat, l)
        except locale.Error:
            yield
        finally:
            locale.setlocale(l_cat, saved)
