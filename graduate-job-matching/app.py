from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import get_config
from models import db, User, GraduateProfile, EmployerProfile, Job, Skill, GraduateSkill, SkillAssessment, JobApplication, MatchingResult, Notification, AdminLog
from matching_engine import JobMatchingEngine
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(get_config())

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== HOME & AUTH ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        if current_user.role == 'graduate':
            return redirect(url_for('graduate_dashboard'))
        elif current_user.role == 'employer':
            return redirect(url_for('employer_dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        role = request.form.get('role', 'graduate')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone_number = request.form.get('phone_number')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            role=role,
            account_status='active'
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create role-specific profile
            if role == 'graduate':
                grad_profile = GraduateProfile(user_id=user.id)
                db.session.add(grad_profile)
                db.session.commit()
                flash('Graduate account created successfully! Please log in.', 'success')
            elif role == 'employer':
                company_name = request.form.get('company_name')
                emp_profile = EmployerProfile(user_id=user.id, company_name=company_name)
                db.session.add(emp_profile)
                db.session.commit()
                flash('Employer account created! Awaiting verification.', 'success')
            
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'error')
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if user.account_status == 'suspended':
                flash('Your account has been suspended.', 'error')
                return redirect(url_for('login'))
            
            login_user(user, remember=request.form.get('remember'))
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on role
            if user.role == 'graduate':
                return redirect(url_for('graduate_dashboard'))
            elif user.role == 'employer':
                return redirect(url_for('employer_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

# ==================== GRADUATE ROUTES ====================

@app.route('/graduate/dashboard')
@login_required
def graduate_dashboard():
    """Graduate dashboard"""
    if current_user.role != 'graduate':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    grad_profile = current_user.graduate_profile
    
    # Get statistics
    total_applications = JobApplication.query.filter_by(graduate_id=grad_profile.id).count()
    shortlisted = JobApplication.query.filter_by(graduate_id=grad_profile.id, application_status='shortlisted').count()
    skills_count = GraduateSkill.query.filter_by(graduate_id=grad_profile.id).count()
    
    # Get top 5 recommended jobs
    recommended_jobs = JobMatchingEngine.find_jobs_for_graduate(grad_profile.id, limit=5)
    
    return render_template(
        'graduate/dashboard.html',
        grad_profile=grad_profile,
        total_applications=total_applications,
        shortlisted=shortlisted,
        skills_count=skills_count,
        recommended_jobs=recommended_jobs
    )

@app.route('/graduate/profile', methods=['GET', 'POST'])
@login_required
def graduate_profile():
    """Graduate profile management"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    grad_profile = current_user.graduate_profile
    
    if request.method == 'POST':
        grad_profile.education_level = request.form.get('education_level')
        grad_profile.institution_name = request.form.get('institution_name')
        grad_profile.course_studied = request.form.get('course_studied')
        grad_profile.graduation_year = request.form.get('graduation_year')
        grad_profile.career_interest = request.form.get('career_interest')
        grad_profile.location = request.form.get('location')
        grad_profile.bio = request.form.get('bio')
        grad_profile.date_updated = datetime.utcnow()
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('graduate_profile'))
    
    return render_template('graduate/profile.html', grad_profile=grad_profile)

@app.route('/graduate/skills')
@login_required
def graduate_skills():
    """Graduate skills management"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    grad_profile = current_user.graduate_profile
    grad_skills = GraduateSkill.query.filter_by(graduate_id=grad_profile.id).all()
    all_skills = Skill.query.all()
    
    return render_template('graduate/skills.html', grad_skills=grad_skills, all_skills=all_skills)

@app.route('/graduate/add-skill', methods=['POST'])
@login_required
def add_skill():
    """Add skill to graduate profile"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    skill_id = request.form.get('skill_id')
    proficiency_level = request.form.get('proficiency_level', 'intermediate')
    
    existing = GraduateSkill.query.filter_by(
        graduate_id=current_user.graduate_profile.id,
        skill_id=skill_id
    ).first()
    
    if not existing:
        grad_skill = GraduateSkill(
            graduate_id=current_user.graduate_profile.id,
            skill_id=skill_id,
            proficiency_level=proficiency_level
        )
        db.session.add(grad_skill)
        db.session.commit()
        flash('Skill added successfully!', 'success')
    else:
        flash('Skill already added!', 'warning')
    
    return redirect(url_for('graduate_skills'))

@app.route('/graduate/jobs')
@login_required
def graduate_jobs():
    """Search and browse jobs"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    # Filter jobs
    location_filter = request.args.get('location', '')
    skill_filter = request.args.get('skill', '')
    
    query = Job.query.filter_by(status='active')
    
    if location_filter:
        query = query.filter(Job.job_location.ilike(f'%{location_filter}%'))
    
    jobs = query.all()
    
    # Add match scores
    grad_profile = current_user.graduate_profile
    jobs_with_scores = []
    for job in jobs:
        match_data = JobMatchingEngine.calculate_match_score(grad_profile.id, job.id)
        jobs_with_scores.append({
            'job': job,
            'match_score': match_data['score'] if match_data else 0,
            'match_data': match_data
        })
    
    # Sort by match score
    jobs_with_scores.sort(key=lambda x: x['match_score'], reverse=True)
    
    return render_template('graduate/jobs.html', jobs_with_scores=jobs_with_scores)

@app.route('/graduate/job/<int:job_id>')
@login_required
def job_detail(job_id):
    """View job details"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    grad_profile = current_user.graduate_profile
    
    # Get match data
    match_data = JobMatchingEngine.calculate_match_score(grad_profile.id, job_id)
    
    # Check if already applied
    application = JobApplication.query.filter_by(
        job_id=job_id,
        graduate_id=grad_profile.id
    ).first()
    
    return render_template('graduate/job_detail.html', job=job, match_data=match_data, application=application)

@app.route('/graduate/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    """Apply for a job"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    grad_profile = current_user.graduate_profile
    cover_letter = request.form.get('cover_letter', '')
    
    # Check if already applied
    existing = JobApplication.query.filter_by(
        job_id=job_id,
        graduate_id=grad_profile.id
    ).first()
    
    if existing:
        flash('You have already applied for this job!', 'warning')
        return redirect(url_for('job_detail', job_id=job_id))
    
    application = JobApplication(
        job_id=job_id,
        graduate_id=grad_profile.id,
        cover_letter=cover_letter,
        application_status='applied'
    )
    
    db.session.add(application)
    db.session.commit()
    
    # Save matching result
    JobMatchingEngine.save_matching_results(grad_profile.id, job_id)
    
    # Notify employer
    employer = job.employer.user
    notification = Notification(
        user_id=employer.id,
        message=f'{current_user.full_name} applied for {job.job_title}',
        notification_type='new_application',
        related_job_id=job_id
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('graduate_applications'))

@app.route('/graduate/applications')
@login_required
def graduate_applications():
    """View graduate's applications"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    grad_profile = current_user.graduate_profile
    applications = JobApplication.query.filter_by(graduate_id=grad_profile.id).all()
    
    return render_template('graduate/applications.html', applications=applications)

@app.route('/graduate/matches')
@login_required
def graduate_matches():
    """View job recommendations/matches"""
    if current_user.role != 'graduate':
        return redirect(url_for('index'))
    
    grad_profile = current_user.graduate_profile
    recommended_jobs = JobMatchingEngine.find_jobs_for_graduate(grad_profile.id, limit=10)
    
    return render_template('graduate/matches.html', recommended_jobs=recommended_jobs)

@app.route('/graduate/notifications')
@login_required
def graduate_notifications():
    """View graduate notifications"""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date_sent.desc()).all()
    return render_template('graduate/notifications.html', notifications=notifications)

# ==================== EMPLOYER ROUTES ====================

@app.route('/employer/dashboard')
@login_required
def employer_dashboard():
    """Employer dashboard"""
    if current_user.role != 'employer':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    emp_profile = current_user.employer_profile
    
    # Statistics
    total_jobs = Job.query.filter_by(employer_id=emp_profile.id).count()
    active_jobs = Job.query.filter_by(employer_id=emp_profile.id, status='active').count()
    total_applications = JobApplication.query.filter(
        JobApplication.job_id.in_([j.id for j in emp_profile.jobs])
    ).count()
    
    return render_template(
        'employer/dashboard.html',
        emp_profile=emp_profile,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications
    )

@app.route('/employer/profile', methods=['GET', 'POST'])
@login_required
def employer_profile():
    """Employer profile management"""
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    
    emp_profile = current_user.employer_profile
    
    if request.method == 'POST':
        emp_profile.company_name = request.form.get('company_name')
        emp_profile.industry = request.form.get('industry')
        emp_profile.company_size = request.form.get('company_size')
        emp_profile.location = request.form.get('location')
        emp_profile.website = request.form.get('website')
        emp_profile.description = request.form.get('description')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('employer_profile'))
    
    return render_template('employer/profile.html', emp_profile=emp_profile)

@app.route('/employer/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    """Post a new job"""
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        skills = request.form.getlist('skills')
        skill_ids = ','.join([str(s) for s in skills])
        
        job = Job(
            employer_id=current_user.employer_profile.id,
            job_title=request.form.get('job_title'),
            job_description=request.form.get('job_description'),
            required_skills=skill_ids,
            education_required=request.form.get('education_required'),
            job_location=request.form.get('job_location'),
            salary_min=request.form.get('salary_min'),
            salary_max=request.form.get('salary_max'),
            job_type=request.form.get('job_type'),
            deadline=datetime.fromisoformat(request.form.get('deadline')) if request.form.get('deadline') else None,
            status='active'
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('employer_jobs'))
    
    skills = Skill.query.all()
    return render_template('employer/post_job.html', skills=skills)

@app.route('/employer/jobs')
@login_required
def employer_jobs():
    """View employer's posted jobs"""
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    
    jobs = Job.query.filter_by(employer_id=current_user.employer_profile.id).all()
    return render_template('employer/jobs.html', jobs=jobs)

@app.route('/employer/job/<int:job_id>/candidates')
@login_required
def job_candidates(job_id):
    """View candidates for a job"""
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    
    if job.employer_id != current_user.employer_profile.id:
        flash('Access denied!', 'error')
        return redirect(url_for('employer_dashboard'))
    
    # Get top candidates
    top_candidates = JobMatchingEngine.find_candidates_for_job(job_id, limit=10)
    
    return render_template('employer/candidates.html', job=job, top_candidates=top_candidates)

@app.route('/employer/applications')
@login_required
def employer_applications():
    """View all applications"""
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    
    emp_jobs = [j.id for j in current_user.employer_profile.jobs]
    applications = JobApplication.query.filter(JobApplication.job_id.in_(emp_jobs)).all()
    
    return render_template('employer/applications.html', applications=applications)

@app.route('/employer/application/<int:app_id>/update', methods=['POST'])
@login_required
def update_application_status(app_id):
    """Update application status"""
    if current_user.role != 'employer':
        return redirect(url_for('index'))
    
    application = JobApplication.query.get_or_404(app_id)
    new_status = request.form.get('status')
    
    application.application_status = new_status
    application.last_updated = datetime.utcnow()
    db.session.commit()
    
    # Notify graduate
    notification = Notification(
        user_id=application.graduate.user_id,
        message=f'Your application status for {application.job.job_title} is now: {new_status}',
        notification_type='application_status',
        related_job_id=application.job_id
    )
    db.session.add(notification)
    db.session.commit()
    
    flash('Application status updated!', 'success')
    return redirect(request.referrer or url_for('employer_applications'))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('index'))
    
    total_users = User.query.count()
    total_graduates = User.query.filter_by(role='graduate').count()
    total_employers = User.query.filter_by(role='employer').count()
    total_jobs = Job.query.count()
    active_jobs = Job.query.filter_by(status='active').count()
    total_applications = JobApplication.query.count()
    total_matches = MatchingResult.query.count()
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_graduates=total_graduates,
        total_employers=total_employers,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_applications=total_applications,
        total_matches=total_matches
    )

@app.route('/admin/users')
@login_required
def admin_users():
    """Manage users"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>/suspend', methods=['POST'])
@login_required
def suspend_user(user_id):
    """Suspend a user"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.account_status = 'suspended'
    
    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action_performed='suspend_user',
        affected_user_id=user_id
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'User {user.email} suspended!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/employers')
@login_required
def admin_employers():
    """Manage employer verification"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    employers = EmployerProfile.query.all()
    return render_template('admin/employers.html', employers=employers)

@app.route('/admin/employer/<int:emp_id>/verify', methods=['POST'])
@login_required
def verify_employer(emp_id):
    """Verify an employer"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    employer = EmployerProfile.query.get_or_404(emp_id)
    employer.is_verified = True
    employer.verification_date = datetime.utcnow()
    
    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action_performed='verify_employer',
        affected_user_id=employer.user_id
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Employer {employer.company_name} verified!', 'success')
    return redirect(url_for('admin_employers'))

