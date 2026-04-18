#!/usr/bin/env python3
"""
LLM-Enhanced Entity Extraction Module - Milestone D2
Uses Anthropic or OpenAI for advanced entity and relationship extraction
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict
import re

logger = logging.getLogger(__name__)

# Check for available LLM providers
HAS_ANTHROPIC = False
HAS_OPENAI = False

try:
    if os.environ.get("ANTHROPIC_API_KEY"):
        import anthropic
        HAS_ANTHROPIC = True
        logger.info("Anthropic API available for LLM extraction")
except ImportError:
    pass

try:
    if os.environ.get("OPENAI_API_KEY"):
        import openai
        HAS_OPENAI = True
        logger.info("OpenAI API available for LLM extraction")
except ImportError:
    pass

# Rate limiting (simple token bucket)
class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, calls_per_minute: int = 10):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        now = time.time()
        time_since_last = now - self.last_call_time
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        self.last_call_time = time.time()

# Global rate limiters
anthropic_limiter = RateLimiter(calls_per_minute=20)
openai_limiter = RateLimiter(calls_per_minute=30)

def extract_with_llm(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Extract entities and relationships using LLM
    
    Args:
        text: Text to extract from
        context: Optional context (metadata, project, etc.)
    
    Returns:
        Dict with entities, edges, and diagnostics
    """
    # Check text length limits
    max_chars = int(os.environ.get("LLM_MAX_TEXT_LENGTH", "10000"))
    if len(text) > max_chars:
        # Truncate intelligently - keep beginning and end
        keep_chars = max_chars // 2 - 100
        text = text[:keep_chars] + "\n\n[...content truncated...]\n\n" + text[-keep_chars:]
    
    # Choose provider
    if HAS_ANTHROPIC:
        return _extract_with_anthropic(text, context)
    elif HAS_OPENAI:
        return _extract_with_openai(text, context)
    else:
        # No LLM available - return empty result
        return {
            "entities": [],
            "edges": [],
            "diagnostics": {
                "model": "none",
                "error": "No LLM API key configured"
            }
        }

def _extract_with_anthropic(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Extract using Anthropic Claude"""
    start_time = time.time()
    
    try:
        anthropic_limiter.wait_if_needed()
        
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        
        # Build prompt
        prompt = _build_extraction_prompt(text, context)
        
        # Call API
        model = os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "1000"))
        temperature = float(os.environ.get("LLM_TEMPERATURE", "0.1"))
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response
        result_text = response.content[0].text
        result = _parse_llm_response(result_text)
        
        # Add diagnostics
        latency_ms = int((time.time() - start_time) * 1000)
        result["diagnostics"] = {
            "model": model,
            "latency_ms": latency_ms,
            "tokens_in": len(prompt.split()),  # Approximate
            "tokens_out": len(result_text.split()),  # Approximate
            "provider": "anthropic"
        }
        
        return result
        
    except Exception as e:
        logger.warning(f"Anthropic extraction failed: {e}")
        return {
            "entities": [],
            "edges": [],
            "diagnostics": {
                "model": "claude",
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        }

def _extract_with_openai(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Extract using OpenAI GPT"""
    start_time = time.time()
    
    try:
        openai_limiter.wait_if_needed()
        
        import openai
        openai.api_key = os.environ["OPENAI_API_KEY"]
        
        # Build prompt
        prompt = _build_extraction_prompt(text, context)
        
        # Call API
        model = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")
        max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "1000"))
        temperature = float(os.environ.get("LLM_TEMPERATURE", "0.1"))
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert at extracting entities and relationships from text. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Parse response
        result_text = response.choices[0].message.content
        result = _parse_llm_response(result_text)
        
        # Add diagnostics
        latency_ms = int((time.time() - start_time) * 1000)
        result["diagnostics"] = {
            "model": model,
            "latency_ms": latency_ms,
            "tokens_in": response.usage.prompt_tokens if hasattr(response, 'usage') else len(prompt.split()),
            "tokens_out": response.usage.completion_tokens if hasattr(response, 'usage') else len(result_text.split()),
            "provider": "openai"
        }
        
        return result
        
    except Exception as e:
        logger.warning(f"OpenAI extraction failed: {e}")
        return {
            "entities": [],
            "edges": [],
            "diagnostics": {
                "model": "gpt",
                "error": str(e),
                "latency_ms": int((time.time() - start_time) * 1000)
            }
        }

def _build_extraction_prompt(text: str, context: Optional[Dict] = None) -> str:
    """Build the extraction prompt for LLM"""
    
    prompt = """Extract entities and relationships from the following text. Focus on:
1. Disambiguating abbreviated names (e.g., MSFT -> Microsoft)
2. Finding employment relationships (who works where, who leads what)
3. Project/product relationships (what builds/uses what)
4. Technical dependencies and references

Text to analyze:
---
{text}
---

Respond with ONLY valid JSON in this exact format:
{{
  "entities": [
    {{
      "type": "org|person|project|tech|repo|url|concept",
      "name": "Full name",
      "aliases": ["Alternative names"],
      "confidence": 0.0-1.0,
      "source": "llm"
    }}
  ],
  "edges": [
    {{
      "type": "MENTIONS|RELATED_TO|EMPLOYEE_OF|LEADS|BUILDS|REFERS_TO|USES|DEPENDS_ON",
      "from": {{"type": "entity", "name": "source entity name"}},
      "to": {{"type": "entity", "name": "target entity name"}},
      "evidence": "snippet from text supporting this relationship",
      "confidence": 0.0-1.0,
      "source": "llm"
    }}
  ]
}}

Rules:
- Only include entities and relationships explicitly mentioned or strongly implied
- Set confidence based on how clear the information is (1.0 = explicit, 0.5 = implied)
- Include evidence snippets for relationships
- Disambiguate common abbreviations (API -> Application Programming Interface if that's the context)
- For people, use full names when possible
- For organizations, use official names (e.g., "Microsoft Corporation" not just "MS")
""".format(text=text[:5000])  # Limit text in prompt
    
    return prompt

