# Expense Splitter Mobile App(Backend)

This is the backend for a full stack mobile app for splitting shared expenses with friends. Create groups, add expenses with flexible splits, see who owes whom, and record settlements when people pay each other back.

## Features:

Authentication : Register and sign in with JWT (access + refresh tokens).
Groups : Create groups and invite members by email.
Expenses : Add expenses with equal, custom, or percentage splits and support multiple payers on one expense.
Balances : View net balances per member, show who owes whom, and settlement history when settled.
Settlements : Record payments between group members.

## Tech used:

Python, Django, Django REST Framework
SQLite database
JWT for login
drf-spectacular (Swagger) for API docs

## How to run

1. Open a terminal in the config folder.
2. Create and activate a virtual environment as:
  python -m venv venv
  venv\Scripts\activate
3. Install packages:
  pip install django djangorestframework djangorestframework-simplejwt django-cors-headers drf-spectacular
4. Run migrations and start the server as:
  python manage.py migrate
  python manage.py runserver

## API docs:
After the server runs, open: http://127.0.0.1:8000/api/schema/swagger-ui/ 

