from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ==================== USER MODELS ====================

class User(UserMixin, db.Model):
    """Base User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='graduate')  # graduate, employer, admin
    account_status = db.Column(db.String(20), default='active')  # active, inactive, suspended
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    graduate_profile = db.relationship('GraduateProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    employer_profile = db.relationship('EmployerProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', cascade='all, delete-orphan')
    admin_logs = db.relationship('AdminLog', backref='admin_user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

# ==================== GRADUATE MODELS ====================

class GraduateProfile(db.Model):
    """Graduate profile information"""
    __tablename__ = 'graduate_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    education_level = db.Column(db.String(100), nullable=True)  # Bachelor, Master, etc.
    institution_name = db.Column(db.String(255), nullable=True)
    course_studied = db.Column(db.String(255), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    career_interest = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    cv_file_path = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_completion = db.Column(db.Float, default=0.0)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    skill_assessments = db.relationship('SkillAssessment', backref='graduate', cascade='all, delete-orphan')
    applications = db.relationship('JobApplication', backref='graduate', cascade='all, delete-orphan')
    matches = db.relationship('MatchingResult', backref='graduate', cascade='all, delete-orphan')
    graduate_skills = db.relationship('GraduateSkill', backref='graduate', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<GraduateProfile {self.user_id}>'

class GraduateSkill(db.Model):
    """Skills possessed by graduates"""
    __tablename__ = 'graduate_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate_profiles.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    proficiency_level = db.Column(db.String(50), default='intermediate')  # beginner, intermediate, advanced, expert
    endorsements = db.Column(db.Integer, default=0)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    skill = db.relationship('Skill', backref='graduate_skills')
    
    def __repr__(self):
        return f'<GraduateSkill {self.graduate_id}-{self.skill_id}>'

# ==================== EMPLOYER MODELS ====================

class EmployerProfile(db.Model):
    """Employer/Company profile"""
    __tablename__ = 'employer_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    industry = db.Column(db.String(255), nullable=True)
    company_size = db.Column(db.String(50), nullable=True)  # startup, small, medium, large, enterprise
    location = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_date = db.Column(db.DateTime, nullable=True)
    subscription_type = db.Column(db.String(50), default='free')  # free, basic, premium
    subscription_end_date = db.Column(db.DateTime, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='employer', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='employer', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EmployerProfile {self.company_name}>'

# ==================== JOB MODELS ====================

class Job(db.Model):
    """Job postings"""
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profiles.id'), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=True)
    required_skills = db.Column(db.String(500), nullable=True)  # Comma-separated skill IDs
    education_required = db.Column(db.String(100), nullable=True)
    job_location = db.Column(db.String(255), nullable=False)
    salary_min = db.Column(db.Float, nullable=True)
    salary_max = db.Column(db.Float, nullable=True)
    job_type = db.Column(db.String(50), nullable=True)  # full-time, part-time, contract
    deadline = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, closed, archived
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    date_closed = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    applications = db.relationship('JobApplication', backref='job', cascade='all, delete-orphan')
    matches = db.relationship('MatchingResult', backref='job', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.job_title}>'

# ==================== SKILLS MODELS ====================

class Skill(db.Model):
    """Available skills in the system"""
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(255), unique=True, nullable=False)
    skill_category = db.Column(db.String(100), nullable=True)  # Programming, Design, Marketing, etc.
    description = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assessments = db.relationship('SkillAssessment', backref='skill', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Skill {self.skill_name}>'

class SkillAssessment(db.Model):
    """Skill assessment test results"""
    __tablename__ = 'skill_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate_profiles.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    test_score = db.Column(db.Float, nullable=True)  # 0-100
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SkillAssessment {self.graduate_id}-{self.skill_id}>'

# ==================== APPLICATION MODELS ====================

class JobApplication(db.Model):
    """Graduate job applications"""
    __tablename__ = 'job_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate_profiles.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    application_status = db.Column(db.String(50), default='applied')  # applied, shortlisted, rejected, accepted, withdrawn
    cover_letter = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('job_id', 'graduate_id', name='uq_job_graduate'),)
    
    def __repr__(self):
        return f'<JobApplication {self.job_id}-{self.graduate_id}>'

# ==================== MATCHING MODELS ====================

class MatchingResult(db.Model):
    """Job-Graduate matching results"""
    __tablename__ = 'matching_results'
    
    id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey('graduate_profiles.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    match_score = db.Column(db.Float, default=0.0)  # 0-100
    skill_match_count = db.Column(db.Integer, default=0)
    location_match = db.Column(db.Boolean, default=False)
    education_match = db.Column(db.Boolean, default=False)
    skill_gap = db.Column(db.String(500), nullable=True)  # Missing skills
    match_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('graduate_id', 'job_id', name='uq_match_graduate_job'),)
    
    def __repr__(self):
        return f'<MatchingResult {self.graduate_id}-{self.job_id}>'

# ==================== NOTIFICATION MODELS ====================

class Notification(db.Model):
    """User notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=True)  # job_match, application_status, system, etc.
    related_job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.user_id}>'

# ==================== PAYMENT MODELS ====================

class Payment(db.Model):
    """Employer subscription payments"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profiles.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD')
    subscription_type = db.Column(db.String(50), nullable=True)  # free, basic, premium
    subscription_duration_days = db.Column(db.Integer, default=30)
    payment_method = db.Column(db.String(50), nullable=True)  # credit_card, paypal, etc.
    transaction_id = db.Column(db.String(255), unique=True, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.employer_id}-{self.transaction_id}>'

# ==================== ADMIN MODELS ====================

class AdminLog(db.Model):
    """Admin activity logs"""
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_performed = db.Column(db.String(255), nullable=False)
    action_details = db.Column(db.Text, nullable=True)
    affected_user_id = db.Column(db.Integer, nullable=True)
    action_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='success')  # success, failed
    
    def __repr__(self):
        return f'<AdminLog {self.admin_id}-{self.action_performed}>'
