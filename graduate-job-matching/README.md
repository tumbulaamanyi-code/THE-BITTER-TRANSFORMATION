# Graduate Job Matching System

A full-stack web application prototype that connects fresh graduates with bachelor's degrees to employers using an intelligent skill-matching engine.

## 🎯 Project Overview

The **Graduate Job Matching System** is an intelligent platform that:
- Connects graduates with job opportunities based on skills
- Provides skill assessments and proficiency tracking
- Uses AI-powered matching algorithm to recommend jobs (0-100 score)
- Manages job applications and hiring workflows
- Includes employer verification and admin controls

## 🛠 Technology Stack

- **Backend:** Python Flask
- **Database:** PostgreSQL (SQLAlchemy ORM)
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Authentication:** Flask-Login with hashed passwords (Werkzeug)
- **API:** RESTful endpoints for matching and candidate search

## 📦 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

### Setup Steps

1. **Clone the repository:**
   ```bash
   cd graduate-job-matching
   ```

2. **Create PostgreSQL database:**
   ```bash
   createdb graduate_job_matching
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Update database URL in `config.py`:**
   ```python
   DATABASE_URL="postgresql://user:password@localhost:5432/graduate_job_matching"
   ```

5. **Seed sample data:**
   ```bash
   python seed_db.py
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Open in browser:**
   ```
   http://127.0.0.1:5000
   ```

## 🔐 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@test.com | 1234 |
| **Graduate** | grad@test.com | 1234 |
| **Employer** | employer@test.com | 1234 |

## 📋 Database Schema

### Users
- Base user table with authentication
- Roles: graduate, employer, admin
- Account status tracking (active, inactive, suspended)

### Graduate Profiles
- Education details (degree, institution, graduation year)
- Career interests and location
- CV file storage
- Profile completion percentage

### Employer Profiles
- Company information
- Verification status
- Subscription management
- Payment history

### Jobs
- Job title, description, requirements
- Required skills (comma-separated IDs)
- Salary range and location
- Application deadline
- Status tracking (active, closed, archived)

### Skills
- Skill catalog with categories
- Programming, Design, Data Science, Business
- Skill descriptions and documentation

### Applications & Matches
- Job applications with status tracking
- Matching results with scores
- Skill gap analysis
- Recommendation engine

## 🧠 Intelligent Matching Algorithm

The system uses a multi-factor matching algorithm:

```python
Match Score = (Skill Matches * 10) + (Location Match * 5) + (Education Match * 10)
Max Score: 100 points
```

**Scoring Factors:**
- **Skill Matching:** Each matching skill = +10 points
- **Location Match:** Graduate location = Job location = +5 points
- **Education Match:** Education level aligned = +10 points
- **Ranking:** Candidates ranked by total match score

## 👥 User Modules

### 1. Graduate Interface
- ✅ Registration & Login
- ✅ Profile management
- ✅ Skill management with proficiency levels
- ✅ Skill assessments and scoring
- ✅ Job search with filters (location, skills)
- ✅ Job application with cover letters
- ✅ Application tracking (status updates)
- ✅ Job recommendations (top 5 matches)
- ✅ Real-time notifications
- ✅ Skill gap analysis

**Key Routes:**
- `/graduate/dashboard` - Main dashboard
- `/graduate/jobs` - Browse jobs
- `/graduate/matches` - See recommendations
- `/graduate/applications` - Track applications
- `/graduate/skills` - Manage skills

### 2. Employer Interface
- ✅ Company registration & verification
- ✅ Company profile management
- ✅ Job posting with skill requirements
- ✅ Candidate search and filtering
- ✅ Skill-based candidate ranking
- ✅ Candidate shortlisting
- ✅ Application management & status updates
- ✅ Analytics dashboard
- ✅ Subscription management

**Key Routes:**
- `/employer/dashboard` - Company overview
- `/employer/post-job` - Create job postings
- `/employer/jobs` - Manage postings
- `/employer/applications` - Manage applications
- `/employer/job/<id>/candidates` - View candidates

