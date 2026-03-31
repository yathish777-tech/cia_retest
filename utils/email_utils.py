from flask_mail import Message
from app import mail
from flask import current_app

def send_email(to, subject, body_html):
    """Send an HTML email."""
    try:
        msg = Message(
            subject=subject,
            recipients=[to] if isinstance(to, str) else to,
            html=body_html,
            sender=current_app.config.get('MAIL_USERNAME')  # ✅ FIXED
        )

        mail.send(msg)
        print("✅ Email sent successfully")
        return True

    except Exception as e:
        print("❌ EMAIL ERROR:", e)  # shows real error in terminal
        return False


def notify_staff_new_application(application, staff_email, staff_name):
    subject = f"New CIA Retest Application - {application.student_name}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f7fb;padding:30px;">
    <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
      <div style="background:linear-gradient(135deg,#1a237e,#283593);padding:20px;border-radius:8px;text-align:center;">
        <h2 style="color:white;margin:0;">📋 CIA Retest Application</h2>
        <p style="color:#90caf9;margin:5px 0 0;">New application requires your attention</p>
      </div>
      <div style="padding:20px 0;">
        <p>Dear <strong>{staff_name}</strong>,</p>
        <p>A student has submitted a CIA retest application that requires your approval.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;color:#1a237e;">Student Name</td><td style="padding:10px;">{application.student_name}</td></tr>
          <tr><td style="padding:10px;font-weight:bold;color:#1a237e;">Register No.</td><td style="padding:10px;">{application.register_number}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;color:#1a237e;">Subject</td><td style="padding:10px;">{application.subject.subject_name} ({application.subject.subject_code})</td></tr>
          <tr><td style="padding:10px;font-weight:bold;color:#1a237e;">CIA Number</td><td style="padding:10px;">CIA - {application.cia_number}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;color:#1a237e;">CIA Date</td><td style="padding:10px;">{application.cia_date}</td></tr>
          <tr><td style="padding:10px;font-weight:bold;color:#1a237e;">Submission Type</td><td style="padding:10px;">{application.submission_type.upper()}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;color:#1a237e;">Reason</td><td style="padding:10px;">{application.reason_type.replace('_',' ').title()}</td></tr>
        </table>
        <p>Please login to the CIA Retest Portal to review and take action.</p>
        <div style="text-align:center;margin-top:20px;">
          <a href="http://localhost:5000/staff/dashboard" style="background:#1a237e;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Review Application</a>
        </div>
      </div>
      <p style="color:#999;font-size:12px;text-align:center;margin-top:20px;">CIA Retest Management System | Department Portal</p>
    </div></body></html>
    """
    return send_email(staff_email, subject, body)


def notify_approver(application, approver_email, approver_name, stage):
    subject = f"Action Required: CIA Retest Application - {application.student_name}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f7fb;padding:30px;">
    <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
      <div style="background:linear-gradient(135deg,#1a237e,#283593);padding:20px;border-radius:8px;text-align:center;">
        <h2 style="color:white;margin:0;">✅ Approval Required</h2>
        <p style="color:#90caf9;margin:5px 0 0;">Stage: {stage.replace('_',' ').title()}</p>
      </div>
      <div style="padding:20px 0;">
        <p>Dear <strong>{approver_name}</strong>,</p>
        <p>A CIA retest application has been forwarded to you for approval.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;">Student</td><td style="padding:10px;">{application.student_name} ({application.register_number})</td></tr>
          <tr><td style="padding:10px;font-weight:bold;">Subject</td><td style="padding:10px;">{application.subject.subject_name}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;">CIA</td><td style="padding:10px;">CIA - {application.cia_number} | {application.cia_date}</td></tr>
          <tr><td style="padding:10px;font-weight:bold;">Type</td><td style="padding:10px;">{application.submission_type.upper()} Submission</td></tr>
        </table>
        <div style="text-align:center;margin-top:20px;">
          <a href="http://localhost:5000/{stage.replace('_staff','')}/dashboard" style="background:#1a237e;color:white;padding:12px 30px;border-radius:6px;text-decoration:none;font-weight:bold;">Review Now</a>
        </div>
      </div>
    </div></body></html>
    """
    return send_email(approver_email, subject, body)


def notify_student_final(application):
    status = application.final_status
    color = '#2e7d32' if status == 'approved' else '#c62828'
    icon = '✅' if status == 'approved' else '❌'
    subject = f"CIA Retest Application {status.title()} - {application.subject.subject_name}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f7fb;padding:30px;">
    <div style="max-width:600px;margin:auto;background:white;border-radius:12px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
      <div style="background:{color};padding:20px;border-radius:8px;text-align:center;">
        <h2 style="color:white;margin:0;">{icon} Application {status.title()}</h2>
      </div>
      <div style="padding:20px 0;">
        <p>Dear <strong>{application.student_name}</strong>,</p>
        <p>Your CIA retest application has been <strong style="color:{color};">{status}</strong>.</p>
        <table style="width:100%;border-collapse:collapse;margin:20px 0;">
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;">Subject</td><td style="padding:10px;">{application.subject.subject_name}</td></tr>
          <tr><td style="padding:10px;font-weight:bold;">CIA Number</td><td style="padding:10px;">CIA - {application.cia_number}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;">Subject Staff</td><td style="padding:10px;">{application.staff_remark or 'N/A'}</td></tr>
          <tr><td style="padding:10px;font-weight:bold;">Tutor Remark</td><td style="padding:10px;">{application.tutor_remark or 'N/A'}</td></tr>
          <tr style="background:#f5f7ff;"><td style="padding:10px;font-weight:bold;">HOD Remark</td><td style="padding:10px;">{application.hod_remark or 'N/A'}</td></tr>
          <tr><td style="padding:10px;font-weight:bold;">Coordinator Remark</td><td style="padding:10px;">{application.coordinator_remark or 'N/A'}</td></tr>
        </table>
        {'<p style="color:#2e7d32;"><strong>Please report to the examination hall on the retest date.</strong></p>' if status == 'approved' else '<p style="color:#c62828;">You may contact your department for further assistance.</p>'}
      </div>
      <p style="color:#999;font-size:12px;text-align:center;">CIA Retest Management System</p>
    </div></body></html>
    """
    return send_email(application.student_email, subject, body)
