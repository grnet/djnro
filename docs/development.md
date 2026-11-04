# Development quick start

The Makefile runs everything through `$(PYTHON)`, which defaults to
[uv](https://docs.astral.sh/uv/) with `requirements.txt` and can be overridden
on the command line or in the environment. Pick one of these:

With uv, no setup needed (uv creates a cached environment from
`requirements.txt` on first use):

    make dev
    make run

With uv and a virtualenv:

    uv venv
    uv pip install -r requirements.txt
    make dev PYTHON=.venv/bin/python
    make run PYTHON=.venv/bin/python

With pip, in an environment you have activated:

    pip install -r requirements.txt
    make dev PYTHON=python
    make run PYTHON=python

`make dev` runs three steps, which can also be run separately:

- `make settings` creates `djnro/local_settings.py` from `djnro/local_settings.py.dev`
  (sqlite database `dev.db`, mail printed to the console, local login only).
  An existing `local_settings.py` is never overwritten.
- `make migrate` creates the database.
- `make seed` creates a fake realm, three institutions and users. It is safe to
  run repeatedly and refuses to run unless `DEBUG = True`.

Log in at <http://localhost:8000/altlogin/>. All passwords are `dev`.

| User  | Institution        | Status                       |
|-------|--------------------|------------------------------|
| alice | Example University | approved                     |
| bob   | Example University | approved                     |
| carol | Example University | pending                      |
| dave  | Example College    | pending                      |
| erin  | Example Hotspot    | approved                     |
| frank | none               | no profile; picks an institution at first login |
| nro   | Example University | staff and superuser (/admin) |

To start over, delete `dev.db` and run `make dev` again.
