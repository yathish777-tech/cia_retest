from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Subject, RetestApplication, CIADate, TutorStudentMapping
from datetime import datetime, date
from functools import wraps

user_bp = Blueprint('user', __name__)

def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'student':
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@user_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    apps = RetestApplication.query.filter_by(student_id=current_user.id)\
        .order_by(RetestApplication.submitted_at.desc()).all()
    return render_template('user/dashboard.html', applications=apps)

@user_bp.route('/apply', methods=['GET', 'POST'])
@login_required
@student_required
def apply():
    subjects = Subject.query.filter_by(is_active=True).all()
    tutors = User.query.filter_by(role='tutor').all()

    if request.method == 'POST':
        register_number = request.form.get('register_number', '').strip()
        student_name = request.form.get('student_name', '').strip()
        student_email = request.form.get('student_email', '').strip()
        subject_id = request.form.get('subject_id')
        staff_id = request.form.get('staff_id')
        tutor_id = request.form.get('tutor_id')
        semester = request.form.get('semester')
        cia_number = request.form.get('cia_number')
        cia_date_str = request.form.get('cia_date')
        reason_type = request.form.get('reason_type')
        reason_detail = request.form.get('reason_detail', '')
        submission_type = request.form.get('submission_type', 'pre')

        try:
            cia_date = datetime.strptime(cia_date_str, '%Y-%m-%d').date()
        except:
            flash('Invalid CIA date format.', 'danger')
            return render_template('user/apply.html', subjects=subjects, tutors=tutors)

        app = RetestApplication(
            student_id=current_user.id,
            register_number=register_number,
            student_name=student_name,
            student_email=student_email,
            subject_id=int(subject_id),
            staff_id=int(staff_id),
            tutor_id=int(tutor_id) if tutor_id else None,
            semester=int(semester),
            cia_number=int(cia_number),
            cia_date=cia_date,
            reason_type=reason_type,
            reason_detail=reason_detail,
            submission_type=submission_type
        )
        db.session.add(app)
        db.session.commit()

        # Email notification to subject staff
        try:
            from utils.email_utils import notify_staff_new_application
            staff = User.query.get(int(staff_id))
            if staff:
                notify_staff_new_application(app, staff.email, staff.name)
        except Exception as e:
            pass  # Don't fail if email fails

        flash('Application submitted successfully! It will be reviewed by the subject staff first.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/apply.html', subjects=subjects, tutors=tutors)

@user_bp.route('/application/<int:app_id>')
@login_required
@student_required
def view_application(app_id):
    app = RetestApplication.query.filter_by(id=app_id, student_id=current_user.id).first_or_404()
    return render_template('user/view_application.html', app=app)

@user_bp.route('/get_staff/<int:subject_id>')
@login_required
def get_staff_for_subject(subject_id):
    from flask import jsonify
    subject = Subject.query.get_or_404(subject_id)
    if subject.staff:
        return jsonify({'staff_id': subject.staff.id, 'staff_name': subject.staff.name})
    return jsonify({'staff_id': None, 'staff_name': None})
