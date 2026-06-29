# Future Edits Guide

The project was reorganized to make changes safer.

## 1. Changing package prices

Edit only this file:

```text
academy/constants.py
```

Example:

```python
PRICE_PER_4_SESSIONS = 1500
SESSION_PACKAGE_CHOICES = [
    (4, '4 sessions - 1500 EGP'),
    (8, '8 sessions - 3000 EGP'),
]
```

## 2. Changing attendance deduction rules

Edit:

```text
academy/services.py
```

Function:

```python
mark_player_attendance(...)
```

Current rule:

- Attend deducts 1 session.
- Absent does not deduct.
- Changing Attend to Absent returns 1 session.
- Same player/date cannot be deducted twice.

## 3. Changing weekly plan dates

Edit:

```text
academy/services.py
```

Function:

```python
calculate_weekly_plan_dates(...)
```

Current rule:

- Start date aligns to the player's group day.
- End date is the last session date.
- One session per week.

## 4. Changing roles

Edit:

```text
academy/permissions.py
```

Current roles:

- Owner: Django superuser. Can create admins/coaches.
- Admin: staff user in `QAURA Admins`. Can manage players and sessions.
- Coach: staff user in `QAURA Coaches`. Can only take attendance.
- Player: logs in by numeric code only.

## 5. Adding a new page

1. Add the view function in `academy/views.py`.
2. Add the URL in `academy/urls.py`.
3. Add the HTML file in `academy/templates/academy/`.
4. Add the navbar link in `academy/templates/academy/base.html` only if needed.
5. Protect the view with one of these decorators:
   - `@admin_required`
   - `@owner_required`
   - `@admin_or_coach_required`

## 6. Database changes

After changing models:

```bash
python manage.py makemigrations
python manage.py migrate
```

Commit the generated migration files to GitHub.

## 7. Safe Git workflow for future edits

```bash
git checkout -b feature/my-change
# edit files
git add .
git commit -m "Describe the change"
git push -u origin feature/my-change
```

Then merge using a Pull Request on GitHub.
