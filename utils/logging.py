
def skip_disallowed_host_suspicious_operations(record):
    if record.name == 'django.security.DisallowedHost':
        return False
    if record.name == 'django.request' and record.exc_info is not None and record.exc_info[0].__name__ == "DisallowedHost":
        return False
    return True

