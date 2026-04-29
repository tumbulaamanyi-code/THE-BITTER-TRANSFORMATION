from models import db, Job, GraduateProfile, GraduateSkill, MatchingResult, Skill
from sqlalchemy import and_, or_

class JobMatchingEngine:
    """Core matching logic for jobs and graduates"""
    
    @staticmethod
    def calculate_match_score(graduate_id, job_id):
        """
        Calculate match score between a graduate and a job.
        
        Scoring Logic:
        - Each skill match: +10 points
        - Location match: +5 points
        - Education match: +10 points
        - Max score: 100
        """
        
        graduate = GraduateProfile.query.get(graduate_id)
        job = Job.query.get(job_id)
        
        if not graduate or not job:
            return None
        
        score = 0
        skill_match_count = 0
        location_match = False
        education_match = False
        missing_skills = []
        
        # Parse required skills from job
        required_skill_ids = [int(sid.strip()) for sid in job.required_skills.split(',') if sid.strip()]
        required_skills = Skill.query.filter(Skill.id.in_(required_skill_ids)).all() if required_skill_ids else []
        required_skill_names = [s.skill_name for s in required_skills]
        
        # Get graduate's skills
        grad_skills = GraduateSkill.query.filter(GraduateSkill.graduate_id == graduate_id).all()
        grad_skill_names = [gs.skill.skill_name for gs in grad_skills]
        
        # Calculate skill matches
        for required_skill in required_skill_names:
            if required_skill in grad_skill_names:
                score += 10
                skill_match_count += 1
            else:
                missing_skills.append(required_skill)
        
        # Location match
        if graduate.location and job.job_location:
            if graduate.location.lower() == job.job_location.lower():
                score += 5
                location_match = True
        
        # Education match
        if graduate.education_level and job.education_required:
            if graduate.education_level.lower() == job.education_required.lower():
                score += 10
                education_match = True
        
        # Cap score at 100
        score = min(score, 100)
        
        return {
            'score': score,
            'skill_match_count': skill_match_count,
            'location_match': location_match,
            'education_match': education_match,
            'missing_skills': ', '.join(missing_skills) if missing_skills else None,
            'total_required_skills': len(required_skill_names),
            'graduate_skills_count': len(grad_skill_names)
        }
    
    @staticmethod
    def find_jobs_for_graduate(graduate_id, limit=5):
        """
        Find top N jobs for a graduate based on skill matching.
        Returns list of (job, match_score) tuples sorted by score descending.
        """
        graduate = GraduateProfile.query.get(graduate_id)
        if not graduate:
            return []
        
        active_jobs = Job.query.filter(Job.status == 'active').all()
        
        job_matches = []
        for job in active_jobs:
            match_data = JobMatchingEngine.calculate_match_score(graduate_id, job.id)
            if match_data:
                job_matches.append((job, match_data))
        
        # Sort by match score descending
        job_matches.sort(key=lambda x: x[1]['score'], reverse=True)
        
        return job_matches[:limit]
    
    @staticmethod
    def find_candidates_for_job(job_id, limit=10):
        """
        Find top N candidates for a job based on skill matching.
        Returns list of (graduate, match_score) tuples sorted by score descending.
        """
        job = Job.query.get(job_id)
        if not job:
            return []
        
        all_graduates = GraduateProfile.query.all()
        
        candidate_matches = []
        for graduate in all_graduates:
            match_data = JobMatchingEngine.calculate_match_score(graduate.id, job_id)
            if match_data:
                candidate_matches.append((graduate, match_data))
        
        # Sort by match score descending
        candidate_matches.sort(key=lambda x: x[1]['score'], reverse=True)
        
        return candidate_matches[:limit]
    
    @staticmethod
    def save_matching_results(graduate_id, job_id):
        """
        Calculate and save matching results to database.
        """
        match_data = JobMatchingEngine.calculate_match_score(graduate_id, job_id)
        
        if not match_data:
            return None
        
        # Check if match already exists
        existing_match = MatchingResult.query.filter(
            and_(
                MatchingResult.graduate_id == graduate_id,
                MatchingResult.job_id == job_id
            )
        ).first()
        
        if existing_match:
            # Update existing match
            existing_match.match_score = match_data['score']
            existing_match.skill_match_count = match_data['skill_match_count']
            existing_match.location_match = match_data['location_match']
            existing_match.education_match = match_data['education_match']
            existing_match.skill_gap = match_data['missing_skills']
        else:
            # Create new match
            existing_match = MatchingResult(
                graduate_id=graduate_id,
                job_id=job_id,
                match_score=match_data['score'],
                skill_match_count=match_data['skill_match_count'],
                location_match=match_data['location_match'],
                education_match=match_data['education_match'],
                skill_gap=match_data['missing_skills']
            )
            db.session.add(existing_match)
        
        db.session.commit()
        return existing_match
    
    @staticmethod
    def generate_all_matches():
        """
        Generate matching results for all graduate-job combinations.
        Useful for bulk processing.
        """
        graduates = GraduateProfile.query.all()
        jobs = Job.query.filter(Job.status == 'active').all()
        
        match_count = 0
        for graduate in graduates:
            for job in jobs:
                result = JobMatchingEngine.save_matching_results(graduate.id, job.id)
                if result:
                    match_count += 1
        
        return match_count
    
    @staticmethod
    def get_skill_gap_analysis(graduate_id, job_id):
        """
        Provide detailed skill gap analysis for a graduate for a specific job.
        """
        match_data = JobMatchingEngine.calculate_match_score(graduate_id, job_id)
        
        if not match_data:
            return None
        
        return {
            'current_match_score': match_data['score'],
            'skills_matched': match_data['skill_match_count'],
            'skills_required': match_data['total_required_skills'],
            'skills_missing': match_data['missing_skills'],
            'graduate_total_skills': match_data['graduate_skills_count'],
            'match_percentage': (match_data['skill_match_count'] / match_data['total_required_skills'] * 100) 
                               if match_data['total_required_skills'] > 0 else 0
        }
    
    @staticmethod
    def get_recommended_jobs_for_graduate(graduate_id, min_score=50):
        """
        Get jobs recommended for a graduate based on match score threshold.
        """
        matches = MatchingResult.query.filter(
            and_(
                MatchingResult.graduate_id == graduate_id,
                MatchingResult.match_score >= min_score
            )
        ).order_by(MatchingResult.match_score.desc()).all()
        
        return [(m.job, {
            'score': m.match_score,
            'skill_match_count': m.skill_match_count,
            'location_match': m.location_match,
            'education_match': m.education_match,
            'missing_skills': m.skill_gap
        }) for m in matches]
    
    @staticmethod
    def get_top_candidates_for_job(job_id, min_score=50):
        """
        Get top candidates for a job based on match score threshold.
        """
        matches = MatchingResult.query.filter(
            and_(
                MatchingResult.job_id == job_id,
                MatchingResult.match_score >= min_score
            )
        ).order_by(MatchingResult.match_score.desc()).all()
        
        return [(m.graduate, {
            'score': m.match_score,
            'skill_match_count': m.skill_match_count,
            'location_match': m.location_match,
            'education_match': m.education_match,
            'missing_skills': m.skill_gap
        }) for m in matches]