@app.route('/admin/jobs')
@login_required
def admin_jobs():
    """Manage jobs"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    jobs = Job.query.all()
    return render_template('admin/jobs.html', jobs=jobs)

@app.route('/admin/job/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    """Delete a job"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    job = Job.query.get_or_404(job_id)
    job_title = job.job_title
    
    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action_performed='delete_job',
        action_details=f'Deleted job: {job_title}'
    )
    
    db.session.delete(job)
    db.session.add(log)
    db.session.commit()
    
    flash(f'Job "{job_title}" deleted!', 'success')
    return redirect(url_for('admin_jobs'))

@app.route('/admin/logs')
@login_required
def admin_logs():
    """View admin activity logs"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    logs = AdminLog.query.order_by(AdminLog.action_date.desc()).all()
    return render_template('admin/logs.html', logs=logs)

@app.route('/admin/backup', methods=['POST'])
@login_required
def backup_database():
    """Trigger database backup"""
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    # Log action
    log = AdminLog(
        admin_id=current_user.id,
        action_performed='database_backup',
        action_details='Database backup initiated'
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Database backup initiated!', 'success')
    return redirect(url_for('admin_dashboard'))

# ==================== API ROUTES ====================

@app.route('/api/matches/generate', methods=['POST'])
@login_required
def api_generate_matches():
    """API endpoint to generate all matches"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        match_count = JobMatchingEngine.generate_all_matches()
        return jsonify({'success': True, 'matches_generated': match_count}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/job/<int:job_id>/match-candidates', methods=['GET'])
@login_required
def api_job_candidates(job_id):
    """API endpoint to get matched candidates for a job"""
    if current_user.role != 'employer':
        return jsonify({'error': 'Unauthorized'}), 401
    
    top_candidates = JobMatchingEngine.find_candidates_for_job(job_id, limit=10)
    
    candidates_data = [{
        'graduate_id': grad.id,
        'name': grad.user.full_name,
        'email': grad.user.email,
        'location': grad.location,
        'match_score': match_data['score'],
        'skill_matches': match_data['skill_match_count'],
        'location_match': match_data['location_match'],
        'education_match': match_data['education_match']
    } for grad, match_data in top_candidates]
    
    return jsonify({'candidates': candidates_data}), 200

@app.route('/api/skill-gap/<int:grad_id>/<int:job_id>', methods=['GET'])
@login_required
def api_skill_gap(grad_id, job_id):
    """API endpoint for skill gap analysis"""
    gap_analysis = JobMatchingEngine.get_skill_gap_analysis(grad_id, job_id)
    
    if gap_analysis:
        return jsonify(gap_analysis), 200
    else:
        return jsonify({'error': 'Graduate or job not found'}), 404

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500

# ==================== CLI COMMANDS ====================

@app.shell_context_processor
def make_shell_context():
    """Add models to shell context"""
    return {
        'db': db,
        'User': User,
        'GraduateProfile': GraduateProfile,
        'EmployerProfile': EmployerProfile,
        'Job': Job,
        'Skill': Skill,
        'GraduateSkill': GraduateSkill,
        'SkillAssessment': SkillAssessment,
        'JobApplication': JobApplication,
        'MatchingResult': MatchingResult,
        'Notification': Notification,
        'AdminLog': AdminLog
    }

# ==================== MAIN ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)
