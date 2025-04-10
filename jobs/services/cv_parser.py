import os
import re
import json
import spacy
import pdfplumber
from docx import Document
from pathlib import Path
from datetime import datetime
from django.conf import settings
from jobs.models import Skill, CV, CVEducation, CVWorkExperience, CVContactInfo

class CVParser:
    """Service class for parsing CVs and extracting information"""
    
    def __init__(self):
        """Initialize the CV parser"""
        # Load NLP model
        self.nlp = spacy.load("en_core_web_lg")
        
        # Initialize skill extractor with comprehensive database
        self.skills_by_category = self._load_skills_database()
        self.all_skills = self._create_skill_pattern()
        
        # Contact pattern for email and phone extraction
        self.contact_pattern = re.compile(
            r'''
            (?:mailto:|tel:)?
            (?P<contact>
                [\w\.-]+@[\w\.-]+(?:\.\w+)+  # Email pattern
                |
                (?:\+?\d{1,3}[-\.\s]?)?(?:\(?\d{3}\)?[-\.\s]?)?\d{3}[-\.\s]?\d{4}  # Phone pattern
            )
            ''', 
            re.VERBOSE
        )
    
    def _load_skills_database(self):
        """Load comprehensive skills database from database or fallback to file"""
        skills_dict = {}
        
        # Try to get skills from database first
        db_skills = Skill.objects.all()
        
        if db_skills.exists():
            # Group skills by category
            for skill in db_skills:
                if skill.category not in skills_dict:
                    skills_dict[skill.category] = []
                skills_dict[skill.category].append(skill.name)
            db_skills.save()
        else:
            # Fallback to JSON file if database is empty
            skills_file = os.path.join(settings.BASE_DIR, 'parser_app', 'data', 'skills_database.json')
            
            if os.path.exists(skills_file):
                with open(skills_file, 'r', encoding='utf-8') as f:
                    skills_dict = json.load(f)
                
                # Populate database with skills from file
                for category, skills in skills_dict.items():
                    for skill_name in skills:
                        Skill.objects.get_or_create(name=skill_name, category=category)
            else:
                # Hardcoded fallback if neither database nor file exists
                skills_dict = {
                    "programming_languages": [
                        "Python", "Java", "JavaScript", "TypeScript", "C\\+\\+", "C#", "PHP", "Ruby", "Go", "Swift",
                        "Kotlin", "Rust", "Scala", "R", "MATLAB", "Perl", "Shell", "SQL", "HTML", "CSS"
                    ],
                    "frameworks_libraries": [
                        "React", "Angular", "Vue", "Node.js", "Django", "Flask", "Spring", "Express",
                        "ASP\\.NET", "Ruby on Rails", "Laravel", "Symfony", "jQuery", "Bootstrap", "TensorFlow",
                        "PyTorch", "Keras", "Pandas", "NumPy", "SciPy"
                    ],
                    "databases": [
                        "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Oracle", "SQL Server", "Redis", "Cassandra",
                        "DynamoDB", "Firebase", "ElasticSearch", "Neo4j", "MariaDB"
                    ],
                    "devops_cloud": [
                        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Jenkins", "GitLab CI", "Travis CI",
                        "Terraform", "Ansible", "Puppet", "Chef", "Nginx", "Apache", "Linux", "Unix", "Windows Server"
                    ],
                    "data_science_ml": [
                        "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
                        "Data Analysis", "Data Science", "Big Data", "Hadoop", "Spark", "Statistics",
                        "Predictive Modeling", "A/B Testing", "Feature Engineering", "Data Visualization",
                        "Reinforcement Learning", "Time Series Analysis"
                    ],
                    "soft_skills": [
                        "Leadership", "Communication", "Teamwork", "Problem Solving", "Critical Thinking",
                        "Project Management", "Time Management", "Adaptability", "Creativity", "Collaboration",
                        "Emotional Intelligence", "Presentation Skills", "Negotiation", "Conflict Resolution",
                        "time management", "analytical","finance", "accounting", "strategic planning", "consulting",

                    ]
                }
                
                # Populate database with hardcoded skills
                for category, skills in skills_dict.items():
                    for skill_name in skills:
                        Skill.objects.get_or_create(name=skill_name, category=category)
        
        return skills_dict
    
    def _create_skill_pattern(self):
        """Create a regex pattern for skill matching from all skills"""
        all_skills = []
        for skills in self.skills_by_category.values():
            all_skills.extend(skills)
        
        # Compile a pattern that matches whole words only
        pattern = r'(?:\b|^)(?:' + '|'.join(all_skills) + r')(?:\b|$)'
        return re.compile(pattern, re.IGNORECASE)
    
    def parse_cv(self, cv_id):
        """Parse a CV and extract information"""
        try:
            # Get CV object from database
            cv_obj = CV.objects.get(id=cv_id)
            cv_obj.status = 'processing'
            cv_obj.save()
            
            # Get file path
            file_path = cv_obj.file.path
            
            # Extract text based on file type
            ext = cv_obj.get_file_extension()
            
            if ext == '.pdf':
                text = self._extract_from_pdf(file_path)
            elif ext == '.docx':
                text = self._extract_from_docx(file_path)
            elif ext == '.txt':
                text = self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {ext}")
            
            # Process and extract information
            parsed_data = self._process_text(text)
            
            # Save parsed data to the CV object
            cv_obj.parsed_data = parsed_data
            cv_obj.extracted_skills = parsed_data["skills"]

            cv_obj.status = 'completed'
            cv_obj.save()
            
            # Save extracted information to related models
            self._save_extracted_info(cv_obj, parsed_data)
            
            return True
            
        except Exception as e:
            if cv_obj:
                cv_obj.status = 'failed'
                cv_obj.save()
            print(f"Error parsing CV: {str(e)}")
            return False
    
    def _extract_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text
    
    def _extract_from_docx(self, file_path):
        """Extract text from DOCX file"""
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    
    def _extract_from_txt(self, file_path):
        """Extract text from TXT file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
        return text
    
    def _process_text(self, text):
        """Process extracted text and extract structured information"""
        # Clean text
        text = self._clean_text(text)
        
        # Process with spaCy
        doc = self.nlp(text)
        
        # Extract different components
        skills = self._extract_skills(text)
        education = self._extract_education(doc, text)
        work_experience = self._extract_work_experience(doc, text)
        contact_info = self._extract_contact_info(text)
        
        # Create structured data
        parsed_data = {
            "skills": skills,
            "education": education,
            "work_experience": work_experience,
            "contact_info": contact_info,
            "raw_text": text,
            "parsed_date": datetime.now().isoformat(),
        }
        
        return parsed_data
    
    def _clean_text(self, text):
        """Clean and normalize text"""
        # Replace multiple spaces and newlines with single space
        text = re.sub(r'\s+', ' ', text)
        # Trim whitespace
        text = text.strip()
        return text
    
    def _extract_skills(self, text):
        """Extract skills from text"""
        skills = []
        matches = self.all_skills.finditer(text)
        for match in matches:
            skill = match.group(0).strip()
            if skill and skill not in skills:
                skills.append(skill)
        return skills
    
    def _extract_education(self, doc, text):
        """Extract education information"""
        education = []
        
        # Look for education sections using keywords
        education_keywords = ["education", "academic background", "qualifications", "degree"]
        sentences = list(doc.sents)
        
        education_section = False
        edu_info = {"institution": "", "degree": "", "years": ""}
        
        for sentence in sentences:
            sent_text = sentence.text.lower()
            
            # Check if we're in an education section
            if any(keyword in sent_text for keyword in education_keywords):
                education_section = True
                continue
            
            # If we've found what appears to be a new section, save the current education info
            if education_section and re.match(r'^[A-Z]', sentence.text) and len(sentence.text) < 50:
                if edu_info["institution"] or edu_info["degree"]:
                    education.append(edu_info.copy())
                    edu_info = {"institution": "", "degree": "", "years": ""}
            
            # Extract education details if we're in an education section
            if education_section:
                # Look for academic institutions (universities, colleges)
                for ent in sentence.ents:
                    if ent.label_ == "ORG" and not edu_info["institution"]:
                        edu_info["institution"] = ent.text
                
                # Look for degree information
                degree_patterns = ["Bachelor", "Master", "PhD", "BSc", "MSc", "BA", "MA", "B.A.", "M.A.", "M.S.", "B.S."]
                for pattern in degree_patterns:
                    if pattern in sentence.text and not edu_info["degree"]:
                        # Extract the full degree phrase
                        degree_match = re.search(r'\b' + pattern + r'[^,;.]*', sentence.text)
                        if degree_match:
                            edu_info["degree"] = degree_match.group(0).strip()
                
                # Look for years
                year_pattern = r'(19|20)\d{2}\s*(-|–|to)\s*(19|20)\d{2}|^(19|20)\d{2}$'
                years_match = re.search(year_pattern, sentence.text)
                if years_match and not edu_info["years"]:
                    edu_info["years"] = years_match.group(0)
        
        # Add any final education info
        if edu_info["institution"] or edu_info["degree"]:
            education.append(edu_info)
        
        return education
    
    def _extract_work_experience(self, doc, text):
        """Extract work experience information"""
        work_experiences = []
        
        # Look for work experience sections using keywords
        work_keywords = ["experience", "employment", "work history", "professional background"]
        sentences = list(doc.sents)
        
        work_section = False
        current_experience = {"company": "", "title": "", "duration": "", "description": ""}
        
        for sentence in sentences:
            sent_text = sentence.text.lower()
            
            # Check if we're in a work experience section
            if any(keyword in sent_text for keyword in work_keywords):
                work_section = True
                continue
            
            # If we've found what appears to be a new section, save the current work info
            if work_section and re.match(r'^[A-Z]', sentence.text) and len(sentence.text) < 50:
                if current_experience["company"] or current_experience["title"]:
                    work_experiences.append(current_experience.copy())
                    current_experience = {"company": "", "title": "", "duration": "", "description": ""}
            
            # Extract work details if we're in a work section
            if work_section:
                # Look for organizations
                for ent in sentence.ents:
                    if ent.label_ == "ORG" and not current_experience["company"]:
                        current_experience["company"] = ent.text
                
                # Look for job titles
                job_titles = ["Engineer", "Developer", "Manager", "Director", "Analyst", "Consultant", "Designer"]
                for title in job_titles:
                    if title in sentence.text and not current_experience["title"]:
                        # Extract the full job title
                        title_match = re.search(r'[A-Za-z]+\s+' + title + r'|' + title + r'\s+[A-Za-z]+', sentence.text)
                        if title_match:
                            current_experience["title"] = title_match.group(0).strip()
                
                # Look for duration
                duration_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*(-|–|to)\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|^\d{4}\s*(-|–|to)\s*\d{4}$'
                duration_match = re.search(duration_pattern, sentence.text)
                if duration_match and not current_experience["duration"]:
                    current_experience["duration"] = duration_match.group(0)
                
                # Add to description
                if current_experience["company"] or current_experience["title"]:
                    current_experience["description"] += sentence.text + " "
        
        # Add any final work experience
        if current_experience["company"] or current_experience["title"]:
            work_experiences.append(current_experience)
        
        return work_experiences
    
    def _extract_contact_info(self, text):
        """Extract contact information like email and phone"""
        contact_info = {"email": "", "phone": ""}
        
        # Find all matches
        matches = self.contact_pattern.finditer(text)
        for match in matches:
            contact = match.group("contact")
            if "@" in contact:
                contact_info["email"] = contact
            else:
                contact_info["phone"] = contact
        
        return contact_info
    
    def _save_extracted_info(self, cv_obj, parsed_data):
        """Save extracted information to related models"""
        # Save skills
        for skill_name in parsed_data.get('skills', []):
            try:
                skill, _ = Skill.objects.get_or_create(
                    name=skill_name,
                    defaults={'category': 'uncategorized'}
                )
                cv_obj.extracted_skills.add(skill)
            except Exception as e:
                print(f"Error saving skill {skill_name}: {str(e)}")
        
        # Save education
        for edu in parsed_data.get('education', []):
            if edu.get('institution'):
                CVEducation.objects.create(
                    cv=cv_obj,
                    institution=edu.get('institution', ''),
                    degree=edu.get('degree', ''),
                    years=edu.get('years', '')
                )
        
        # Save work experience
        for exp in parsed_data.get('work_experience', []):
            if exp.get('company') or exp.get('title'):
                CVWorkExperience.objects.create(
                    cv=cv_obj,
                    company=exp.get('company', ''),
                    title=exp.get('title', ''),
                    duration=exp.get('duration', ''),
                    description=exp.get('description', '')
                )
        
        # Save contact info
        contact = parsed_data.get('contact_info', {})
        if contact.get('email') or contact.get('phone'):
            CVContactInfo.objects.create(
                cv=cv_obj,
                email=contact.get('email', ''),
                phone=contact.get('phone', '')
            )