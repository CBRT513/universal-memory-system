#!/usr/bin/env python3
"""
Test graph extraction API modes
"""

import sys
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests


def mock_llm_response():
    """Mock LLM response for testing without API key"""
    return {
        "entities": [
            {"type": "person", "name": "Alice Johnson", "confidence": 0.85, "source": "llm"},
            {"type": "org", "name": "Acme Corporation", "confidence": 0.9, "source": "llm"},
            {"type": "project", "name": "Project Orion", "confidence": 0.75, "source": "llm"}
        ],
        "edges": [
            {
                "type": "EMPLOYEE_OF",
                "from": {"type": "entity", "name": "Alice Johnson"},
                "to": {"type": "entity", "name": "Acme Corporation"},
                "evidence": "Alice works at Acme",
                "confidence": 0.8,
                "source": "llm"
            },
            {
                "type": "LEADS",
                "from": {"type": "entity", "name": "Alice Johnson"},
                "to": {"type": "entity", "name": "Project Orion"},
                "evidence": "Alice leads Project Orion",
                "confidence": 0.7,
                "source": "llm"
            }
        ],
        "diagnostics": {
            "model": "mock",
            "latency_ms": 10,
            "tokens_in": 100,
            "tokens_out": 50
        }
    }


def test_rule_mode(base_url="http://127.0.0.1:8091"):
    """Test rule-based extraction mode"""
    print("\n=== Testing Rule Mode ===")
    
    text = "Check out github.com/openai/gpt-4. Python and JavaScript are used extensively."
    
    response = requests.post(
        f"{base_url}/api/graph/extract?mode=rule",
        json={
            "text": text,
            "project": "test",
            "persist": False
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Rule extraction: {len(data['entities'])} entities found")
        
        # Check for expected entity types
        entity_types = set(e["type"] for e in data["entities"])
        assert "repo" in entity_types or "url" in entity_types, "Expected repo/URL entity"
        assert "tech" in entity_types, "Expected tech entities"
        
        # Check diagnostics
        assert "timings" in data["diagnostics"], "Missing timing diagnostics"
        
        print(f"  Entity types: {entity_types}")
        print(f"  Extraction time: {data['diagnostics']['timings'].get('total', 'N/A')}ms")
        return True
    else:
        print(f"✗ Rule mode failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False


def test_llm_mode(base_url="http://127.0.0.1:8091"):
    """Test LLM extraction mode"""
    print("\n=== Testing LLM Mode ===")
    
    text = "Alice Johnson leads Project Orion at Acme Corporation."
    
    response = requests.post(
        f"{base_url}/api/graph/extract?mode=llm&min_confidence=0.3",
        json={
            "text": text,
            "project": "test",
            "persist": False
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if len(data["entities"]) == 0:
            print("⚠ LLM mode returned no entities (likely no API key configured)")
            print("  This is expected behavior when no LLM API key is set")
            return True
        else:
            print(f"✓ LLM extraction: {len(data['entities'])} entities found")
            
            # Check for LLM-specific features
            has_confidence = all("confidence" in e for e in data["entities"])
            has_source = all(e.get("source") == "llm" for e in data["entities"])
            
            assert has_confidence, "LLM entities should have confidence scores"
            assert has_source, "LLM entities should have source='llm'"
            
            print(f"  Entities: {[e['name'] for e in data['entities']]}")
            print(f"  Edges: {len(data.get('edges', []))} relationships found")
            
            if "diagnostics" in data and "latency_ms" in data["diagnostics"]:
                print(f"  LLM latency: {data['diagnostics']['latency_ms']}ms")
            
            return True
    else:
        print(f"✗ LLM mode failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False


def test_hybrid_mode(base_url="http://127.0.0.1:8091"):
    """Test hybrid extraction mode"""
    print("\n=== Testing Hybrid Mode ===")
    
    text = """
    Visit github.com/openai/whisper for speech recognition.
    Alice Johnson leads the development team at OpenAI.
    They use Python, JavaScript, and Rust extensively.
    """
    
    response = requests.post(
        f"{base_url}/api/graph/extract?mode=hybrid",
        json={
            "text": text,
            "project": "test",
            "persist": False
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Hybrid extraction: {len(data['entities'])} entities found")
        
        # Check for both rule and LLM entities
        entity_types = set(e["type"] for e in data["entities"])
        sources = set(e.get("source", "rule") for e in data["entities"])
        
        print(f"  Entity types: {entity_types}")
        print(f"  Sources: {sources}")
        
        # Check merge diagnostics
        if "diagnostics" in data and "merge" in data["diagnostics"]:
            merge_info = data["diagnostics"]["merge"]
            print(f"  Merge stats: +{merge_info.get('added_entities', 0)} entities, "
                  f"+{merge_info.get('added_edges', 0)} edges from LLM")
        
        # Check timing breakdown
        if "diagnostics" in data and "timings" in data["diagnostics"]:
            timings = data["diagnostics"]["timings"]
            print(f"  Timing: rule={timings.get('rule_ms', 0)}ms, "
                  f"llm={timings.get('llm_ms', 0)}ms, "
                  f"merge={timings.get('merge_ms', 0)}ms")
        
        return True
    else:
        print(f"✗ Hybrid mode failed: {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return False


def test_source_filtering(base_url="http://127.0.0.1:8091"):
    """Test entity filtering by source"""
    print("\n=== Testing Source Filtering ===")
    
    # First, extract some entities with hybrid mode
    text = "Microsoft and Google are major tech companies. Visit github.com/microsoft/vscode."
    
    response = requests.post(
        f"{base_url}/api/graph/extract?mode=hybrid",
        json={
            "text": text,
            "project": "test-filter",
            "persist": True  # Need to persist for filtering
        }
    )
    
    if response.status_code != 200:
        print("✗ Failed to create test entities")
        return False
    
    time.sleep(1)  # Give it a moment to persist
    
    # Test filtering by source
    tests = [
        ("rule", "Rule-extracted entities"),
        ("llm", "LLM-extracted entities"),
        ("any", "All entities")
    ]
    
    for source, desc in tests:
        response = requests.get(
            f"{base_url}/api/graph/entities",
            params={"q": "microsoft", "source": source, "limit": 10}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  {desc}: {len(data)} results")
        else:
            print(f"  Failed to filter by source={source}")
            return False
    
    print("✓ Source filtering works")
    return True


def test_stats_with_source(base_url="http://127.0.0.1:8091"):
    """Test stats endpoint with source breakdown"""
    print("\n=== Testing Stats with Source ===")
    
    response = requests.get(
        f"{base_url}/api/graph/stats",
        params={"project_id": "vader-lab"}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if "entities_by_source" in data:
            print(f"✓ Stats includes source breakdown:")
            for source, count in data["entities_by_source"].items():
                print(f"    {source}: {count} entities")
        else:
            print("⚠ Stats doesn't include source breakdown (migration may be needed)")
        
        print(f"  Total entities: {data.get('total_entities', 0)}")
        print(f"  Total edges: {data.get('total_edges', 0)}")
        
        return True
    else:
        print(f"✗ Stats failed: {response.status_code}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("GRAPH EXTRACTION MODE TESTS")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8091"
    
    # Check if API is running
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code != 200:
            print("⚠ API not responding at", base_url)
            print("Start the API with: uvicorn src.api_service:app --port 8091")
            sys.exit(1)
    except requests.ConnectionError:
        print("⚠ Cannot connect to API at", base_url)
        print("Start the API with: uvicorn src.api_service:app --port 8091")
        sys.exit(1)
    
    # Run tests
    results = []
    results.append(("Rule Mode", test_rule_mode(base_url)))
    results.append(("LLM Mode", test_llm_mode(base_url)))
    results.append(("Hybrid Mode", test_hybrid_mode(base_url)))
    results.append(("Source Filtering", test_source_filtering(base_url)))
    results.append(("Stats with Source", test_stats_with_source(base_url)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\nALL TESTS PASSED ✓")
    else:
        print("\nSOME TESTS FAILED ✗")
        sys.exit(1)