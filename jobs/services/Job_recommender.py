import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from jobs.models import Job, JobRecommendation, CV, JobActivity

class JobRecommender:
    """Service class for recommending jobs based on CV data and user activities"""
    
    def __init__(self):
        """Initialize the job recommender with job listings from database"""
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.job_listings = []
        self.job_vectors = None
        self.job_id_to_index = {}
        self.update_job_vectors()
        # Clean up old recommendations with low scores
        JobRecommendation.objects.filter(match_score__lt=30).delete()
    
    def update_job_vectors(self):
        """Update job vectors and index mapping from database"""
        job_listings = Job.objects.all()
        if not job_listings.exists():
            self.job_listings = []
            self.job_vectors = None
            self.job_id_to_index = {}
            return
        
        self.job_listings = list(job_listings)
        self.job_id_to_index = {job.id: idx for idx, job in enumerate(self.job_listings)}
        job_texts = []
        
        for job in self.job_listings:
            job_text = f"{job.title} {job.description} "
            job_text += " ".join(skill.name for skill in job.skills.all())
            job_texts.append(job_text)
        
        self.job_vectors = self.vectorizer.fit_transform(job_texts)
    
    def recommend_jobs_for_cv(self, cv_id, num_recommendations=10):
        """Recommend jobs by combining CV and user activity data"""
        try:
            cv_obj = CV.objects.get(id=cv_id)
            user = cv_obj.created_by  # Adjust based on CV's user field
            
            JobRecommendation.objects.filter(cv=cv_obj).delete()
            
            if not self.job_listings or self.job_vectors is None:
                return []
            
            # CV-based similarity
            cv_text = self._extract_cv_text(cv_obj)
            cv_vector = self.vectorizer.transform([cv_text])
            cv_scores = cosine_similarity(cv_vector, self.job_vectors).flatten()
            
            # Activity-based similarity
            activity_scores = self._calculate_activity_scores(user)
            
            # Combine scores
            combined_scores = 0.7 * cv_scores + 0.3 * activity_scores
            return self._save_recommendations(cv_obj, combined_scores, num_recommendations)
        
        except Exception as e:
            print(f"Error recommending jobs: {str(e)}")
            return []
    
    def _extract_cv_text(self, cv_obj):
        """Extract skills and experience from CV"""
        cv_text = " ".join(skill.name for skill in cv_obj.extracted_skills.all())
        for exp in cv_obj.work_experience.all():
            cv_text += f" {exp.title or ''} {exp.description or ''}"
        return cv_text
    
    def _calculate_activity_scores(self, user):
        """Calculate scores based on user's job interactions"""
        activity_scores = np.zeros(len(self.job_listings))
        activities = JobActivity.objects.filter(user=user)
        
        if activities.exists():
            activity_weights = {'applied': 2.0, 'saved': 1.5, 'viewed': 1.0}
            user_activity_vector = csr_matrix((1, self.job_vectors.shape[1]))
            
            for activity in activities:
                job_id = activity.job.id
                if job_id in self.job_id_to_index:
                    idx = self.job_id_to_index[job_id]
                    weight = activity_weights.get(activity.activity_type, 1.0)
                    user_activity_vector += self.job_vectors[idx] * weight
            
            if user_activity_vector.sum() > 0:
                activity_scores = cosine_similarity(user_activity_vector, self.job_vectors).flatten()
        
        return activity_scores
    
    def _save_recommendations(self, cv_obj, scores, num_recommendations):
        """Save top recommendations to the database"""
        recommendations = []
        sorted_indices = scores.argsort()[::-1]
        
        for i, idx in enumerate(sorted_indices):
            if i >= num_recommendations:
                break
            score = scores[idx]
            if score < 0.1:
                continue
            job = self.job_listings[idx]
            recommendation = JobRecommendation.objects.create(
                cv=cv_obj, job=job, match_score=round(score * 100, 1)
            recommendations.append(recommendation)
        
        return recommendations