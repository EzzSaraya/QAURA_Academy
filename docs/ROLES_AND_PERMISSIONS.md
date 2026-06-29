# Roles and Permissions

## Owner

Owner is a Django superuser created by:

```bash
python manage.py createsuperuser
```

Owner can:

- Access admin dashboard
- Add paid sessions
- Take attendance
- Edit/delete player users
- Create admin accounts
- Create coach accounts
- Delete admin/coach accounts

## Admin

Admin is a staff user in the `QAURA Admins` group.

Admin can:

- Access dashboard
- Add paid sessions
- Take attendance
- Edit player phone number, username, start date, end date logic
- Delete player users

Admin cannot:

- Create other admins or coaches

## Coach

Coach is a staff user in the `QAURA Coaches` group.

Coach can:

- Take attendance only

Coach cannot:

- Add sessions
- Open dashboard
- Create users
- Edit/delete players

## Player

Player is not a staff account. Player logs in using numeric code only.

Player can:

- Register
- Login using code
- See remaining sessions, paid amount, start date, end date, and session dates

Player cannot:

- See admin login from player pages
- Add sessions
- Take attendance
- Access dashboard
