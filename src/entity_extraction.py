#!/usr/bin/env python3
"""
Entity Extraction Module - Milestone D1
Rule-based entity extraction with normalization
"""

import re
import time
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

try:
    from graph_normalization import normalize_name, entity_hash, edge_hash
except ImportError:
    from .graph_normalization import normalize_name, entity_hash, edge_hash

logger = logging.getLogger(__name__)

# Entity type constants
TYPE_PERSON = "person"
TYPE_ORG = "org"
TYPE_TECH = "tech"
TYPE_URL = "url"
TYPE_REPO = "repo"
TYPE_TOPIC = "topic"

# Patterns for entity detection
ORG_SUFFIXES = r"\b(Inc|LLC|Ltd|Labs|Systems|AI|Corp|Corporation|Research|Company|Group|Foundation|Institute|University|College|Academy|School|Bank|Partners|Ventures|Capital|Holdings|Industries|Technologies|Solutions|Services|Software|Hardware|Networks|Enterprises|Associates|Consulting|Analytics|Dynamics|Innovations|Robotics|Biotech|Pharma|Health|Medical|Finance|Financial|Insurance|Energy|Motors|Airlines|Airways|Entertainment|Media|Publishing|News|Records|Studios|Productions|Games|Gaming|Hotels|Resorts|Retail|Store|Stores|Market|Markets|Foods|Beverages|Restaurant|Restaurants|Cafe|Coffee|Pizza|Burger|Automotive|Auto|Cars|Trucks|Transport|Transportation|Logistics|Shipping|Delivery|Express|Telecom|Telecommunications|Wireless|Mobile|Internet|Digital|Data|Cloud|Security|Cyber|Defense|Defence|Aerospace|Space|Aviation|Engineering|Construction|Manufacturing|Industrial|Chemical|Materials|Mining|Oil|Gas|Power|Electric|Utilities|Water|Environmental|Green|Solar|Wind|Nuclear|Realty|Real Estate|Properties|Development|Developers|Builders|Homes|Housing|Apartments|Management|Advisory|Law|Legal|Accounting|Tax|Audit|Strategy|Marketing|Advertising|PR|Public Relations|Design|Creative|Agency|Studio|Lab|Laboratory|Center|Centre|Hub|Zone|Park|Plaza|Tower|Building|Complex|Campus|District|Global|International|National|Regional|Local|World|United|American|European|Asian|Pacific|Atlantic|Northern|Southern|Eastern|Western|Central|Metro|City|State|County|Municipal|Federal|Government|Gov|Dept|Department|Bureau|Commission|Authority|Administration|Office|Council|Committee|Board|Panel|Task Force|Alliance|Coalition|Federation|Union|Association|Society|Organization|Organisation|Community|Network|Forum|Consortium|Partnership|Cooperative|Co-op|Collective|Movement|Initiative|Project|Program|Programme|Scheme|Fund|Trust|Charity|Nonprofit|Non-profit|NGO)\b"
PERSON_TITLES = r"\b(Mr|Mrs|Ms|Miss|Dr|Doctor|Prof|Professor|Sir|Lady|Lord|Dame|Rev|Reverend|Fr|Father|Sr|Sister|Br|Brother|Rabbi|Imam|Sheikh|Gen|General|Col|Colonel|Maj|Major|Capt|Captain|Lt|Lieutenant|Sgt|Sergeant|Officer|Detective|Chief|Director|Manager|President|VP|Vice President|CEO|CFO|CTO|COO|CMO|CIO|CISO|Founder|Co-founder|Chairman|Chair|Secretary|Treasurer|Minister|Senator|Representative|Congressman|Congresswoman|Governor|Mayor|Ambassador|Judge|Justice|Attorney|Lawyer|Counselor|Advisor|Consultant|Engineer|Developer|Designer|Architect|Analyst|Scientist|Researcher|Scholar|Academic|Lecturer|Teacher|Instructor|Coach|Trainer|Specialist|Expert|Professional|Technician|Operator|Administrator|Coordinator|Assistant|Associate|Intern|Trainee|Apprentice|Student|Candidate|Applicant)\b"

