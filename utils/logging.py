
def skip_disallowed_host_suspicious_operations(record):
    if record.name == 'django.security.DisallowedHost':
        return False
    return True

