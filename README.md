# Placement Portal Application

This is a simple Placement Portal web application built with Flask, Jinja2 templates and SQLite.

Features included (minimal, but covers core requirements):

- Admin (pre-created) can approve/reject companies and drives, view/search users and companies.
- Companies can register and create drives (visible after admin approval). They can view and update applications.
- Students can register, update profile, view approved drives and apply. They can see application status.

No JavaScript is used for core functionality. Database is created programmatically.

Run locally (Windows PowerShell):

1. Create a virtual environment (optional but recommended):
   python -m venv venv; .\venv\Scripts\Activate
2. Install requirements:
   python -m pip install -r requirements.txt
3. Run the app:
   python app.py
4. Open in browser: http://127.0.0.1:5000/

Default admin credentials (pre-created):

- username: admin
- password: adminpass

Notes:

- The SQLite database file `placement.db` is created automatically in the project folder.
- This project keeps code intentionally simple and heavily commented for learning.
