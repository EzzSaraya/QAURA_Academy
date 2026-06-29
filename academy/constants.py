"""Project constants kept in one place so future changes are easy.

Change prices, packages, role group names, and session keys here instead of
searching through views/forms/templates.
"""

ADMIN_GROUP_NAME = 'QAURA Admins'
COACH_GROUP_NAME = 'QAURA Coaches'
PLAYER_SESSION_KEY = 'qaura_player_id'

# Player codes are generated as numbers only, starting from this value.
FIRST_PLAYER_CODE = 100

# Pricing rule: every 4 sessions costs 1500 EGP.
SESSIONS_PER_PACKAGE = 4
PRICE_PER_4_SESSIONS = 1500
PRICE_PER_SESSION = PRICE_PER_4_SESSIONS // SESSIONS_PER_PACKAGE

SESSION_PACKAGE_CHOICES = [
    (4, '4 sessions - 1500 EGP'),
    (8, '8 sessions - 3000 EGP'),
    (12, '12 sessions - 4500 EGP'),
    (16, '16 sessions - 6000 EGP'),
    (20, '20 sessions - 7500 EGP'),
]

DEFAULT_TRAINING_GROUPS = [
    {'name': 'Monday Group', 'day': 'Monday', 'time': '20:00'},
    {'name': 'Saturday Group', 'day': 'Saturday', 'time': '20:00'},
]
