from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, RetestApplication
from datetime import datetime
from functools import wraps
from sqlalchemy import or_, and_

hod_bp = Blueprint('hod', __name__)

def hod_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'hod':
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@hod_bp.route('/dashboard')
@login_required
@hod_required
def dashboard():
    # PRE: tutor approved, hod pending
    # LATE: coordinator approved (first round), hod pending
    pending_pre = RetestApplication.query.filter_by(
        submission_type='pre', tutor_status='approved', hod_status='pending'
    ).filter(RetestApplication.staff_status == 'approved').all()

    pending_late = RetestApplication.query.filter_by(
        submission_type='late', coordinator_status='approved', hod_status='pending'
    ).filter(RetestApplication.staff_status == 'approved', RetestApplication.tutor_status == 'approved').all()

    pending = pending_pre + pending_late

    reviewed = RetestApplication.query.filter(
        RetestApplication.hod_status.in_(['approved', 'rejected'])
    ).order_by(RetestApplication.hod_action_time.desc()).all()

    stats = {
        'pending': len(pending),
        'approved': sum(1 for r in reviewed if r.hod_status == 'approved'),
        'rejected': sum(1 for r in reviewed if r.hod_status == 'rejected'),
        'total': len(pending) + len(reviewed)
    }
    return render_template('hod/dashboard.html', pending=pending, reviewed=reviewed, stats=stats)

@hod_bp.route('/action/<int:app_id>', methods=['POST'])
@login_required
@hod_required
def action(app_id):
    application = RetestApplication.query.get_or_404(app_id)
    act = request.form.get('action')
    remark = request.form.get('remark', '')

    application.hod_status = 'approved' if act == 'approve' else 'rejected'
    application.hod_remark = remark
    application.hod_action_time = datetime.utcnow()

    if act == 'reject':
        application.final_status = 'rejected'
        try:
            from utils.email_utils import notify_student_final
            notify_student_final(application)
        except: pass
    else:
        # PRE: after HOD -> coordinator (final)
        # LATE: after HOD -> coordinator (second time, final)
        try:
            from utils.email_utils import notify_approver
            coordinator = User.query.filter_by(role='coordinator').first()
            if coordinator:
                notify_approver(application, coordinator.email, coordinator.name, 'coordinator')
        except: pass

    db.session.commit()
    flash(f'Application {act}d successfully.', 'success')
    return redirect(url_for('hod.dashboard'))