# Tech terms that should be recognized as entities
TECH_TERMS = {
    "python", "javascript", "typescript", "java", "golang", "rust", "ruby", "php", "swift", "kotlin",
    "react", "vue", "angular", "svelte", "nextjs", "nuxtjs", "gatsby", "webpack", "vite", "rollup",
    "nodejs", "deno", "bun", "express", "fastapi", "django", "flask", "rails", "laravel", "spring",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "firebase",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "ansible", "jenkins", "gitlab",
    "github", "git", "svn", "mercurial", "bitbucket", "jira", "confluence", "slack", "discord",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "jupyter", "colab",
    "openai", "anthropic", "gpt", "claude", "llm", "bert", "transformer", "diffusion", "gan",
    "blockchain", "bitcoin", "ethereum", "web3", "nft", "defi", "dao", "smart contract",
    "api", "rest", "graphql", "grpc", "websocket", "oauth", "jwt", "ssl", "tls", "https",
    "html", "css", "sass", "tailwind", "bootstrap", "material-ui", "semantic-ui",
    "linux", "ubuntu", "debian", "fedora", "centos", "macos", "windows", "android", "ios",
    "vim", "emacs", "vscode", "intellij", "eclipse", "atom", "sublime", "notepad++",
    "agile", "scrum", "kanban", "devops", "ci/cd", "microservices", "serverless", "edge computing",
    "machine learning", "deep learning", "neural network", "computer vision", "nlp", "reinforcement learning",
    "quantum computing", "ar", "vr", "xr", "metaverse", "iot", "5g", "edge ai"
}

# Common topic keywords that map to topics
TOPIC_MAP = {
    "artificial intelligence": "AI",
    "machine learning": "ML", 
    "deep learning": "DL",
    "natural language processing": "NLP",
    "computer vision": "CV",
    "data science": "DataScience",
    "web development": "WebDev",
    "mobile development": "MobileDev",
    "cloud computing": "Cloud",
    "cybersecurity": "Security",
    "devops": "DevOps",
    "blockchain": "Blockchain",
    "quantum computing": "Quantum",
    "robotics": "Robotics",
    "augmented reality": "AR/VR",
    "virtual reality": "AR/VR",
    "internet of things": "IoT",
    "big data": "BigData",
    "edge computing": "EdgeComputing",
    "5g": "5G",
    "fintech": "FinTech",
    "healthtech": "HealthTech",
    "edtech": "EdTech",
    "gaming": "Gaming",
    "ecommerce": "Ecommerce",
    "social media": "SocialMedia",
    "content creation": "Content",
    "digital marketing": "Marketing",
    "startup": "Startup",
    "venture capital": "VC",
    "open source": "OpenSource"
}

