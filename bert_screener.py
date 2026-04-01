"""
BERT-Based Resume Screener - Simplified Implementation
Using Sentence-BERT for semantic similarity matching
"""
import numpy as np
import re
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer, util


class BERTResumeScreener:
    """
    Simple and effective resume screening using Sentence-BERT.
    Much better than TF-IDF with minimal complexity.
    """
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the BERT model.
        'all-MiniLM-L6-v2' is fast and accurate - perfect for production.
        """
        print("Loading BERT model... (this happens once at startup)")
        self.model = SentenceTransformer(model_name)
        self.util = util
        print("✓ Model loaded successfully!")
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\-]', ' ', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def calculate_similarity(self, job_description: str, resume_text: str) -> float:
        """
        Calculate semantic similarity between job description and resume.
        Returns a score between 0 and 1 (higher is better match).
        """
        # Preprocess texts
        job_clean = self.preprocess_text(job_description)
        resume_clean = self.preprocess_text(resume_text)
        
        # Generate embeddings (convert text to vectors)
        job_embedding = self.model.encode(job_clean, convert_to_tensor=True)
        resume_embedding = self.model.encode(resume_clean, convert_to_tensor=True)
        
        # Calculate cosine similarity
        similarity = self.util.cos_sim(job_embedding, resume_embedding)
        
        return float(similarity[0][0])
    
    def rank_resumes(self, job_description: str, resumes: Dict[str, str], 
                     top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Rank all resumes based on similarity to job description.
        
        Args:
            job_description: The job posting text
            resumes: Dictionary mapping resume_name -> resume_text
            top_k: Number of top candidates to return (default: 3)
        
        Returns:
            List of tuples: (resume_name, similarity_score)
            Sorted by similarity score in descending order
        """
        results = []
        
        print(f"\nAnalyzing {len(resumes)} resumes using BERT...")
        
        for resume_name, resume_text in resumes.items():
            # Calculate similarity score
            score = self.calculate_similarity(job_description, resume_text)
            results.append((resume_name, score))
            print(f"  ✓ {resume_name}: {score:.4f}")
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\nTop {top_k} matches found!")
        return results[:top_k]


# Test the screener (run this to verify it works)
if __name__ == "__main__":
    print("="*60)
    print("Testing BERT Resume Screener")
    print("="*60)
    
    # Initialize screener
    screener = BERTResumeScreener()
    
    # Sample job description
    job_description = """
    Senior Python Developer
    
    We are looking for an experienced Python developer with 5+ years of experience.
    
    Required Skills:
    - Python programming
    - Django or Flask
    - SQL databases
    - RESTful APIs
    - Docker
    
    Nice to have:
    - AWS experience
    - React or Vue.js
    """
    
    # Sample resumes
    resumes = {
        "john_doe.pdf": """
        John Doe
        Senior Software Engineer
        
        7 years of experience in Python development.
        Expert in Django, Flask, PostgreSQL, and REST APIs.
        Deployed applications using Docker and AWS.
        Built microservices architecture.
        """,
        
        "jane_smith.pdf": """
        Jane Smith
        Full Stack Developer
        
        3 years of experience.
        Skills: JavaScript, React, Node.js, MongoDB
        Built several web applications.
        Some Python experience.
        """,
        
        "bob_johnson.pdf": """
        Bob Johnson
        Python Developer
        
        5 years of Python experience.
        Django expert, MySQL, PostgreSQL.
        REST API development.
        Docker and Kubernetes.
        Familiar with AWS services.
        """
    }
    
    # Rank resumes
    results = screener.rank_resumes(job_description, resumes, top_k=3)
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    for rank, (name, score) in enumerate(results, 1):
        print(f"\nRank {rank}: {name}")
        print(f"Match Score: {score*100:.2f}%")
        
        # Interpretation
        if score >= 0.7:
            print("Assessment: ✅ Excellent match")
        elif score >= 0.5:
            print("Assessment: ⚠️  Good match")
        else:
            print("Assessment: ❌ Weak match")
