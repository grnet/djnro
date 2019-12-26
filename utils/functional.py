from django.utils.inspect import getargspec

class cached_property(object):
    """Property descriptor that caches the return value
    of the get function.
    Like django.utils.functional.cached_property with the addition
    of setter and deleter.
    *Examples*
    .. code-block:: python
        @cached_property
        def connection(self):
            return Connection()
        @connection.setter  # Prepares stored value
        def connection(self, value):
            if value is None:
                raise TypeError("Connection must be a connection")
            return value
        @connection.deleter
        def connection(self, value):
            # Additional action to do at del(self.attr)
            if value is not None:
                print("Connection %r deleted" % (value, ))
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        if name is None and fget is not None:
            name = fget.__name__
        self.__name__ = name
        if fget is not None:
            self.__module__ = fget.__module__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        try:
            return obj.__dict__[self.__name__]
        except KeyError:
            value = obj.__dict__[self.__name__] = self.fget(obj)
            return value

    def __set__(self, obj, value):
        if obj is None:
            return
        if self.fset is not None:
            value = self.fset(obj, value)
        obj.__dict__[self.__name__] = value

    def __delete__(self, obj):
        if obj is None:
            return
        try:
            value = obj.__dict__.pop(self.__name__)
        except KeyError:
            pass
        else:
            if self.fdel is not None:
                fdel_args = [obj]
                if len(getargspec(self.fdel)[0]) == 2:
                    fdel_args.append(value)
                self.fdel(*fdel_args)

    def setter(self, fset):
        return self.__class__(self.fget, fset, self.fdel, self.__doc__, self.__name__)

    def deleter(self, fdel):
        return self.__class__(self.fget, self.fset, fdel, self.__doc__, self.__name__)
