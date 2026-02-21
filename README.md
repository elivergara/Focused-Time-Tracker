# Focus Performance Tracker

A professional Django web app for tracking focused work sessions, accountability, and monthly performance trends.

Focus Performance Tracker helps users:
- define and manage their own **Focus Categories**
- log daily **Focus Sessions** with planned vs actual minutes
- track completion status and miss reasons
- review monthly progress through dashboards and exports

## Stack
- Django + SQLite
- Bootstrap 5
- Font Awesome Free
- Sass
- Chart.js (dashboard visualizations)

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

## Core Features
- Public landing page + auth flow (signup/login)
- User-isolated accounts and data
- Daily Focus Log (1–8 sessions/day)
- Focus Category management (create, edit, activate/inactivate, delete)
- Monthly Accountability Report with CSV export
- KPI cards, trend charts, category mix, and goal progress

## Recommended Next Steps
- GitHub backup + CI workflow
- VPS deployment (OpenLiteSpeed + Gunicorn service)
- Scheduled reminders/notifications
- Weekly and monthly automated review summaries
- Optional Postgres migration for production scale
