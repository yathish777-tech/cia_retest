from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, RetestApplication
from datetime import datetime
from functools import wraps

coordinator_bp = Blueprint('coordinator', __name__)

def coordinator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role not in ('coordinator', 'admin'):
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated

@coordinator_bp.route('/dashboard')
@login_required
@coordinator_required
def dashboard():
    # PRE: HOD approved, coordinator pending (final step)
    pending_pre = RetestApplication.query.filter_by(
        submission_type='pre', hod_status='approved', coordinator_status='pending'
    ).filter(RetestApplication.staff_status == 'approved', RetestApplication.tutor_status == 'approved').all()

    # LATE: tutor approved, coordinator pending (first round, then goes to HOD)
    pending_late_first = RetestApplication.query.filter_by(
        submission_type='late', tutor_status='approved', coordinator_status='pending', hod_status='pending'
    ).filter(RetestApplication.staff_status == 'approved').all()

    # LATE: HOD approved, coordinator pending (second round = final)
    pending_late_final = RetestApplication.query.filter_by(
        submission_type='late', hod_status='approved', coordinator_status='pending'
    ).filter(RetestApplication.staff_status == 'approved', RetestApplication.tutor_status == 'approved').all()
    # Avoid duplicates
    late_first_ids = {a.id for a in pending_late_first}
    pending_late_final = [a for a in pending_late_final if a.id not in late_first_ids]

    pending = pending_pre + pending_late_first + pending_late_final

    all_approved = RetestApplication.query.filter_by(final_status='approved').all()
    all_rejected = RetestApplication.query.filter_by(final_status='rejected').all()
    all_applications = RetestApplication.query.order_by(RetestApplication.submitted_at.desc()).all()

    stats = {
        'pending': len(pending),
        'total': RetestApplication.query.count(),
        'approved': len(all_approved),
        'rejected': len(all_rejected)
    }
    return render_template('coordinator/dashboard.html',
        pending=pending, all_applications=all_applications, stats=stats)

@coordinator_bp.route('/action/<int:app_id>', methods=['POST'])
@login_required
@coordinator_required
def action(app_id):
    application = RetestApplication.query.get_or_404(app_id)
    act = request.form.get('action')
    remark = request.form.get('remark', '')
    is_final = request.form.get('is_final', 'false') == 'true'

    application.coordinator_status = 'approved' if act == 'approve' else 'rejected'
    application.coordinator_remark = remark
    application.coordinator_action_time = datetime.utcnow()

    if act == 'reject':
        application.final_status = 'rejected'
        try:
            from utils.email_utils import notify_student_final
            notify_student_final(application)
        except: pass
    else:
        # Determine if this is final or goes to HOD
        # PRE submission: coordinator is always final
        # LATE submission first pass: go to HOD
        # LATE submission second pass (after HOD): final
        is_late_first_pass = (
            application.submission_type == 'late' and
            application.hod_status == 'pending'
        )
        if is_late_first_pass:
            try:
                from utils.email_utils import notify_approver
                hod = User.query.filter_by(role='hod').first()
                if hod:
                    notify_approver(application, hod.email, hod.name, 'hod')
            except: pass
        else:
            application.final_status = 'approved'
            try:
                from utils.email_utils import notify_student_final
                notify_student_final(application)
            except: pass

    db.session.commit()
    flash(f'Application {act}d.', 'success')
    return redirect(url_for('coordinator.dashboard'))
