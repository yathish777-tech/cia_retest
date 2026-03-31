from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    register_number = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum('student','subject_staff','tutor','hod','coordinator','admin'), default='student')
    department = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(150), nullable=False)
    subject_code = db.Column(db.String(20), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff = db.relationship('User', foreign_keys=[staff_id], backref='subjects_teaching')


class CIADate(db.Model):
    __tablename__ = 'cia_dates'
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    cia_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    exam_date = db.Column(db.Date, nullable=False)
    retest_date = db.Column(db.Date, nullable=True)
    semester = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(20), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', backref='cia_dates')
    creator = db.relationship('User', foreign_keys=[created_by])


class RetestApplication(db.Model):
    __tablename__ = 'retest_applications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    register_number = db.Column(db.String(20), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    student_email = db.Column(db.String(150), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    semester = db.Column(db.Integer, nullable=False)
    cia_number = db.Column(db.Integer, nullable=False)
    cia_date = db.Column(db.Date, nullable=False)
    reason_type = db.Column(db.Enum('health_issues','on_duty','others'), nullable=False)
    reason_detail = db.Column(db.Text, nullable=True)
    submission_type = db.Column(db.Enum('pre','late'), nullable=False, default='pre')
    
    # Approval chain statuses
    staff_status = db.Column(db.Enum('pending','approved','rejected'), default='pending')
    staff_remark = db.Column(db.Text, nullable=True)
    staff_action_time = db.Column(db.DateTime, nullable=True)

    tutor_status = db.Column(db.Enum('pending','approved','rejected'), default='pending')
    tutor_remark = db.Column(db.Text, nullable=True)
    tutor_action_time = db.Column(db.DateTime, nullable=True)

    hod_status = db.Column(db.Enum('pending','approved','rejected'), default='pending')
    hod_remark = db.Column(db.Text, nullable=True)
    hod_action_time = db.Column(db.DateTime, nullable=True)

    coordinator_status = db.Column(db.Enum('pending','approved','rejected'), default='pending')
    coordinator_remark = db.Column(db.Text, nullable=True)
    coordinator_action_time = db.Column(db.DateTime, nullable=True)

    final_status = db.Column(db.Enum('pending','approved','rejected'), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_id], backref='applications')
    subject = db.relationship('Subject', foreign_keys=[subject_id], backref='applications')
    staff = db.relationship('User', foreign_keys=[staff_id], backref='staff_applications')
    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='tutor_applications')

    def current_stage(self):
        """Return the current pending stage of the application."""
        if self.staff_status == 'pending':
            return 'subject_staff'
        elif self.staff_status == 'approved' and self.tutor_status == 'pending':
            return 'tutor'
        elif self.submission_type == 'pre':
            if self.tutor_status == 'approved' and self.hod_status == 'pending':
                return 'hod'
            elif self.hod_status == 'approved' and self.coordinator_status == 'pending':
                return 'coordinator'
        elif self.submission_type == 'late':
            if self.tutor_status == 'approved' and self.coordinator_status == 'pending':
                return 'coordinator'
            elif self.coordinator_status == 'approved' and self.hod_status == 'pending':
                return 'hod'
        return 'completed'


class TutorStudentMapping(db.Model):
    __tablename__ = 'tutor_student_mapping'
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tutor = db.relationship('User', foreign_keys=[tutor_id], backref='tutored_students')
    student = db.relationship('User', foreign_keys=[student_id], backref='tutor_mappings')
