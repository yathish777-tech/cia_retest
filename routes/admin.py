from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Subject, CIADate, RetestApplication, TutorStudentMapping
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_apps = RetestApplication.query.count()
    approved = RetestApplication.query.filter_by(final_status='approved').count()
    rejected = RetestApplication.query.filter_by(final_status='rejected').count()
    pending = RetestApplication.query.filter_by(final_status='pending').count()
    pre_count = RetestApplication.query.filter_by(submission_type='pre').count()
    late_count = RetestApplication.query.filter_by(submission_type='late').count()
    total_students = User.query.filter_by(role='student').count()
    total_staff = User.query.filter_by(role='subject_staff').count()

    # Per-subject stats
    subjects = Subject.query.filter_by(is_active=True).all()
    subject_stats = []
    for s in subjects:
        count = RetestApplication.query.filter_by(subject_id=s.id).count()
        subject_stats.append({'name': s.subject_name, 'code': s.subject_code, 'count': count})
    subject_stats.sort(key=lambda x: x['count'], reverse=True)

    recent_apps = RetestApplication.query.order_by(RetestApplication.submitted_at.desc()).limit(10).all()

    stats = {
        'total': total_apps, 'approved': approved, 'rejected': rejected,
        'pending': pending, 'pre': pre_count, 'late': late_count,
        'students': total_students, 'staff': total_staff
    }
    return render_template('admin/dashboard.html', stats=stats,
        subject_stats=subject_stats, recent_apps=recent_apps)

# ─── STAFF MANAGEMENT ─────────────────────────────────────────────────────────
@admin_bp.route('/staff')
@login_required
@admin_required
def manage_staff():
    staff_list = User.query.filter(User.role.in_(['subject_staff','tutor','hod','coordinator'])).all()
    return render_template('admin/manage_staff.html', staff_list=staff_list)

@admin_bp.route('/staff/add', methods=['POST'])
@login_required
@admin_required
def add_staff():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    role = request.form.get('role', '')
    department = request.form.get('department', '').strip()
    password = request.form.get('password', 'staff123')

    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'danger')
        return redirect(url_for('admin.manage_staff'))

    user = User(name=name, email=email, phone=phone, role=role, department=department)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'{role.replace("_"," ").title()} added successfully! Default password: {password}', 'success')
    return redirect(url_for('admin.manage_staff'))

@admin_bp.route('/staff/edit/<int:uid>', methods=['POST'])
@login_required
@admin_required
def edit_staff(uid):
    user = User.query.get_or_404(uid)
    user.name = request.form.get('name', user.name).strip()
    user.phone = request.form.get('phone', user.phone).strip()
    user.department = request.form.get('department', user.department).strip()
    new_pass = request.form.get('password', '').strip()
    if new_pass:
        user.set_password(new_pass)
    db.session.commit()
    flash('Staff updated.', 'success')
    return redirect(url_for('admin.manage_staff'))

@admin_bp.route('/staff/toggle/<int:uid>', methods=['POST'])
@login_required
@admin_required
def toggle_staff(uid):
    user = User.query.get_or_404(uid)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.manage_staff'))

# ─── SUBJECT MANAGEMENT ───────────────────────────────────────────────────────
@admin_bp.route('/subjects')
@login_required
@admin_required
def manage_subjects():
    subjects = Subject.query.all()
    staff_list = User.query.filter_by(role='subject_staff', is_active=True).all()
    return render_template('admin/manage_subjects.html', subjects=subjects, staff_list=staff_list)

@admin_bp.route('/subjects/add', methods=['POST'])
@login_required
@admin_required
def add_subject():
    subject = Subject(
        subject_name=request.form.get('subject_name', '').strip(),
        subject_code=request.form.get('subject_code', '').strip(),
        semester=int(request.form.get('semester', 1)),
        department=request.form.get('department', '').strip(),
        staff_id=int(request.form.get('staff_id')) if request.form.get('staff_id') else None
    )
    db.session.add(subject)
    db.session.commit()
    flash('Subject added.', 'success')
    return redirect(url_for('admin.manage_subjects'))

@admin_bp.route('/subjects/edit/<int:sid>', methods=['POST'])
@login_required
@admin_required
def edit_subject(sid):
    subject = Subject.query.get_or_404(sid)
    subject.subject_name = request.form.get('subject_name', subject.subject_name)
    subject.subject_code = request.form.get('subject_code', subject.subject_code)
    subject.semester = int(request.form.get('semester', subject.semester))
    subject.department = request.form.get('department', subject.department)
    subject.staff_id = int(request.form.get('staff_id')) if request.form.get('staff_id') else None
    subject.is_active = request.form.get('is_active') == 'on'
    db.session.commit()
    flash('Subject updated.', 'success')
    return redirect(url_for('admin.manage_subjects'))

# ─── CIA DATES MANAGEMENT ─────────────────────────────────────────────────────
@admin_bp.route('/cia-dates')
@login_required
@admin_required
def manage_cia_dates():
    subjects = Subject.query.filter_by(is_active=True).all()
    cia_dates = CIADate.query.order_by(CIADate.exam_date.desc()).all()
    return render_template('admin/manage_cia_dates.html', subjects=subjects, cia_dates=cia_dates)

@admin_bp.route('/cia-dates/add', methods=['POST'])
@login_required
@admin_required
def add_cia_date():
    try:
        exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
        retest_date_str = request.form.get('retest_date', '')
        retest_date = datetime.strptime(retest_date_str, '%Y-%m-%d').date() if retest_date_str else None
        cia = CIADate(
            subject_id=int(request.form.get('subject_id')),
            cia_number=int(request.form.get('cia_number')),
            exam_date=exam_date,
            retest_date=retest_date,
            semester=int(request.form.get('semester')),
            academic_year=request.form.get('academic_year', '').strip(),
            created_by=current_user.id
        )
        db.session.add(cia)
        db.session.commit()
        flash('CIA date added.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin.manage_cia_dates'))

@admin_bp.route('/cia-dates/edit/<int:cid>', methods=['POST'])
@login_required
@admin_required
def edit_cia_date(cid):
    cia = CIADate.query.get_or_404(cid)
    try:
        cia.exam_date = datetime.strptime(request.form.get('exam_date'), '%Y-%m-%d').date()
        rd = request.form.get('retest_date', '')
        cia.retest_date = datetime.strptime(rd, '%Y-%m-%d').date() if rd else None
        cia.academic_year = request.form.get('academic_year', cia.academic_year)
        db.session.commit()
        flash('CIA date updated.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('admin.manage_cia_dates'))

# ─── ALL APPLICATIONS VIEW ────────────────────────────────────────────────────
@admin_bp.route('/applications')
@login_required
@admin_required
def all_applications():
    apps = RetestApplication.query.order_by(RetestApplication.submitted_at.desc()).all()
    return render_template('admin/all_applications.html', apps=apps)

@admin_bp.route('/applications/<int:app_id>')
@login_required
@admin_required
def view_application(app_id):
    app = RetestApplication.query.get_or_404(app_id)
    return render_template('admin/view_application.html', app=app)
