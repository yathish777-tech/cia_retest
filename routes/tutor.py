from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, RetestApplication
from datetime import datetime
from functools import wraps

tutor_bp = Blueprint('tutor', __name__)

def tutor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'tutor':
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@tutor_bp.route('/dashboard')
@login_required
@tutor_required
def dashboard():
    # Pending = staff approved, tutor pending
    pending = RetestApplication.query.filter_by(
        tutor_id=current_user.id,
        staff_status='approved',
        tutor_status='pending'
    ).order_by(RetestApplication.submitted_at.desc()).all()

    reviewed = RetestApplication.query.filter(
        RetestApplication.tutor_id == current_user.id,
        RetestApplication.tutor_status.in_(['approved', 'rejected'])
    ).order_by(RetestApplication.tutor_action_time.desc()).all()

    stats = {
        'pending': len(pending),
        'approved': sum(1 for r in reviewed if r.tutor_status == 'approved'),
        'rejected': sum(1 for r in reviewed if r.tutor_status == 'rejected'),
        'total': len(pending) + len(reviewed)
    }
    return render_template('tutor/dashboard.html', pending=pending, reviewed=reviewed, stats=stats)

@tutor_bp.route('/action/<int:app_id>', methods=['POST'])
@login_required
@tutor_required
def action(app_id):
    application = RetestApplication.query.filter_by(
        id=app_id, tutor_id=current_user.id, staff_status='approved', tutor_status='pending'
    ).first_or_404()

    act = request.form.get('action')
    remark = request.form.get('remark', '')

    application.tutor_status = 'approved' if act == 'approve' else 'rejected'
    application.tutor_remark = remark
    application.tutor_action_time = datetime.utcnow()

    if act == 'reject':
        application.final_status = 'rejected'
        try:
            from utils.email_utils import notify_student_final
            notify_student_final(application)
        except: pass
    else:
        # Forward based on submission type
        # PRE: staff -> tutor -> HOD -> coordinator
        # LATE: staff -> tutor -> coordinator -> HOD -> coordinator
        try:
            from utils.email_utils import notify_approver
            from models import User
            if application.submission_type == 'pre':
                hod = User.query.filter_by(role='hod').first()
                if hod:
                    notify_approver(application, hod.email, hod.name, 'hod')
            else:  # late
                coordinator = User.query.filter_by(role='coordinator').first()
                if coordinator:
                    notify_approver(application, coordinator.email, coordinator.name, 'coordinator')
        except: pass

    db.session.commit()
    flash(f'Application {act}d successfully.', 'success')
    return redirect(url_for('tutor.dashboard'))
