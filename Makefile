PYTHON ?= uv run --with-requirements requirements.txt python

.PHONY: dev settings migrate seed run

dev: settings migrate seed

# Never overwrites an existing local_settings.py
settings:
	@if [ -e djnro/local_settings.py ]; then \
		echo "djnro/local_settings.py exists, leaving it alone"; \
	else \
		cp -v djnro/local_settings.py.dev djnro/local_settings.py; \
		echo "created djnro/local_settings.py from local_settings.py.dev"; \
	fi

migrate:
	$(PYTHON) manage.py migrate

seed:
	$(PYTHON) manage.py seed_devdata

run:
	$(PYTHON) manage.py runserver 127.0.0.1:8000
