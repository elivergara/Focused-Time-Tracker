# MIT Dashboard

Starter Django app for tracking MIT (Most Important Task) sessions.

## Stack
- Django + SQLite
- Bootstrap 5
- Font Awesome Free
- Sass

## Setup
```bash
cd ~/Django/MIT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run sass:build
python manage.py migrate
python manage.py runserver
```

## Sass commands
- Build once: `npm run sass:build`
- Watch mode: `npm run sass:watch`

## Next build targets
- MIT session models (Bible/Guitar/Work-Skill)
- Daily check-in input form
- Monthly summary dashboard
- Charting + exports
