# Project Structure

```text
qaura_academy_mvp/
├─ academy/
│  ├─ constants.py              # Prices, packages, role names, session key, default groups
│  ├─ models.py                 # Database tables: TrainingGroup, Player, Attendance
│  ├─ services.py               # Business logic: codes, sessions, attendance deduction
│  ├─ permissions.py            # Owner/admin/coach/player access rules
│  ├─ forms.py                  # Forms and validation
│  ├─ views.py                  # Page controllers only
│  ├─ urls.py                   # App routes
│  ├─ templates/                # HTML templates
│  ├─ static/img/               # Logo and images
│  ├─ management/commands/      # create_admin, create_coach, seed_groups
│  └─ migrations/               # Database migrations
├─ qaura_academy/
│  ├─ settings.py               # Django settings + deployment config
│  ├─ urls.py                   # Root URLs
│  ├─ wsgi.py                   # Production entrypoint
│  └─ asgi.py
├─ docs/                        # Maintenance docs
├─ build.sh                     # Render build command
├─ render.yaml                  # Render blueprint
├─ requirements.txt
├─ .env.example
├─ .gitignore
└─ README.md
```

## Where to edit common things

| Change needed | File |
|---|---|
| Change session price/package options | `academy/constants.py` |
| Change player code starting number | `academy/constants.py` |
| Change default groups | `academy/constants.py` + run `seed_groups` or edit DB |
| Change who can access pages | `academy/permissions.py` |
| Change session/date/attendance logic | `academy/services.py` |
| Change forms and validation | `academy/forms.py` |
| Change page layout/design | `academy/templates/academy/*.html` |
| Change logo/images | `academy/static/img/` |
| Change deployment/domain config | `.env`, `qaura_academy/settings.py`, `render.yaml` |
