# GitHub Workflow

## First upload

```bash
git init
git add .
git commit -m "Initial organized QAURA Academy project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/qaura-academy.git
git push -u origin main
```

## For every future edit

```bash
git checkout -b feature/edit-name
# make the edit
git add .
git commit -m "Short clear message"
git push -u origin feature/edit-name
```

Open a Pull Request on GitHub and merge it into `main` after testing.

## Good commit examples

```text
Add owner user management page
Fix weekly end date calculation
Update player registration form
Improve attendance UI
```

## Do not commit

- `.env`
- `db.sqlite3`
- `venv/`
- `__pycache__/`
- uploaded private files
