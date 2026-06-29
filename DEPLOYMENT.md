# QAURA Academy Deployment Notes

## Local run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_groups
python manage.py createsuperuser
python manage.py runserver
```

## Render settings

Build command:

```bash
./build.sh
```

Start command:

```bash
gunicorn qaura_academy.wsgi:application
```

Environment variables:

```text
SECRET_KEY=<generate strong secret>
DEBUG=False
ALLOWED_HOSTS=qaura.com,www.qaura.com,.onrender.com
CSRF_TRUSTED_ORIGINS=https://qaura.com,https://www.qaura.com
DATABASE_URL=<Render PostgreSQL internal connection string>
```

## First live accounts

After deployment, use Render Shell:

```bash
python manage.py createsuperuser
python manage.py create_coach --username coach1 --password coach12345
```
