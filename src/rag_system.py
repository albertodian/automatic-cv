"""
RAG (Retrieval-Augmented Generation) System for CV Optimization

This module implements a complete RAG system using:
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- Semantic search for relevant experience/project retrieval
- Query expansion for better matching
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Disable tokenizers parallelism warning (before importing sentence_transformers)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RetrievalResult:
    """Container for retrieved content with metadata."""
    content: Dict[str, Any]
    score: float
    source_type: str  # 'experience', 'project', 'skill'
    relevance_reason: str


class CVRAGSystem:
    """
    RAG system for intelligent CV content retrieval and optimization.
    
    Features:
    - Semantic search across experiences, projects, and skills
    - Query expansion for better coverage
    - Relevance scoring with multiple factors
    - Persistent vector storage
    - Hybrid search (semantic + keyword)
    """

    # models_to_test = [
    # "all-MiniLM-L6-v2",  # Current (baseline)
    # "all-mpnet-base-v2",  # Better
    # "multi-qa-mpnet-base-dot-v1",  # QA-optimized
    # "BAAI/bge-small-en-v1.5"  # SOTA small
    # ]
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "cv_content"
    ):
        """
        Initialize the RAG system.
        
        Args:
            model_name: Sentence transformer model for embeddings
            persist_directory: Path to persist ChromaDB
            collection_name: Name of the collection
        """
        print(f"Initializing RAG system with model: {model_name}")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize ChromaDB
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"Created new collection: {collection_name}")
    
    def index_profile(self, profile: Dict[str, Any]) -> None:
        """
        Index all profile content into the vector database.
        
        Args:
            profile: Complete profile dictionary
        """
        print("\nIndexing profile content...")
        
        # Clear existing data to avoid ID conflicts (fresh indexing every time)
        try:
            existing_ids = self.collection.get()['ids']
            if existing_ids:
                self.collection.delete(ids=existing_ids)
                print(f"Cleared {len(existing_ids)} old entries")
        except:
            pass  # Collection is empty or doesn't exist
        
        documents = []
        metadatas = []
        ids = []
        
        # Index experiences
        for i, exp in enumerate(profile.get('experience', [])):
            doc_text = self._format_experience(exp)
            documents.append(doc_text)
            metadatas.append({
                'type': 'experience',
                'index': i,
                'title': exp.get('title', ''),
                'company': exp.get('company', ''),
                'period': exp.get('period', ''),
                'skills': ', '.join(exp.get('skills', []))[:100],
                'original_json': json.dumps(exp)
            })
            ids.append(f"exp_{i}")
        
        # Index projects
        for i, proj in enumerate(profile.get('projects', [])):
            doc_text = self._format_project(proj)
            documents.append(doc_text)
            metadatas.append({
                'type': 'project',
                'index': i,
                'name': proj.get('name', ''),
                'role': proj.get('role', ''),
                'description': proj.get('description', '')[:100],
                'skills': ', '.join(proj.get('skills', []))[:100],
                'original_json': json.dumps(proj)
            })
            ids.append(f"proj_{i}")
        
        # Index skill groups
        skills = profile.get('skills', [])
        if skills:
            skills_text = " ".join(skills)
            documents.append(skills_text)
            metadatas.append({
                'type': 'skills',
                'count': len(skills),
                'original_json': json.dumps(skills)
            })
            ids.append("skills_all")
        
        # Index education
        for i, edu in enumerate(profile.get('education', [])):
            doc_text = self._format_education(edu)
            documents.append(doc_text)
            metadatas.append({
                'type': 'education',
                'index': i,
                'degree': edu.get('degree', ''),
                'institution': edu.get('institution', ''),
                'original_json': json.dumps(edu)
            })
            ids.append(f"edu_{i}")
        
        # Add to collection
        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Indexed {len(documents)} items")
            print(f"  - {len([m for m in metadatas if m['type']=='experience'])} experiences")
            print(f"  - {len([m for m in metadatas if m['type']=='project'])} projects")
            print(f"  - {len([m for m in metadatas if m['type']=='education'])} education entries")
    
    def retrieve_relevant_experiences(
        self,
        job_info: Dict[str, Any],
        top_k: int = 3,
        min_score: float = 0.15
    ) -> List[RetrievalResult]:
        """
        Retrieve the most relevant experiences for a job.
        
        Args:
            job_info: Parsed job information
            top_k: Number of experiences to retrieve
            min_score: Minimum relevance score threshold
            
        Returns:
            List of RetrievalResult objects
        """
        # Build query from job info
        query = self._build_job_query(job_info)
        
        # Retrieve from vector DB
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 2,  # Get more for filtering
            where={"type": "experience"}
        )
        
        # Parse and score results
        retrieved = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            score = 1 - distance  # Convert distance to similarity
            
            if score >= min_score:
                original = json.loads(metadata['original_json'])
                
                # Additional scoring factors
                recency_bonus = self._calculate_recency_score(original.get('years', original.get('period', '')))
                keyword_bonus = self._calculate_keyword_overlap(
                    original, 
                    job_info.get('keywords', [])
                )
                title_bonus = self._calculate_title_match_bonus(
                    original,
                    job_info.get('title', '')
                )
                
                # Adjusted weights: keywords more important, semantic less dominant
                final_score = (score * 0.4) + (keyword_bonus * 0.4) + (recency_bonus * 0.2) + title_bonus
                
                retrieved.append(RetrievalResult(
                    content=original,
                    score=final_score,
                    source_type='experience',
                    relevance_reason=f"Semantic: {score:.2f}, Keywords: {keyword_bonus:.2f}, Recency: {recency_bonus:.2f}, Title: {title_bonus:.2f}"
                ))
        
        # Sort by final score and return top_k
        retrieved.sort(key=lambda x: x.score, reverse=True)
        return retrieved[:top_k]
    
    def retrieve_relevant_projects(
        self,
        job_info: Dict[str, Any],
        top_k: int = 4,
        min_score: float = 0.15
    ) -> List[RetrievalResult]:
        """
        Retrieve the most relevant projects for a job.
        
        Args:
            job_info: Parsed job information
            top_k: Number of projects to retrieve
            min_score: Minimum relevance score threshold
            
        Returns:
            List of RetrievalResult objects
        """
        query = self._build_job_query(job_info, focus='technical')
        
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 2,
            where={"type": "project"}
        )
        
        retrieved = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            score = 1 - distance
            
            if score >= min_score:
                original = json.loads(metadata['original_json'])
                
                # Get recency bonus (works with both 'year' for projects and 'period'/'years' for experiences)
                recency_bonus = self._calculate_recency_score(
                    original.get('year', original.get('years', original.get('period', '')))
                )
                
                # Tech stack overlap bonus  
                tech_bonus = self._calculate_tech_overlap(
                    original.get('skills', []),
                    job_info.get('keywords', [])
                )

                # Balanced weights for projects: tech most important, semantic and recency as modifiers
                final_score = (score * 0.25) + (tech_bonus * 0.65) + (recency_bonus * 0.1)
                
                retrieved.append(RetrievalResult(
                    content=original,
                    score=final_score,
                    source_type='project',
                    relevance_reason=f"Semantic: {score:.2f}, Tech: {tech_bonus:.2f}, Recency: {recency_bonus:.2f}"
                ))
        
        retrieved.sort(key=lambda x: x.score, reverse=True)
        return retrieved[:top_k]
    
    def retrieve_relevant_skills(
        self,
        job_info: Dict[str, Any],
        profile_skills: List[str],
        top_k: int = 25
    ) -> Tuple[List[str], List[str]]:
        """
        Retrieve and prioritize skills based on job requirements using synonym-aware matching.
        
        Args:
            job_info: Parsed job information
            profile_skills: Original list of profile skills
            top_k: Maximum number of skills to return
            
        Returns:
            Tuple of (prioritized_skills, new_keywords_to_add)
        """
        job_keywords = [k.lower() for k in job_info.get('keywords', [])]
        profile_skills_lower = {s.lower(): s for s in profile_skills}
        
        # Score each skill by relevance to job keywords
        skill_scores = {}
        
        for skill_lower, skill_original in profile_skills_lower.items():
            score = 0.0
            
            # Check direct match with synonyms
            skill_variants = self._normalize_keyword(skill_lower)
            
            for job_keyword in job_keywords:
                job_variants = self._normalize_keyword(job_keyword)
                
                # Check if any variants overlap
                if skill_variants & job_variants:
                    score += 2.0  # Direct match (via synonyms)
                elif any(sv in job_keyword or job_keyword in sv for sv in skill_variants):
                    score += 1.0  # Partial match
            
            skill_scores[skill_original] = score
        
        # Sort skills by relevance score
        sorted_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Separate into matched (score > 0) and unmatched (score = 0)
        matched_skills = [skill for skill, score in sorted_skills if score > 0]
        unmatched_skills = [skill for skill, score in sorted_skills if score == 0]
        
        # Prioritize: matched skills first, then unmatched
        prioritized = (matched_skills + unmatched_skills)[:top_k]
        
        # Find new keywords to potentially add (not in profile but in job)
        # Only suggest if they're truly new (no synonym match)
        new_keywords = []
        for keyword in job_keywords[:15]:  # Check more keywords
            has_match = False
            keyword_variants = self._normalize_keyword(keyword)
            
            for skill in profile_skills:
                skill_variants = self._normalize_keyword(skill.lower())
                if keyword_variants & skill_variants:
                    has_match = True
                    break
            
            if not has_match and len(new_keywords) < 5:
                new_keywords.append(keyword.title())  # Capitalize properly
        
        return prioritized, new_keywords
    
    def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Perform hybrid search (semantic + keyword) across all content.
        
        Args:
            query: Search query
            filters: Optional metadata filters
            top_k: Number of results to return
            
        Returns:
            List of RetrievalResult objects
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=filters
        )
        
        retrieved = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            score = 1 - distance
            original = json.loads(metadata['original_json'])
            
            retrieved.append(RetrievalResult(
                content=original,
                score=score,
                source_type=metadata['type'],
                relevance_reason=f"Hybrid search score: {score:.2f}"
            ))
        
        return retrieved
    
    def reset_database(self) -> None:
        """Reset the vector database (useful for reindexing)."""
        print("🗑️  Resetting vector database...")
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )
        print("Database reset complete")
    
    # Helper methods
    
    def _format_experience(self, exp: Dict) -> str:
        """Format experience for embedding."""
        parts = [
            exp.get('title', ''),
            exp.get('company', ''),
            exp.get('description', ''),
            ' '.join(exp.get('descrition_list', [])),  # Note: typo in original
            ' '.join(exp.get('skills', []))
        ]
        return ' '.join([p for p in parts if p])
    
    def _format_project(self, proj: Dict) -> str:
        """Format project for embedding."""
        parts = [
            proj.get('name', ''),
            proj.get('role', ''),
            proj.get('description', ''),
            ' '.join(proj.get('skills', []))
        ]
        return ' '.join([p for p in parts if p])
    
    def _format_education(self, edu: Dict) -> str:
        """Format education for embedding."""
        parts = [
            edu.get('degree', ''),
            edu.get('field', ''),
            edu.get('institution', ''),
            edu.get('description', '')
        ]
        return ' '.join([p for p in parts if p])
    
    def _build_job_query(
        self, 
        job_info: Dict, 
        focus: str = 'general'
    ) -> str:
        """
        Build a query string from job information.
        
        Args:
            job_info: Job information dict
            focus: 'general' or 'technical' focus
        """
        parts = [job_info.get('title', '')]
        
        if focus == 'technical':
            parts.extend(job_info.get('keywords', [])[:15])
        else:
            parts.append(job_info.get('summary', ''))
            parts.extend(job_info.get('requirements', [])[:5])
            parts.extend(job_info.get('responsibilities', [])[:5])
        
        return ' '.join([str(p) for p in parts if p])
    
    def _calculate_title_match_bonus(self, experience: Dict, job_title: str) -> float:
        """Calculate bonus for matching job title keywords - GENERIC for all tech roles."""
        exp_title = experience.get('title', '').lower()
        job_title_lower = job_title.lower()
        
        # Generic role keywords (covers all tech disciplines)
        role_keywords = [
            # Levels
            'senior', 'junior', 'lead', 'principal', 'staff', 'intern',
            # Roles
            'engineer', 'developer', 'programmer', 'architect', 'designer',
            'scientist', 'analyst', 'researcher', 'consultant', 'specialist',
            # Domains
            'software', 'hardware', 'systems', 'platform', 'infrastructure',
            'frontend', 'backend', 'fullstack', 'full-stack', 'full stack',
            'mobile', 'web', 'cloud', 'devops', 'data', 'database',
            'ai', 'ml', 'machine learning', 'robotics', 'embedded', 'iot',
            'security', 'network', 'qa', 'test', 'quality'
        ]
        
        matches = 0
        for keyword in role_keywords:
            if keyword in exp_title and keyword in job_title_lower:
                matches += 1
        
        # Strong bonus for exact role match (Engineer to Engineer, Developer to Developer)
        if 'engineer' in exp_title and 'engineer' in job_title_lower:
            matches += 2
        elif 'developer' in exp_title and 'developer' in job_title_lower:
            matches += 2
        
        # Each match adds 6%, max 30% bonus
        return min(matches * 0.06, 0.3)
    
    def _calculate_recency_score(self, period_or_year: str) -> float:
        """
        Calculate recency bonus (0.0 to 1.0).
        
        Handles both:
        - Experience periods: "2023-2024", "Jan 2023 - Dec 2024"
        - Project years: "2024", "2023"
        
        Args:
            period_or_year: Period string (experience) or year string (project)
            
        Returns:
            Recency score from 0.0 (old) to 1.0 (current/recent)
        """
        if not period_or_year:
            return 0.0
        
        # Extract years (e.g., "2023-2024", "Jan 2023 - Dec 2024", or just "2024")
        import re
        years = re.findall(r'\d{4}', str(period_or_year))
        
        if not years:
            return 0.0
        
        # Use the most recent year found
        latest_year = max([int(y) for y in years])
        current_year = datetime.now().year
        
        years_ago = current_year - latest_year
        
        # Scoring based on how recent the work is
        if years_ago <= 0:  # Current or future
            return 1.0
        elif years_ago == 1:  # Last year
            return 0.8
        elif years_ago == 2:  # 2 years ago
            return 0.5
        elif years_ago == 3:  # 3 years ago
            return 0.3
        else:  # 4+ years ago
            return 0.1
    
    def _normalize_keyword(self, keyword: str) -> set:
        """Normalize keyword to catch variations and synonyms - GENERIC for all tech roles."""
        kw_lower = keyword.lower().strip()
        
        # Generic tech synonym mapping (AI, ML, Web, Mobile, Systems, etc.)
        synonyms = {
            # AI/ML
            'ai': {'ai', 'artificial intelligence', 'intelligent'},
            'ml': {'ml', 'machine learning', 'model', 'training'},
            'llm': {'llm', 'large language model', 'gpt', 'chatbot'},
            'cv': {'computer vision', 'vision', 'image processing'},
            'dl': {'deep learning', 'neural network', 'cnn', 'rnn'},
            
            # Programming Languages
            'python': {'python', 'py', 'pythonic'},
            'javascript': {'javascript', 'js', 'typescript', 'ts', 'node'},
            'java': {'java', 'jvm', 'spring'},
            'c++': {'c++', 'cpp', 'c'},
            'c#': {'c#', 'csharp', '.net'},
            
            # Frameworks/Libraries
            'react': {'react', 'reactjs', 'react.js', 'jsx'},
            'angular': {'angular', 'angularjs'},
            'vue': {'vue', 'vuejs', 'vue.js'},
            'django': {'django', 'flask', 'fastapi'},
            'tensorflow': {'tensorflow', 'tf', 'keras'},
            'pytorch': {'pytorch', 'torch'},
            
            # Mobile
            'mobile': {'mobile', 'ios', 'android', 'flutter', 'react native', 'app'},
            'flutter': {'flutter', 'dart'},
            
            # DevOps/Cloud
            'cloud': {'cloud', 'aws', 'azure', 'gcp', 'serverless'},
            'docker': {'docker', 'container', 'kubernetes', 'k8s'},
            'ci/cd': {'ci/cd', 'pipeline', 'deployment', 'jenkins', 'github actions'},
            
            # Databases
            'database': {'database', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql'},
            
            # General Software Engineering
            'software': {'software', 'engineering', 'development', 'developer', 'engineer'},
            'backend': {'backend', 'back-end', 'server', 'api', 'rest', 'graphql'},
            'frontend': {'frontend', 'front-end', 'ui', 'ux', 'web'},
            'fullstack': {'fullstack', 'full-stack', 'full stack'},
            'api': {'api', 'rest', 'restful', 'graphql', 'endpoint'},
            
            # Robotics/Embedded
            'robotics': {'robotics', 'robot', 'ros', 'autonomous'},
            'embedded': {'embedded', 'firmware', 'iot', 'microcontroller'},
            
            # Data
            'data': {'data', 'dataset', 'analytics', 'etl', 'pipeline'},
            'big data': {'big data', 'spark', 'hadoop', 'streaming'},
            
            # General Skills
            'testing': {'testing', 'test', 'qa', 'unit test', 'integration'},
            'git': {'git', 'github', 'gitlab', 'version control'},
            'agile': {'agile', 'scrum', 'sprint', 'jira'},
            'teamwork': {'teamwork', 'team', 'collaboration', 'collaborative'},
            'leadership': {'leadership', 'lead', 'mentor', 'mentoring'},
        }
        
        # Check if keyword matches any synonym group
        for key, syn_set in synonyms.items():
            if kw_lower in syn_set:
                return syn_set
        
        # Partial matching for compound keywords
        for key, syn_set in synonyms.items():
            if any(syn in kw_lower or kw_lower in syn for syn in syn_set):
                return syn_set
        
        # Return original if no synonyms found
        return {kw_lower}
    
    def _calculate_keyword_overlap(
        self, 
        content: Dict, 
        keywords: List[str]
    ) -> float:
        """Calculate keyword overlap score with synonym support (0.0 to 1.0)."""
        if not keywords:
            return 0.0
        
        # Get all text from content
        text = json.dumps(content).lower()
        
        matches = 0
        for keyword in keywords:
            # Get all synonym variations
            variants = self._normalize_keyword(keyword)
            
            # Match if ANY variant found in text
            if any(variant in text for variant in variants):
                matches += 1
        
        return min(matches / len(keywords), 1.0)
    
    def _calculate_tech_overlap(
        self, 
        project_skills: List[str], 
        job_keywords: List[str]
    ) -> float:
        """Calculate technical skill overlap with synonym support (0.0 to 1.0)."""
        if not project_skills or not job_keywords:
            return 0.0
        
        # Use synonym matching like keyword overlap
        matches = 0
        for job_keyword in job_keywords:
            # Get synonym variations of job keyword
            job_variants = self._normalize_keyword(job_keyword)
            
            # Check if any project skill matches any variant
            for skill in project_skills:
                skill_variants = self._normalize_keyword(skill)
                
                # Check for overlap between variant sets
                if job_variants & skill_variants:  # Set intersection
                    matches += 1
                    break  # Count each job keyword only once
        
        # Return match ratio
        return min(matches / len(job_keywords), 1.0)


class RAGEnhancedGenerator:
    """
    Wrapper that combines RAG retrieval with LLM generation.
    """
    
    def __init__(self, rag_system: CVRAGSystem):
        self.rag = rag_system
    
    def generate_optimized_profile_with_rag(
        self,
        profile: Dict[str, Any],
        job_info: Dict[str, Any],
        llm_function: callable,
        model_name: str,
        use_rag_prompt: bool = True
    ) -> Dict[str, Any]:
        """
        Generate optimized profile using RAG-retrieved content.
        
        Args:
            profile: Original profile
            job_info: Parsed job information
            llm_function: LLM generation function to call
            model_name: Model name to use
            use_rag_prompt: Whether to use RAG-specific prompt
            
        Returns:
            Optimized profile dict
        """
        print("\nRAG-Enhanced Profile Generation")
        
        # Retrieve relevant content
        print("\n1. Retrieving relevant experiences...")
        relevant_exp = self.rag.retrieve_relevant_experiences(job_info, top_k=3)
        for i, result in enumerate(relevant_exp, 1):
            print(f"   [{i}] {result.content.get('title')} @ {result.content.get('company')}")
            print(f"       Score: {result.score:.3f} - {result.relevance_reason}")
        
        print("\n2. Retrieving relevant projects...")
        relevant_proj = self.rag.retrieve_relevant_projects(job_info, top_k=4)
        for i, result in enumerate(relevant_proj, 1):
            print(f"   [{i}] {result.content.get('name')}")
            print(f"       Score: {result.score:.3f} - {result.relevance_reason}")
        
        print("\n3. Prioritizing skills based on job relevance...")
        prioritized_skills, new_keywords = self.rag.retrieve_relevant_skills(
            job_info, 
            profile.get('skills', [])
        )
        
        # Show skills that match job keywords (BALANCED: technical synonyms OK, generic ones NO)
        job_keywords_lower = [k.lower() for k in job_info.get('keywords', [])]
        
        # Build match list with balanced synonym matching
        relevant_top_10 = []
        
        # Blacklist: Generic skills that should NEVER be matched loosely
        generic_blacklist = {
            'adobe', 'photoshop', 'illustrator', 'creative suite',
            '3d modeling', 'blender', 'maya', '3d',
            'video editing', 'premiere', 'after effects',
            'graphic design', 'design', 'ui design',
            'unity', 'unreal', 'game engine', 'gaming',
            'wordpress', 'wix', 'squarespace'
        }
        
        for skill in prioritized_skills[:25]:  # Check more skills
            skill_lower = skill.lower()
            
            # Skip if skill is in generic blacklist (unless explicitly in job keywords)
            is_blacklisted = any(bl in skill_lower for bl in generic_blacklist)
            if is_blacklisted:
                # Only include if EXACTLY in job keywords
                if skill_lower not in job_keywords_lower:
                    continue
            
            # Check for match using synonym-aware matching for technical terms
            is_relevant = False
            skill_variants = self.rag._normalize_keyword(skill_lower)
            
            for job_kw in job_keywords_lower:
                job_variants = self.rag._normalize_keyword(job_kw)
                
                # Match if variants overlap
                if skill_variants & job_variants:
                    is_relevant = True
                    break
            
            if is_relevant:
                relevant_top_10.append(skill)
            
            if len(relevant_top_10) >= 10:
                break
        
        print(f"   Job-matched skills ({len(relevant_top_10)}): {', '.join(relevant_top_10)}")
        if new_keywords:
            print(f"   Consider adding: {', '.join(new_keywords[:5])}")
        
        # Build RAG-enhanced profile for LLM
        rag_profile = profile.copy()
        rag_profile['experience'] = [r.content for r in relevant_exp]
        rag_profile['projects'] = [r.content for r in relevant_proj]
        rag_profile['skills'] = prioritized_skills
        
        # Add metadata to guide LLM
        rag_profile['_rag_metadata'] = {
            'experience_scores': [r.score for r in relevant_exp],
            'project_scores': [r.score for r in relevant_proj],
            'suggested_keywords': new_keywords[:8],
            'retrieval_method': 'semantic_search_with_scoring'
        }
        
        print("\n4. Generating optimized CV with LLM...")
        print(f"   Input to LLM: {len(rag_profile['experience'])} experiences, {len(rag_profile['projects'])} projects")
        
        optimized = llm_function(rag_profile, job_info, model_name)
        
        # Remove metadata from final output
        if '_rag_metadata' in optimized:
            del optimized['_rag_metadata']
        
        print("RAG-enhanced generation complete\n")
        return optimized
