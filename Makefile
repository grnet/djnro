PYTHON ?= uv run --with-requirements requirements.txt python

.PHONY: dev settings migrate seed run

dev: settings migrate seed

# Never overwrites an existing local_settings.py
settings:
	@if [ -e djnro/local_settings.py ]; then \
		echo "djnro/local_settings.py exists, leaving it alone"; \
	else \
		$(PYTHON) -c "import secrets; print(open('djnro/local_settings.py.dev').read().replace('@@SECRET_KEY@@', secrets.token_urlsafe(50)), end='')" > djnro/local_settings.py; \
		echo "created djnro/local_settings.py from local_settings.py.dev"; \
	fi

migrate:
	$(PYTHON) manage.py migrate

seed:
	$(PYTHON) manage.py seed_devdata

run:
	$(PYTHON) manage.py runserver 0.0.0.0:8000
