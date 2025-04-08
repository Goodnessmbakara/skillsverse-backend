from rest_framework import serializers
from rest_framework import serializers
from .models import Job, CV, Skill, CVEducation, CVWorkExperience, CVContactInfo, JobRecommendation

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['name', 'category']

class CVEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVEducation
        exclude = ('cv',)

class CVWorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVWorkExperience
        exclude = ('cv',)

class CVContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CVContactInfo
        exclude = ('cv', 'id')

class JobSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'company_name', 'location',
            'salary_min', 'salary_max', 'employment_type', 'created_at',
            'slug', 'tags', 'skills', 'company_logo', 'source'
        ]
        read_only_fields = ['created_at', 'slug']

class JobRecommendationSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = JobRecommendation
        fields = ['id', 'job', 'match_score', 'created_at']
        read_only_fields = ['job', 'match_score', 'created_at']
        
class CVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ('file', 'original_filename')
        
    def validate_file(self, value):
        """Validate file extension"""
        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = ['.pdf', '.docx', '.txt']
        if ext not in valid_extensions:
            raise serializers.ValidationError(
                'Unsupported file extension. Please upload a PDF, DOCX, or TXT file.'
            )
        return value

class CVSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    education = CVEducationSerializer(many=True, read_only=True)
    work_experience = CVWorkExperienceSerializer(many=True, read_only=True)
    contact_info = CVContactInfoSerializer(read_only=True)
    recommendations = JobRecommendationSerializer(many=True, read_only=True)
    
    class Meta:
        model = CV
        fields = ('id', 'original_filename', 'uploaded_at', 'status', 
                  'skills', 'education', 'work_experience', 'contact_info', 
                  'recommendations')
    
    def get_skills(self, obj):
        return SkillSerializer(obj.extracted_skills, many=True).data