### 3. Admin Interface
- ✅ User management
- ✅ Employer verification
- ✅ Job content moderation
- ✅ Account suspension/activation
- ✅ System analytics
- ✅ Activity logging
- ✅ Database backup

**Key Routes:**
- `/admin/dashboard` - Admin overview
- `/admin/users` - Manage users
- `/admin/employers` - Verify employers
- `/admin/jobs` - Moderate jobs
- `/admin/logs` - View activity logs

## 🔌 API Endpoints

### Matching Endpoints
- `POST /api/matches/generate` - Generate all matches
- `GET /api/job/<job_id>/match-candidates` - Get matched candidates
- `GET /api/skill-gap/<grad_id>/<job_id>` - Skill gap analysis

## 📊 Sample Data

When seeded, the database includes:
- **3 Graduates** with skills and assessments
- **2 Employers** verified and ready to post
- **1 Admin** account
- **17 Skills** across 4 categories
- **5 Sample Jobs** with skill requirements
- **4 Job Applications**
- Pre-generated matching results

## 🚀 Features Implemented

✅ **Intelligent Job Matching** - AI-powered skill analysis
✅ **Skill Assessments** - Test and validate proficiency
✅ **Real-time Notifications** - Job match & application alerts
✅ **Application Tracking** - Full lifecycle management
✅ **Analytics Dashboard** - Metrics for all user types
✅ **Responsive Design** - Mobile-friendly UI
✅ **Role-based Access** - Different dashboards per role
✅ **Secure Authentication** - Password hashing & session management
✅ **Database Relationships** - Normalized PostgreSQL schema
✅ **REST API** - Programmatic access

## 📁 Project Structure

```
graduate-job-matching/
├── app.py                  # Main Flask application (40+ routes)
├── models.py              # Database models (12 tables)
├── config.py              # Configuration management
├── matching_engine.py     # Intelligent matching algorithm
├── seed_db.py            # Sample data seeding
├── requirements.txt       # Python dependencies
└── templates/
    ├── base.html         # Base template with Bootstrap 5
    ├── index.html        # Landing page
    ├── auth/
    │   ├── login.html
    │   └── register.html
    ├── graduate/
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── skills.html
    │   ├── jobs.html
    │   ├── job_detail.html
    │   ├── applications.html
    │   ├── matches.html
    │   └── notifications.html
    ├── employer/
    │   ├── dashboard.html
    │   ├── profile.html
    │   ├── post_job.html
    │   ├── jobs.html
    │   ├── candidates.html
    │   └── applications.html
    └── admin/
        ├── dashboard.html
        ├── users.html
        ├── employers.html
        ├── jobs.html
        └── logs.html
```

## 💡 How the Matching Engine Works

```python
# Example: Match graduate to job
graduate_skills = ['Python', 'JavaScript', 'SQL']
job_required = ['Python', 'SQL', 'React']

# Matching process:
# 1. Python match found → +10 points
# 2. SQL match found → +10 points
# 3. React NOT found → skill gap
# Location match → +5 points
# Education match → +10 points

# Final Score: 10 + 10 + 5 + 10 = 35/100 (35% match)
```

## 🔒 Security Features

- ✅ Password hashing with Werkzeug
- ✅ Session-based authentication
- ✅ Role-based access control
- ✅ Account status verification
- ✅ Admin action logging
- ✅ CSRF protection via Flask-WTF

## 📈 Future Enhancements

- [ ] Email notifications integration
- [ ] Advanced filtering and search
- [ ] Interview scheduling system
- [ ] Salary prediction ML model
- [ ] LinkedIn integration
- [ ] Mobile app (Flutter/React Native)
- [ ] Video interview platform
- [ ] Skill verification system

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## 📝 License

MIT License - See LICENSE file for details

## 👨‍💼 Support

For issues and questions:
- Create an issue on GitHub
- Contact: support@jobmatcher.com
- Documentation: See README and inline code comments

---

**Built with ❤️ for connecting graduates with opportunities**
