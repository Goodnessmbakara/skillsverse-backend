import spacy
from spacy.tokens import Span
from typing import List, Dict, Any

class CustomNERExtractor:
    """Custom Named Entity Recognition for CV and Job Parsing"""
    
    def __init__(self, model_path: str = 'en_core_web_lg'):
        """
        Initialize the custom NER extractor
        
        Args:
            model_path (str): Path to spaCy language model
        """
        self.nlp = spacy.load(model_path)
        self._add_custom_entity_rules()
    
    def _add_custom_entity_rules(self):
        """Add custom entity recognition rules"""
        # Add custom pipeline components
        
        @self.nlp.component('skill_ruler')
        def skill_ruler(doc):
            """Custom skill entity ruler"""
            matches = []
            
            # Custom skill patterns
            skill_patterns = [
                "machine learning", "data science", "artificial intelligence", 
                "cloud computing", "software engineering", "cybersecurity",
                "blockchain", "big data", "natural language processing",
                "full stack development", "devops", "data analytics"
            ]
            
            for pattern in skill_patterns:
                start_index = doc.text.lower().find(pattern)
                if start_index != -1:
                    start = doc.text.lower().index(pattern)
                    end = start + len(pattern)
                    span = Span(doc, start, end, label_="SKILL")
                    matches.append(span)
            
            for match in matches:
                doc.ents += (match,)
            
            return doc
        
        self.nlp.add_pipe('skill_ruler', last=True)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text
        
        Args:
            text (str): Input text to parse
        
        Returns:
            Dict[str, List[str]]: Extracted entities by type
        """
        doc = self.nlp(text)
        
        # Initialize entity dictionary
        entities = {
            "PERSON": [],
            "ORG": [],
            "GPE": [],  # Geopolitical entities
            "SKILL": [],
            "JOB_TITLE": [],
            "EDUCATION": []
        }
        
        # Extract standard named entities
        for ent in doc.ents:
            # Map standard entities
            if ent.label_ in ["PERSON", "ORG", "GPE"]:
                entities[ent.label_].append(ent.text)
        
        # Custom entity extraction
        job_title_patterns = [
            "engineer", "developer", "manager", "analyst", 
            "architect", "director", "specialist", "consultant"
        ]
        
        education_patterns = [
            "bachelor", "master", "phd", "doctorate", 
            "bs", "ms", "ma", "ba", "bsc", "msc"
        ]
        
        # Custom job title and skills extraction
        for token in doc:
            # Job Title extraction
            if any(title in token.text.lower() for title in job_title_patterns):
                entities["JOB_TITLE"].append(token.text)
            
            # Education level extraction
            if any(edu in token.text.lower() for edu in education_patterns):
                entities["EDUCATION"].append(token.text)
        
        # Add detected skills from skill ruler
        entities["SKILL"] = [ent.text for ent in doc.ents if ent.label_ == "SKILL"]
        
        return entities
    
    def extract_company_skills(self, text: str) -> Dict[str, List[str]]:
        """
        Extract company and associated skills from text
        
        Args:
            text (str): Input text to parse
        
        Returns:
            Dict[str, List[str]]: Companies and their associated skills
        """
        doc = self.nlp(text)
        
        company_skills = {}
        current_company = None
        
        for sent in doc.sents:
            # Find organizations in the sentence
            org_ents = [ent for ent in sent.ents if ent.label_ == "ORG"]
            skill_ents = [ent for ent in sent.ents if ent.label_ == "SKILL"]
            
            if org_ents:
                current_company = org_ents[0].text
                if current_company not in company_skills:
                    company_skills[current_company] = []
            
            # Add skills to current company
            if current_company and skill_ents:
                company_skills[current_company].extend([skill.text for skill in skill_ents])
        
        return company_skills