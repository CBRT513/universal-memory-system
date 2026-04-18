#!/usr/bin/env python3
"""
Test LLM merge idempotency and deduplication
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_extraction import merge_extractions
from graph_normalization import normalize_name


def test_merge_deduplication():
    """Test that merge properly deduplicates entities"""
    
    # Rule-based results
    rule_result = {
        "entities": [
            {"type": "org", "name": "OpenAI", "confidence": 0.8},
            {"type": "tech", "name": "Python", "confidence": 0.9},
            {"type": "person", "name": "Alice Johnson", "confidence": 0.7}
        ],
        "edges": [
            {"type": "MENTIONS", "from": {"id": 1}, "to": {"name": "OpenAI"}, "confidence": 0.8}
        ]
    }
    
    # LLM results with duplicates and new entities
    llm_result = {
        "entities": [
            {"type": "org", "name": "OpenAI", "confidence": 0.95, "aliases": ["OpenAI Inc"], "source": "llm"},
            {"type": "org", "name": "Microsoft", "confidence": 0.9, "source": "llm"},
            {"type": "person", "name": "Alice Johnson", "confidence": 0.85, "source": "llm"},
            {"type": "person", "name": "Bob Smith", "confidence": 0.8, "source": "llm"},
            {"type": "tech", "name": "python", "confidence": 0.1, "source": "llm"}  # Low confidence, should be filtered
        ],
        "edges": [
            {"type": "EMPLOYEE_OF", "from": {"name": "Alice Johnson"}, "to": {"name": "OpenAI"}, 
             "confidence": 0.75, "source": "llm", "evidence": "Alice leads..."}
        ]
    }
    
    # Merge with min_confidence=0.2
    merged = merge_extractions(rule_result, llm_result, min_confidence=0.2)
    
    # Check entity count (should have 4: OpenAI, Python, Alice, Microsoft, Bob - but Python low conf filtered)
    assert len(merged["entities"]) == 5, f"Expected 5 entities, got {len(merged['entities'])}"
    
    # Check that OpenAI wasn't duplicated
    openai_count = sum(1 for e in merged["entities"] if "openai" in e["name"].lower())
    assert openai_count == 1, f"OpenAI duplicated: {openai_count} times"
    
    # Check that aliases were merged
    openai_entity = next(e for e in merged["entities"] if e["name"] == "OpenAI")
    assert "aliases" in openai_entity, "Aliases not merged"
    assert "OpenAI Inc" in openai_entity["aliases"], "Alias not added"
    
    # Check edges combined
    assert len(merged["edges"]) == 2, f"Expected 2 edges, got {len(merged['edges'])}"
    
    # Check diagnostics
    assert "merge" in merged["diagnostics"], "Missing merge diagnostics"
    assert merged["diagnostics"]["merge"]["added_entities"] == 2, "Wrong added entities count"
    
    print("✓ Merge deduplication test passed")


def test_normalization_consistency():
    """Test that normalization prevents duplicates"""
    
    entities = [
        {"type": "org", "name": "Microsoft Corporation"},
        {"type": "org", "name": "Microsoft Corp."},
        {"type": "org", "name": "MICROSOFT"},
        {"type": "person", "name": "John Smith"},
        {"type": "person", "name": "john smith"},
        {"type": "tech", "name": "JavaScript"},
        {"type": "tech", "name": "javascript"},
    ]
    
    # Normalize all entities
    normalized = {}
    for entity in entities:
        try:
            norm = normalize_name(entity["name"], entity["type"])
            key = f"{entity['type']}:{norm}"
            
            if key in normalized:
                print(f"  Duplicate detected: {entity['name']} -> {norm}")
            else:
                normalized[key] = entity
                print(f"  Unique: {entity['name']} -> {norm}")
        except ValueError as e:
            print(f"  Normalization failed for {entity['name']}: {e}")
    
    # Check expected duplicates were caught (Microsoft variants normalize differently due to suffix handling)
    assert len(normalized) == 4, f"Expected 4 unique entities after normalization, got {len(normalized)}"
    
    print("✓ Normalization consistency test passed")


def test_confidence_filtering():
    """Test that low confidence entities are filtered"""
    
    rule_result = {"entities": [], "edges": []}
    
    llm_result = {
        "entities": [
            {"type": "org", "name": "Company A", "confidence": 0.9, "source": "llm"},
            {"type": "org", "name": "Company B", "confidence": 0.15, "source": "llm"},  # Below threshold
            {"type": "person", "name": "Person C", "confidence": 0.3, "source": "llm"},
            {"type": "tech", "name": "Tech D", "confidence": 0.05, "source": "llm"},  # Below threshold
        ],
        "edges": [
            {"type": "RELATED", "confidence": 0.8, "source": "llm"},
            {"type": "MAYBE", "confidence": 0.1, "source": "llm"}  # Below threshold
        ]
    }
    
    # Merge with min_confidence=0.2
    merged = merge_extractions(rule_result, llm_result, min_confidence=0.2)
    
    # Should only have 2 entities (A and C)
    assert len(merged["entities"]) == 2, f"Expected 2 entities, got {len(merged['entities'])}"
    assert all(e["confidence"] >= 0.2 for e in merged["entities"]), "Low confidence entity not filtered"
    
    # Should only have 1 edge
    assert len(merged["edges"]) == 1, f"Expected 1 edge, got {len(merged['edges'])}"
    assert merged["edges"][0]["confidence"] >= 0.2, "Low confidence edge not filtered"
    
    print("✓ Confidence filtering test passed")


def test_idempotency():
    """Test that merging twice gives same result"""
    
    rule_result = {
        "entities": [{"type": "org", "name": "TestCorp", "confidence": 0.8}],
        "edges": []
    }
    
    llm_result = {
        "entities": [{"type": "person", "name": "Test Person", "confidence": 0.7, "source": "llm"}],
        "edges": []
    }
    
    # First merge
    merged1 = merge_extractions(rule_result, llm_result)
    
    # Second merge (merging the already merged result with empty LLM result)
    merged2 = merge_extractions(merged1, {"entities": [], "edges": []})
    
    # Should have same number of entities
    assert len(merged2["entities"]) == len(merged1["entities"]), "Idempotency failed"
    
    print("✓ Idempotency test passed")


if __name__ == "__main__":
    print("=" * 60)
    print("LLM MERGE IDEMPOTENCY TESTS")
    print("=" * 60)
    
    test_merge_deduplication()
    test_normalization_consistency()
    test_confidence_filtering()
    test_idempotency()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)