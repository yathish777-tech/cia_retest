from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, RetestApplication
from datetime import datetime
from functools import wraps

staff_bp = Blueprint('staff', __name__)

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != 'subject_staff':
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@staff_bp.route('/dashboard')
@login_required
@staff_required
def dashboard():
    pending = RetestApplication.query.filter_by(
        staff_id=current_user.id, staff_status='pending'
    ).order_by(RetestApplication.submitted_at.desc()).all()

    reviewed = RetestApplication.query.filter(
        RetestApplication.staff_id == current_user.id,
        RetestApplication.staff_status.in_(['approved', 'rejected'])
    ).order_by(RetestApplication.staff_action_time.desc()).all()

    stats = {
        'pending': len(pending),
        'approved': sum(1 for r in reviewed if r.staff_status == 'approved'),
        'rejected': sum(1 for r in reviewed if r.staff_status == 'rejected'),
        'total': len(pending) + len(reviewed)
    }
    return render_template('subject_staff/dashboard.html', pending=pending, reviewed=reviewed, stats=stats)

@staff_bp.route('/action/<int:app_id>', methods=['POST'])
@login_required
@staff_required
def action(app_id):
    application = RetestApplication.query.filter_by(id=app_id, staff_id=current_user.id).first_or_404()
    action = request.form.get('action')
    remark = request.form.get('remark', '')

    if action not in ['approve', 'reject']:
        flash('Invalid action.', 'danger')
        return redirect(url_for('staff.dashboard'))

    application.staff_status = 'approved' if action == 'approve' else 'rejected'
    application.staff_remark = remark
    application.staff_action_time = datetime.utcnow()

    if action == 'reject':
        application.final_status = 'rejected'
        try:
            from utils.email_utils import notify_student_final
            notify_student_final(application)
        except: pass
    else:
        # Forward to tutor
        try:
            from utils.email_utils import notify_approver
            tutor = application.tutor
            if tutor:
                notify_approver(application, tutor.email, tutor.name, 'tutor')
        except: pass

    db.session.commit()
    flash(f'Application {action}d successfully.', 'success')
    return redirect(url_for('staff.dashboard'))
