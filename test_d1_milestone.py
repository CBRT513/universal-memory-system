#!/usr/bin/env python3
"""
Test script for Milestone D1 - Entity Extraction and Graph API
"""

import sys
import json
import time
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_extraction():
    """Test entity extraction directly"""
    from entity_extraction import extract_entities
    
    text = """
    OpenAI and Anthropic are leading AI companies. 
    GitHub is owned by Microsoft. 
    Python and JavaScript are popular programming languages.
    Check out the repository at github.com/openai/gpt-4.
    Visit https://www.anthropic.com for more information.
    Machine learning and deep learning are transforming technology.
    """
    
    result = extract_entities(text, project="test")
    
    print("=== Entity Extraction Test ===")
    print(f"Extracted {len(result['entities'])} entities:")
    for entity in result['entities']:
        print(f"  - {entity['type']}: {entity['name']} (confidence: {entity['confidence']})")
    
    print(f"\nExtraction took {result['diagnostics']['timings']['total']:.3f}s")
    print(f"Rules fired: {', '.join(result['diagnostics']['rules_fired'])}")
    return result

def test_graph_api(base_url="http://127.0.0.1:8091"):
    """Test Graph API endpoints"""
    print("\n=== Graph API Tests ===")
    
    # Test extraction endpoint
    print("\n1. Testing extraction endpoint...")
    response = requests.post(
        f"{base_url}/api/graph/extract",
        json={
            "text": "Docker and Kubernetes are container orchestration platforms.",
            "project": "vader-lab",
            "persist": True
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Extracted {len(data['entities'])} entities")
    else:
        print(f"   ✗ Failed: {response.status_code}")
    
    # Test entity search
    print("\n2. Testing entity search...")
    response = requests.get(
        f"{base_url}/api/graph/entities",
        params={"q": "docker", "limit": 3}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Found {len(data)} entities matching 'docker'")
        for entity in data[:3]:
            print(f"     - {entity['type']}: {entity['name']}")
    else:
        print(f"   ✗ Failed: {response.status_code}")
    
    # Test document search
    print("\n3. Testing document search...")
    response = requests.get(
        f"{base_url}/api/graph/documents",
        params={"q": "README", "limit": 3}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Found {len(data)} documents")
        for doc in data:
            print(f"     - {doc.get('title', 'Untitled')}: {doc.get('url', 'No URL')[:50]}...")
    else:
        print(f"   ✗ Failed: {response.status_code}")
    
    # Test graph stats
    print("\n4. Testing graph stats...")
    response = requests.get(
        f"{base_url}/api/graph/stats",
        params={"project_id": "vader-lab"}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Graph statistics:")
        print(f"     - Total entities: {data['total_entities']}")
        print(f"     - Total edges: {data['total_edges']}")
        print(f"     - Documents: {data['documents']}")
        print(f"     - Entity types: {json.dumps(data['entities'], indent=8)}")
    else:
        print(f"   ✗ Failed: {response.status_code}")

def test_capture_integration(base_url="http://127.0.0.1:8091"):
    """Test capture with automatic entity extraction"""
    print("\n=== Capture Integration Test ===")
    
    # Capture a URL
    print("\n1. Capturing a URL...")
    response = requests.post(
        f"{base_url}/api/capture",
        json={
            "url": "https://raw.githubusercontent.com/pytorch/pytorch/main/README.md",
            "project": "vader-lab"
        }
    )
    
    if response.status_code in [200, 202]:
        job_id = response.json()["job_id"]
        print(f"   ✓ Capture job created: {job_id}")
        
        # Wait for completion
        print("   Waiting for capture to complete...")
        time.sleep(3)
        
        # Check job status
        response = requests.get(f"{base_url}/api/capture/{job_id}")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "done":
                print(f"   ✓ Capture completed: {data['result']['id']}")
                
                # Check if entities were extracted
                print("\n2. Checking extracted entities...")
                response = requests.get(
                    f"{base_url}/api/graph/entities",
                    params={"q": "pytorch", "limit": 5}
                )
                if response.status_code == 200:
                    entities = response.json()
                    if entities:
                        print(f"   ✓ Found {len(entities)} PyTorch-related entities")
                        for entity in entities[:3]:
                            print(f"     - {entity['type']}: {entity['name']}")
                    else:
                        print("   ⚠ No PyTorch entities found (might be cached)")
                else:
                    print(f"   ✗ Failed to search entities: {response.status_code}")
            else:
                print(f"   ✗ Capture failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ✗ Failed to check job status: {response.status_code}")
    else:
        print(f"   ✗ Failed to create capture job: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("MILESTONE D1 TEST SUITE")
    print("Entity Extraction and Graph API")
    print("=" * 60)
    
    # Test direct extraction
    extraction_result = test_extraction()
    
    # Test Graph API
    test_graph_api()
    
    # Test capture integration
    test_capture_integration()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)