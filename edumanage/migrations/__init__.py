from django.db import migrations
from django.utils import six

# a version of django.utils.functional.curry that *appends* extra args
def wrapper(f, *extra_args, **extra_kwargs):
    def wrapped(*args, **kwargs):
        return f(*(args + extra_args), **dict(kwargs, **extra_kwargs))
    return wrapped

# https://stackoverflow.com/a/55532892

class AppAwareRunPython(migrations.RunPython):
    # MonkeyPatch the forwards `code` with a wrapped version that adds an extra
    # argument `app_label`
    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        self.code = wrapper(self.code, app_label)
        super(AppAwareRunPython, self).database_forwards(
            app_label, schema_editor, from_state, to_state)

    # Same for backwards
    def database_backwards(self, app_label, schema_editor, from_state,
                           to_state):
        if self.reverse_code:
            self.reverse_code = wrapper(self.reverse_code, app_label)
        super(AppAwareRunPython, self).database_backwards(
            app_label, schema_editor, from_state, to_state)

    # Add the etra argument to noop
    @staticmethod
    def noop(apps, schema_editor, app_label=None):
        migrations.RunPython.noop(apps, schema_editor)

# Allow migrations using AppAwareRunPython.noop to be squashed on Python 2
# (it doesn't support serializing unbound methods so install a module function
# instead).
if six.PY2:
    def noop(apps, schema_editor, app_label=None):
        return None
    AppAwareRunPython.noop = staticmethod(noop)
