#!/usr/bin/env python3
"""
Graph Normalization Module - Milestone C
Handles entity normalization and hashing for deduplication
"""

import re
import json
import unicodedata
import hashlib
from typing import Literal, Optional

# Regex patterns for normalization
_ZW = re.compile(r'[\u200B-\u200D\uFEFF]')  # Zero-width chars
_PUNCT = re.compile(r"[-_\./,;:\|()\[\]{}]+")  # Punctuation to replace
_MULTI = re.compile(r"\s+")  # Multiple spaces

def _nfkc(s: str) -> str:
    """Apply NFKC Unicode normalization"""
    return unicodedata.normalize("NFKC", s)

def normalize_name(raw: str, etype: str) -> str:
    """
    Normalize entity name for deduplication
    
    Args:
        raw: Raw entity name
        etype: Entity type (person, org, tech, concept, etc.)
    
    Returns:
        Normalized name string
    
    Raises:
        ValueError: If normalized name is too short (<2 chars)
    """
    # Unicode normalize and strip
    s = _nfkc(raw or "").strip()
    
    # Remove zero-width chars and lowercase
    s = _ZW.sub("", s).lower()
    
    # Replace punctuation with spaces
    s = _PUNCT.sub(" ", s)
    
    # Collapse multiple spaces
    s = _MULTI.sub(" ", s).strip()
    
    # Remove quotes and backticks
    s = s.strip("'\"`")
    
    # Type-specific processing
    if etype in {"org", "tech", "concept"}:
        # Remove common suffixes for organizations
        s = re.sub(r"\b(inc|ltd|llc|gmbh|sa|plc|corp|co|company)\.?$", "", s, flags=re.IGNORECASE).strip()
    
    # Validate minimum length
    if len(s) < 2:
        raise ValueError(f"Normalized name too short: '{s}' from '{raw}'")
    
    return s

def sha1_16(s: str) -> str:
    """Generate 16-character hash from string"""
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

def entity_hash(etype: str, normalized_name: str, project_id: str) -> str:
    """
    Generate unique entity hash for deduplication
    
    Args:
        etype: Entity type
        normalized_name: Already normalized entity name
        project_id: Project identifier
    
    Returns:
        16-character hash string
    """
    return sha1_16(f"{etype}|{normalized_name}|{project_id}")

def edge_hash(src_id: int, dst_id: int, etype: str, key_props: dict, project_id: str) -> str:
    """
    Generate unique edge hash for idempotency
    
    Args:
        src_id: Source node ID
        dst_id: Destination node ID
        etype: Edge type
        key_props: Identifying properties (will be sorted)
        project_id: Project identifier
    
    Returns:
        16-character hash string
    """
    # Sort keys for consistent hashing
    key = json.dumps(key_props or {}, sort_keys=True, separators=(",", ":"))
    return sha1_16(f"{src_id}|{dst_id}|{etype}|{key}|{project_id}")

def is_valid_entity_name(name: str, etype: str) -> bool:
    """
    Check if entity name is valid for normalization
    
    Args:
        name: Raw entity name
        etype: Entity type
    
    Returns:
        True if name can be normalized, False otherwise
    """
    try:
        normalize_name(name, etype)
        return True
    except (ValueError, AttributeError):
        return False

def extract_initials(name: str) -> str:
    """
    Extract initials from a name (useful for person entities)
    
    Args:
        name: Person's name
    
    Returns:
        Uppercase initials
    """
    words = name.split()
    initials = ''.join(word[0].upper() for word in words if word)
    return initials

def normalize_url(url: str) -> str:
    """
    Normalize URL for consistent comparison
    
    Args:
        url: Raw URL
    
    Returns:
        Normalized URL (lowercase, no trailing slash, no www.)
    """
    if not url:
        return ""
    
    url = url.lower().strip()
    
    # Remove protocol
    url = re.sub(r'^https?://', '', url)
    
    # Remove www.
    url = re.sub(r'^www\.', '', url)
    
    # Remove trailing slash
    url = url.rstrip('/')
    
    return url