class EntityExtractor:
    """Rule-based entity extractor"""
    
    def __init__(self, project_id: str = "vader-lab"):
        self.project_id = project_id
        self.org_pattern = re.compile(rf"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s*(?:{ORG_SUFFIXES})", re.IGNORECASE)
        self.person_pattern = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
        self.url_pattern = re.compile(r"https?://[^\s<>\"'\]]+")
        self.github_pattern = re.compile(r"github\.com/([A-Za-z0-9_-]+)/([A-Za-z0-9_.-]+)")
        self.hashtag_pattern = re.compile(r"#(\w+)")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        
    def extract_entities(self, text: str, doc_id: Optional[int] = None, project: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract entities from text
        
        Returns:
            Dict with entities, edges, and diagnostics
        """
        start_time = time.time()
        project = project or self.project_id
        
        entities = []
        edges = []
        diagnostics = {
            "rules_fired": [],
            "counts": defaultdict(int),
            "timings": {}
        }
        
        # Track unique entities to avoid duplicates
        seen_entities = set()
        entity_positions = defaultdict(list)  # Track positions for co-occurrence
        
        # Extract organizations
        t0 = time.time()
        for match in self.org_pattern.finditer(text):
            org_name = match.group(0).strip()
            if self._is_valid_entity(org_name):
                entity_key = self._make_entity_key(TYPE_ORG, org_name, project)
                if entity_key not in seen_entities:
                    entities.append({
                        "type": TYPE_ORG,
                        "name": org_name,
                        "normalized": self._safe_normalize(org_name, TYPE_ORG),
                        "confidence": 0.8,
                        "project": project
                    })
                    seen_entities.add(entity_key)
                    diagnostics["counts"][TYPE_ORG] += 1
                entity_positions[entity_key].append(match.span())
        diagnostics["timings"]["orgs"] = time.time() - t0
        if diagnostics["counts"][TYPE_ORG] > 0:
            diagnostics["rules_fired"].append("org_suffix")
        
        # Extract people
        t0 = time.time()
        for match in self.person_pattern.finditer(text):
            name = match.group(0)
            # Filter out common false positives
            if not self._is_likely_person(name):
                continue
            entity_key = self._make_entity_key(TYPE_PERSON, name, project)
            if entity_key not in seen_entities:
                entities.append({
                    "type": TYPE_PERSON,
                    "name": name,
                    "normalized": self._safe_normalize(name, TYPE_PERSON),
                    "confidence": 0.7,
                    "project": project
                })
                seen_entities.add(entity_key)
                diagnostics["counts"][TYPE_PERSON] += 1
            entity_positions[entity_key].append(match.span())
        diagnostics["timings"]["people"] = time.time() - t0
        if diagnostics["counts"][TYPE_PERSON] > 0:
            diagnostics["rules_fired"].append("person_pattern")
        
        # Extract URLs
        t0 = time.time()
        for match in self.url_pattern.finditer(text):
            url = match.group(0)
            entity_key = self._make_entity_key(TYPE_URL, url, project)
            if entity_key not in seen_entities:
                entities.append({
                    "type": TYPE_URL,
                    "name": url,
                    "normalized": self._safe_normalize(url, TYPE_URL),
                    "confidence": 1.0,
                    "project": project
                })
                seen_entities.add(entity_key)
                diagnostics["counts"][TYPE_URL] += 1
            entity_positions[entity_key].append(match.span())
        diagnostics["timings"]["urls"] = time.time() - t0
        if diagnostics["counts"][TYPE_URL] > 0:
            diagnostics["rules_fired"].append("url_pattern")
        
        # Extract GitHub repos
        t0 = time.time()
        for match in self.github_pattern.finditer(text):
            owner = match.group(1)
            repo = match.group(2)
            repo_name = f"github.com/{owner}/{repo}"
            entity_key = self._make_entity_key(TYPE_REPO, repo_name, project)
            if entity_key not in seen_entities:
                entities.append({
                    "type": TYPE_REPO,
                    "name": repo_name,
                    "normalized": self._safe_normalize(repo_name, TYPE_REPO),
                    "confidence": 1.0,
                    "project": project
                })
                seen_entities.add(entity_key)
                diagnostics["counts"][TYPE_REPO] += 1
            entity_positions[entity_key].append(match.span())
        diagnostics["timings"]["repos"] = time.time() - t0
        if diagnostics["counts"][TYPE_REPO] > 0:
            diagnostics["rules_fired"].append("github_pattern")
        
        # Extract tech terms
        t0 = time.time()
        text_lower = text.lower()
        for term in TECH_TERMS:
            if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
                entity_key = self._make_entity_key(TYPE_TECH, term, project)
                if entity_key not in seen_entities:
                    entities.append({
                        "type": TYPE_TECH,
                        "name": term.title() if len(term) > 3 else term.upper(),
                        "normalized": self._safe_normalize(term, TYPE_TECH),
                        "confidence": 0.9,
                        "project": project
                    })
                    seen_entities.add(entity_key)
                    diagnostics["counts"][TYPE_TECH] += 1
                # Find positions
                for m in re.finditer(r'\b' + re.escape(term) + r'\b', text_lower):
                    entity_positions[entity_key].append(m.span())
        diagnostics["timings"]["tech"] = time.time() - t0
        if diagnostics["counts"][TYPE_TECH] > 0:
            diagnostics["rules_fired"].append("tech_terms")
        
        # Extract hashtags as topics
        t0 = time.time()
        for match in self.hashtag_pattern.finditer(text):
            tag = match.group(1)
            entity_key = self._make_entity_key(TYPE_TOPIC, tag, project)
            if entity_key not in seen_entities:
                entities.append({
                    "type": TYPE_TOPIC,
                    "name": f"#{tag}",
                    "normalized": self._safe_normalize(tag, TYPE_TOPIC),
                    "confidence": 0.9,
                    "project": project
                })
                seen_entities.add(entity_key)
                diagnostics["counts"][TYPE_TOPIC] += 1
            entity_positions[entity_key].append(match.span())
        
        # Extract topics from keyword map
        for phrase, topic in TOPIC_MAP.items():
            if phrase in text_lower:
                entity_key = self._make_entity_key(TYPE_TOPIC, topic, project)
                if entity_key not in seen_entities:
                    entities.append({
                        "type": TYPE_TOPIC,
                        "name": topic,
                        "normalized": self._safe_normalize(topic, TYPE_TOPIC),
                        "confidence": 0.85,
                        "project": project
                    })
                    seen_entities.add(entity_key)
                    diagnostics["counts"][TYPE_TOPIC] += 1
        diagnostics["timings"]["topics"] = time.time() - t0
        if diagnostics["counts"][TYPE_TOPIC] > 0:
            diagnostics["rules_fired"].append("hashtags_topics")
        
        # Create edges if doc_id provided
        if doc_id:
            # Create MENTIONS edges for all entities
            for entity in entities:
                edges.append({
                    "type": "MENTIONS",
                    "src_id": doc_id,
                    "dst_entity": entity,
                    "confidence": entity["confidence"],
                    "properties": {
                        "extraction_method": "rule_based",
                        "frequency": len(entity_positions.get(
                            self._make_entity_key(entity["type"], entity["name"], project), []
                        ))
                    }
                })
            
            # Create RELATED_TO edges for co-occurring entities (same sentence heuristic)
            sentences = self._split_sentences(text)
            for sentence in sentences:
                sentence_entities = []
                for entity in entities:
                    if entity["name"].lower() in sentence.lower():
                        sentence_entities.append(entity)
                
                # Create edges between all pairs in same sentence
                for i, e1 in enumerate(sentence_entities):
                    for e2 in sentence_entities[i+1:]:
                        if e1["type"] == TYPE_ORG and e2["type"] == TYPE_ORG:
                            edges.append({
                                "type": "RELATED_TO",
                                "src_entity": e1,
                                "dst_entity": e2,
                                "confidence": 0.6,
                                "properties": {
                                    "context": "same_sentence",
                                    "sentence_hash": str(hash(sentence))[:8]
                                }
                            })
        
        diagnostics["timings"]["total"] = time.time() - start_time
        diagnostics["counts"]["total_entities"] = len(entities)
        diagnostics["counts"]["total_edges"] = len(edges)
        
        return {
            "entities": entities,
            "edges": edges,
            "diagnostics": diagnostics
        }
    
    def _safe_normalize(self, text: str, etype: str) -> str:
        """Safely normalize text, returning original if normalization fails"""
        try:
            return normalize_name(text, etype)
        except (ValueError, AttributeError):
            return text.lower().strip()
    
    def _make_entity_key(self, etype: str, name: str, project: str) -> str:
        """Create unique key for entity deduplication"""
        normalized = self._safe_normalize(name, etype)
        return f"{etype}|{normalized}|{project}"
    
    def _is_valid_entity(self, text: str) -> bool:
        """Check if text is a valid entity name"""
        if not text or len(text) < 2:
            return False
        if text.isupper() and len(text) > 10:  # Likely an acronym sentence
            return False
        return True
    
    def _is_likely_person(self, name: str) -> bool:
        """Check if name is likely a person (not a place or thing)"""
        # Common false positives
        false_positives = {
            "United States", "United Kingdom", "New York", "San Francisco", 
            "Los Angeles", "New Jersey", "North America", "South America",
            "Middle East", "Far East", "Silicon Valley", "Wall Street",
            "Main Street", "High Street", "First Avenue", "Second Avenue",
            "January February", "Monday Tuesday", "Spring Summer",
            "Big Data", "Machine Learning", "Artificial Intelligence",
            "Best Practices", "Open Source", "Real Time", "High Performance"
        }
        
        if name in false_positives:
            return False
        
        # Must have at least first and last name
        parts = name.split()
        if len(parts) < 2:
            return False
        
        # Check for title prefixes
        if any(title in name for title in ["Mr ", "Mrs ", "Ms ", "Dr ", "Prof "]):
            return True
        
        # Basic heuristic: at least 2 capitalized words, not too many
        if 2 <= len(parts) <= 4:
            return all(p[0].isupper() for p in parts if p)
        
        return False
    
    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitter"""
        # Simple regex-based sentence splitting
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]