def _parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response into structured format"""
    
    # Try to extract JSON from response
    try:
        # Look for JSON block
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            json_text = json_match.group(0)
            data = json.loads(json_text)
        else:
            # Try parsing entire response as JSON
            data = json.loads(response_text)
        
        # Validate and normalize structure
        result = {
            "entities": [],
            "edges": []
        }
        
        # Process entities
        for entity in data.get("entities", []):
            if isinstance(entity, dict) and "name" in entity and "type" in entity:
                normalized_entity = {
                    "type": entity.get("type", "concept"),
                    "name": entity["name"],
                    "aliases": entity.get("aliases", []),
                    "confidence": float(entity.get("confidence", 0.7)),
                    "source": "llm"
                }
                result["entities"].append(normalized_entity)
        
        # Process edges
        for edge in data.get("edges", []):
            if isinstance(edge, dict) and "from" in edge and "to" in edge:
                normalized_edge = {
                    "type": edge.get("type", "RELATED_TO"),
                    "from": edge["from"],
                    "to": edge["to"],
                    "evidence": edge.get("evidence", ""),
                    "confidence": float(edge.get("confidence", 0.6)),
                    "source": "llm"
                }
                result["edges"].append(normalized_edge)
        
        return result
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse LLM response: {e}")
        logger.debug(f"Response was: {response_text[:500]}")
        return {
            "entities": [],
            "edges": [],
            "diagnostics": {
                "parse_error": str(e)
            }
        }

def merge_extractions(rule_result: Dict, llm_result: Dict, min_confidence: float = 0.2) -> Dict[str, Any]:
    """
    Merge rule-based and LLM extraction results
    
    Args:
        rule_result: Result from rule-based extraction
        llm_result: Result from LLM extraction
        min_confidence: Minimum confidence for LLM entities
    
    Returns:
        Merged result with deduplication
    """
    start_time = time.time()
    
    # Start with rule-based results
    merged = {
        "entities": list(rule_result.get("entities", [])),
        "edges": list(rule_result.get("edges", [])),
        "diagnostics": {}
    }
    
    # Track seen entities for deduplication (normalized name -> entity)
    seen_entities = {}
    
    # Index rule-based entities by normalized name
    try:
        from graph_normalization import normalize_name
    except ImportError:
        from .graph_normalization import normalize_name
    
    for entity in merged["entities"]:
        try:
            normalized = normalize_name(entity["name"], entity["type"])
            seen_entities[f"{entity['type']}:{normalized}"] = entity
        except:
            # If normalization fails, use raw name
            seen_entities[f"{entity['type']}:{entity['name'].lower()}"] = entity
    
    # Add LLM entities if not duplicates and above confidence threshold
    added_entities = 0
    for entity in llm_result.get("entities", []):
        if entity.get("confidence", 0) < min_confidence:
            continue
        
        try:
            normalized = normalize_name(entity["name"], entity["type"])
            key = f"{entity['type']}:{normalized}"
        except:
            key = f"{entity['type']}:{entity['name'].lower()}"
        
        if key not in seen_entities:
            merged["entities"].append(entity)
            seen_entities[key] = entity
            added_entities += 1
        else:
            # Merge aliases if LLM found any
            existing = seen_entities[key]
            if "aliases" not in existing:
                existing["aliases"] = []
            for alias in entity.get("aliases", []):
                if alias not in existing["aliases"] and alias != existing["name"]:
                    existing["aliases"].append(alias)
    
    # Add LLM edges if above confidence threshold
    added_edges = 0
    for edge in llm_result.get("edges", []):
        if edge.get("confidence", 0) < min_confidence:
            continue
        merged["edges"].append(edge)
        added_edges += 1
    
    # Merge diagnostics
    merge_ms = int((time.time() - start_time) * 1000)
    merged["diagnostics"] = {
        "rule": rule_result.get("diagnostics", {}),
        "llm": llm_result.get("diagnostics", {}),
        "merge": {
            "added_entities": added_entities,
            "added_edges": added_edges,
            "total_entities": len(merged["entities"]),
            "total_edges": len(merged["edges"]),
            "merge_ms": merge_ms
        }
    }
    
    return merged

# Configuration helpers
def is_llm_enabled() -> bool:
    """Check if LLM extraction is enabled"""
    return HAS_ANTHROPIC or HAS_OPENAI

def get_llm_config() -> Dict[str, Any]:
    """Get current LLM configuration"""
    return {
        "enabled": is_llm_enabled(),
        "provider": "anthropic" if HAS_ANTHROPIC else ("openai" if HAS_OPENAI else None),
        "model": os.environ.get("LLM_MODEL", "default"),
        "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "1000")),
        "temperature": float(os.environ.get("LLM_TEMPERATURE", "0.1")),
        "min_confidence": float(os.environ.get("LLM_MIN_CONFIDENCE", "0.2")),
        "extract_on_capture": os.environ.get("LLM_EXTRACT_ON_CAPTURE", "false").lower() == "true"
    }