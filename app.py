"""
app.py
Main Flask application for the Placement Portal.

This file wires routes, templates and uses models.py for DB operations.
Comments are added liberally to explain each part.
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash
import models
from datetime import datetime

# Create Flask app
app = Flask(__name__)
# Secret key for session management. In production, keep this secret!
app.secret_key = 'secret-key'

# Initialize database and default admin on startup
models.init_db()


# Helper decorator-like checks (simple functions used inside routes)
def logged_in():
    return 'user_id' in session


def current_user():
    if not logged_in():
        return None
    return models.get_user_by_id(session['user_id'])


@app.route('/')
def index():
    # Home page: show approved drives to everyone (students can apply after login)
    drives = models.get_drives(only_approved=True)
    return render_template('index.html', drives=drives, user=current_user())


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login for all roles
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = models.verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            flash('Logged in successfully.', 'success')
            # redirect by role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'company':
                return redirect(url_for('company_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html', user=current_user())


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    # Student registration: create user + student profile stub
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form.get('full_name', '')
        department = request.form.get('department', '')
        cgpa = request.form.get('cgpa')
        phone = request.form.get('phone', '')

        user_id = models.create_user(username, password, 'student')
        if not user_id:
            flash('Username already taken', 'danger')
            return render_template('register_student.html')
        models.add_student_profile(user_id, full_name, department, float(cgpa) if cgpa else None, phone)
        flash('Student registered. You can login now.', 'success')
        return redirect(url_for('login'))
    return render_template('register_student.html', user=current_user())


@app.route('/register/company', methods=['GET', 'POST'])
def register_company():
    # Company registration: create user + company profile (requires admin approval)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        company_name = request.form.get('company_name', '')
        hr_contact = request.form.get('hr_contact', '')
        website = request.form.get('website', '')

        user_id = models.create_user(username, password, 'company')
        if not user_id:
            flash('Username already taken', 'danger')
            return render_template('register_company.html')
        models.add_company_profile(user_id, company_name, hr_contact, website)
        flash('Company registered. Wait for admin approval to login.', 'info')
        return redirect(url_for('index'))
    return render_template('register_company.html', user=current_user())


@app.route('/admin')
def admin_dashboard():
    # Admin only page
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required', 'danger')
        return redirect(url_for('login'))

    # Show companies and drives to admin
    companies = models.get_companies()
    drives = models.get_drives(only_approved=False)
    # fetch simple totals for dashboard summary
    total_students = models.count_students()
    total_companies = models.count_companies()
    query = request.args.get('q', '').strip()
    student_results = []
    company_results = []
    if query:
        # use model search helpers for more complete matching
        company_results = models.search_companies(query)
        student_results = models.search_students(query)
    else:
        # no query: show full listing as before
        company_results = companies

    return render_template('admin_dashboard.html', user=user, companies=companies, drives=drives, q=query,
                           total_students=total_students, total_companies=total_companies,
                           company_results=company_results, student_results=student_results)


@app.route('/admin/company/<int:company_id>/approve')
def admin_approve_company(company_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for('login'))
    models.set_company_approval(company_id, True)
    flash('Company approved', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/company/<int:company_id>/reject')
def admin_reject_company(company_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for('login'))
    models.set_company_approval(company_id, False)
    flash('Company rejected', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/drive/<int:drive_id>/approve')
def admin_approve_drive(drive_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for('login'))
    models.set_drive_status(drive_id, 'Approved')
    flash('Drive approved', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/drive/<int:drive_id>/reject')
def admin_reject_drive(drive_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        return redirect(url_for('login'))
    models.set_drive_status(drive_id, 'Pending')
    flash('Drive set to pending/rejected', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/company')
def company_dashboard():
    # Company main page: must be approved to create drives
    user = current_user()
    if not user or user['role'] != 'company':
        flash('Company login required', 'danger')
        return redirect(url_for('login'))
    company = models.get_company_by_userid(user['id'])
    if not company:
        flash('Company profile not found', 'danger')
        return redirect(url_for('index'))
    # fetch drives for this company
    all_drives = [d for d in models.get_drives(only_approved=False) if d['company_id'] == company['id']]
    return render_template('company_dashboard.html', user=user, company=company, drives=all_drives)


@app.route('/company/drive/create', methods=['GET', 'POST'])
def company_create_drive():
    user = current_user()
    if not user or user['role'] != 'company':
        return redirect(url_for('login'))
    company = models.get_company_by_userid(user['id'])
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        eligibility = request.form['eligibility']
        deadline = request.form['deadline']
        models.create_drive(company['id'], title, desc, eligibility, deadline)
        flash('Drive created. Admin will approve it.', 'info')
        return redirect(url_for('company_dashboard'))
    return render_template('create_drive.html', user=user, company=company)


@app.route('/drive/<int:drive_id>')
def drive_view(drive_id):
    drive = models.get_drive(drive_id)
    if not drive:
        flash('Drive not found', 'danger')
        return redirect(url_for('index'))
    return render_template('drive.html', drive=drive, user=current_user())


@app.route('/drive/<int:drive_id>/apply', methods=['POST'])
def drive_apply(drive_id):
    user = current_user()
    if not user or user['role'] != 'student':
        flash('Student login required to apply', 'danger')
        return redirect(url_for('login'))
    student = models.get_student_by_userid(user['id'])
    success = models.apply_for_drive(student['id'], drive_id, datetime.utcnow().isoformat())
    if success:
        flash('Applied successfully', 'success')
    else:
        flash('You have already applied or error occurred', 'warning')
    return redirect(url_for('drive_view', drive_id=drive_id))


@app.route('/company/drive/<int:drive_id>/applications')
def company_drive_applications(drive_id):
    user = current_user()
    if not user or user['role'] != 'company':
        return redirect(url_for('login'))
    company = models.get_company_by_userid(user['id'])
    drive = models.get_drive(drive_id)
    if drive['company_id'] != company['id']:
        flash('Not authorized', 'danger')
        return redirect(url_for('company_dashboard'))
    apps = models.get_applications_for_drive(drive_id)
    return render_template('view_applications.html', user=user, drive=drive, apps=apps)


@app.route('/application/<int:app_id>/status', methods=['POST'])
def application_update_status(app_id):
    user = current_user()
    if not user or user['role'] != 'company':
        return redirect(url_for('login'))
    new_status = request.form.get('status')
    models.set_application_status(app_id, new_status)
    flash('Application status updated', 'success')
    return redirect(request.referrer or url_for('company_dashboard'))


@app.route('/student')
def student_dashboard():
    user = current_user()
    if not user or user['role'] != 'student':
        return redirect(url_for('login'))
    student = models.get_student_by_userid(user['id'])
    # show approved drives
    drives = models.get_drives(only_approved=True)
    return render_template('student_dashboard.html', user=user, student=student, drives=drives)


@app.route('/student/profile/edit', methods=['GET', 'POST'])
def edit_student_profile():
    """Allow a logged-in student to edit their profile.

    Uses models.add_student_profile which performs an INSERT OR REPLACE into
    the students table so it acts as both create and update.
    """
    user = current_user()
    if not user or user['role'] != 'student':
        flash('Student login required', 'danger')
        return redirect(url_for('login'))

    student = models.get_student_by_userid(user['id'])

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        department = request.form.get('department', '').strip()
        cgpa = request.form.get('cgpa')
        phone = request.form.get('phone', '').strip()

        # convert cgpa if provided
        cgpa_val = float(cgpa) if cgpa else None
        models.add_student_profile(user['id'], full_name, department, cgpa_val, phone)
        flash('Profile updated', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('edit_student_profile.html', user=user, student=student)


if __name__ == '__main__':
    # run in debug for development (remove debug=True in production)
    app.run(debug=True)
