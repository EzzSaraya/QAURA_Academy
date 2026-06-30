# QAURA Academy System

Django website for QAURA Academy to manage player registration, weekly paid sessions, coach attendance, numeric player codes, and separated Owner/Admin/Coach/Player access.

## Main URLs

| Page | URL |
|---|---|
| Role selection | `/` |
| Owner/Admin login | `/admin-login/` |
| Coach login | `/coach-login/` |
| Player page | `/player/` |
| Player registration | `/register/` |
| Player code login | `/player-login/` |
| Player sessions | `/my-sessions/` |
| Attendance | `/attendance/` |
| Add sessions | `/add-sessions/` |
| Owner user management | `/owner/users/` |

## Roles

- **Owner:** Django superuser. Can create admins and coaches.
- **Admin:** Can add sessions, edit/delete players, and take attendance.
- **Coach:** Can only take attendance.
- **Player:** Can register and login using numeric code only.

Full permission details: `docs/ROLES_AND_PERMISSIONS.md`

## Local setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_groups
python manage.py createsuperuser
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Create coach/admin from command line

```bash
python manage.py create_coach --username coach1 --password coach12345
python manage.py create_admin --username admin1 --password admin12345
```

The preferred way is for the owner to login and use:

```text
Manage Users → Create User
```

## Future edits

The repository is organized so most changes happen in one clear place:

| Change needed | File |
|---|---|
| Prices/packages | `academy/constants.py` |
| Role permissions | `academy/permissions.py` |
| Attendance/session logic | `academy/services.py` |
| Forms/validation | `academy/forms.py` |
| Pages/UI | `academy/templates/academy/` |
| Deployment/domain settings | `.env`, `qaura_academy/settings.py`, `render.yaml` |

More details: `docs/FUTURE_EDITS.md`

## Deployment

This project is prepared for:

```text
GitHub → Render → PostgreSQL → Cloudflare domain
```

Deployment guide: `DEPLOYMENT.md`

## Domain

The project accepts:

```text
qaura.com
www.qaura.com
```

Local testing still uses:

```text
http://127.0.0.1:8000/
```

## Branding

Footer displays:

```text
Powered by BaseTech
```
