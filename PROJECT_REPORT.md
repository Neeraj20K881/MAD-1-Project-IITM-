# Placement Portal — Project Report

Author: Neeraj Kumar

Roll No: 24f2000881

Course: Data Science

Institute: IIT Madras (IITM)

Email: 24f2000881@ds.study.iitm.ac.in

Date: 03-03-2026

---

## 1. Project Title

Placement Portal Web Application

## 2. Problem Statement (what the project should solve)

Many institutes manage campus recruitment manually using spreadsheets, emails and scattered documents. This causes problems such as missing approvals, duplicate applications, unclear statuses and difficulty tracking placement history. The Placement Portal aims to centralize recruitment workflows so Admin (Institute), Companies and Students can interact safely: companies register and create drives, admin approves companies and drives, students apply and view status.

## 3. My Approach (how I solved it)

I implemented a simple, easy-to-understand web application using Flask (Python) and SQLite. The design choices were kept deliberately minimal so the code is readable and easy to follow.

- Roles: Admin, Company and Student. Each role has separate pages and permissions checked server-side.
- Database: SQLite created programmatically on first run; tables: `users`, `students`, `companies`, `drives`, `applications`.
- Authentication: Basic username/password login; passwords hashed using Werkzeug.
- Approvals: Companies and drives require admin approval before students can see or apply.
- No JavaScript is used for core logic — server-side rendering with Jinja2 templates.

I focused on clarity over features: the goal was to cover the core requirements end-to-end with simple, well-commented code so anyone (including me) can read and extend it.

## 4. AI/LLM Declaration

I used an AI assistant only to help scaffold parts of the project (for example, initial project structure and example templates). I personally wrote, integrated and adapted the application logic, reviewed and tested all code locally, added comments, and made the final design decisions and edits. I accept full responsibility for the correctness, originality and submission of this work.

## 5. Frameworks and Libraries Used

- Flask (web framework)
- Jinja2 (templating — used via Flask)
- SQLite3 (database, built-in Python library)
- Werkzeug (for password hashing, included with Flask)
- Bootstrap CSS (CDN for styling — no JS required)

All Python dependencies are listed in `requirements.txt` (currently `Flask>=2.0`).

## 6. ER Diagram and Database Schema

Below is a textual ER diagram showing tables and relationships. It matches the schema created in `models.py`.

Tables and important fields:

- users (id PK, username UNIQUE, password_hash, role (admin|student|company))
- students (id PK, user_id FK -> users.id UNIQUE, full_name, department, cgpa, phone)
- companies (id PK, user_id FK -> users.id UNIQUE, company_name, hr_contact, website, approved, blacklisted)
- drives (id PK, company_id FK -> companies.id, job_title, job_desc, eligibility, deadline, status)
- applications (id PK, student_id FK -> students.id, drive_id FK -> drives.id, applied_on, status)

Relationships:

users 1---1 students (a student is linked to a user account)
users 1---1 companies (a company is linked to a user account)
companies 1---_ drives (a company can create many drives)
students 1---_ applications (a student can apply to many drives)
drives 1---\* applications (a drive can have many applications)

Simple ASCII ER diagram:

    [users]
      id PK
      username
      role
        |1
        |
    +---+---+
    |       |

[students] [companies]
id PK id PK
user_id FK user_id FK
|1 |1
| |
| [drives]
| id PK
[applications] drive_id FK
id PK student_id FK

Note: `applications` has a UNIQUE(student_id, drive_id) constraint to prevent duplicate applications.

## 7. API Resource Endpoints (routes)

This project uses server-side rendered routes instead of a JSON API, but the resource endpoints (HTTP routes) are listed below along with the HTTP method and short purpose.

- GET / : Home page — list approved drives
- GET, POST /login : Login page
- GET /logout : Logout
- GET, POST /register/student : Student registration (creates user + student profile)
- GET, POST /register/company : Company registration (creates user + company profile; requires admin approval to login)
- GET /admin : Admin dashboard (view/search companies and drives) — admin only
- GET /admin/company/<company_id>/approve : Approve a company — admin only
- GET /admin/company/<company_id>/reject : Reject company — admin only
- GET /admin/drive/<drive_id>/approve : Approve a drive — admin only
- GET /admin/drive/<drive_id>/reject : Set drive to pending — admin only
- GET /company : Company dashboard (view profile, drives) — company only
- GET, POST /company/drive/create : Create a drive (company creates; admin must approve)
- GET /drive/<drive_id> : View drive details
- POST /drive/<drive_id>/apply : Student applies to drive (student only)
- GET /company/drive/<drive_id>/applications : Company views applications for a drive — company only
- POST /application/<app_id>/status : Company updates application status (Shortlisted / Selected / Rejected)
- GET /student : Student dashboard — student only

Note: All role checks are done server-side by checking the logged-in user's role in session.

## 8. How to Run (short steps)

1. Create virtual environment (optional):

   py -3 -m venv venv
   .\venv\Scripts\Activate

2. Install requirements:

   py -3 -m pip install -r requirements.txt

3. Run the app:

   py -3 app.py

4. Open browser: http://127.0.0.1:5000/

Default admin credentials (created on first run):

- username: admin
- password: adminpass

## 9. Project Artifacts Submitted

- Source code (Flask app): files in project root (for example `app.py`, `models.py`, `templates/`, `requirements.txt`).
- This report (PROJECT_REPORT.md)
- Presentation video (Drive link below) and code in repository.

Drive link to presentation video ( link):

https://drive.google.com/file/d/1INSMoJbvH08MQknZgHbixMdxyd_jDj5g/view?usp=drive_link

---