# Singleton instance
_extractor = None

def get_entity_extractor(project_id: str = "vader-lab") -> EntityExtractor:
    """Get or create entity extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor(project_id)
    return _extractor

def extract_entities(text: str, doc_id: Optional[int] = None, project: Optional[str] = None) -> Dict[str, Any]:
    """
    Main extraction function (rule-based only)
    
    Args:
        text: Text to extract from
        doc_id: Optional document ID for creating edges
        project: Optional project ID
    
    Returns:
        Dict with entities, edges, and diagnostics
    """
    extractor = get_entity_extractor(project or "vader-lab")
    return extractor.extract_entities(text, doc_id, project)

def hybrid_extract(text: str, doc_id: Optional[int] = None, project: Optional[str] = None, 
                   min_confidence: float = 0.2) -> Dict[str, Any]:
    """
    Hybrid extraction using both rule-based and LLM methods
    
    Args:
        text: Text to extract from
        doc_id: Optional document ID for creating edges
        project: Optional project ID
        min_confidence: Minimum confidence for LLM entities
    
    Returns:
        Merged result with entities, edges, and diagnostics
    """
    import time
    start_time = time.time()
    
    # Step 1: Run rule-based extraction
    rule_result = extract_entities(text, doc_id, project)
    rule_ms = rule_result.get("diagnostics", {}).get("timings", {}).get("total", 0) * 1000
    
    # Step 2: Check if LLM is enabled and run if available
    try:
        from llm_extraction import extract_with_llm, merge_extractions, is_llm_enabled
    except ImportError:
        from .llm_extraction import extract_with_llm, merge_extractions, is_llm_enabled
    
    if is_llm_enabled():
        # Build context for LLM
        context = {
            "project": project,
            "doc_id": doc_id,
            "rule_entities_found": len(rule_result.get("entities", [])),
            "rule_edges_found": len(rule_result.get("edges", []))
        }
        
        # Run LLM extraction
        llm_result = extract_with_llm(text, context)
        llm_ms = llm_result.get("diagnostics", {}).get("latency_ms", 0)
        
        # Merge results
        merged_result = merge_extractions(rule_result, llm_result, min_confidence)
        merge_ms = merged_result.get("diagnostics", {}).get("merge", {}).get("merge_ms", 0)
        
        # Add total timing
        total_ms = int((time.time() - start_time) * 1000)
        merged_result["diagnostics"]["timings"] = {
            "rule_ms": rule_ms,
            "llm_ms": llm_ms,
            "merge_ms": merge_ms,
            "total_ms": total_ms
        }
        
        return merged_result
    else:
        # LLM not enabled, return rule-based results
        logger.info("LLM not enabled, returning rule-based extraction only")
        return rule_result