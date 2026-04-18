#!/usr/local/share/universal-memory-system/venv/bin/python3
"""
Manual Content Classifier - Let user define what content actually is
"""

import sys
import json
import requests
from datetime import datetime

def get_user_classification():
    """Ask user to classify the content type"""
    print("\n🔍 What type of content is this?\n")
    print("1. Article (blog post, news, tutorial)")
    print("2. Code snippet")
    print("3. Interface/UI capture")
    print("4. Note/reminder")
    print("5. Documentation")
    print("6. Error/troubleshooting")
    print("7. Other")
    
    while True:
        choice = input("\nSelect type (1-7): ").strip()
        
        type_map = {
            '1': 'article',
            '2': 'code_snippet',
            '3': 'interface_capture',
            '4': 'note',
            '5': 'documentation',
            '6': 'error_log',
            '7': 'other'
        }
        
        if choice in type_map:
            content_type = type_map[choice]
            
            # For articles, get additional info
            if content_type == 'article':
                print("\n📰 Article Details:")
                title = input("Title (optional): ").strip()
                author = input("Author (optional): ").strip()
                priority = input("Priority 1-10 (default 5): ").strip() or "5"
                
                return {
                    'type': content_type,
                    'title': title or None,
                    'author': author or None,
                    'priority': int(priority),
                    'is_actionable': input("Is this actionable? (y/n): ").strip().lower() == 'y'
                }
            else:
                return {'type': content_type}
        else:
            print("Invalid choice. Please select 1-7.")

def store_with_classification(content, classification):
    """Store content with user-provided classification"""
    
    # Determine tags based on classification
    tags = [classification['type']]
    
    if classification['type'] == 'article':
        tags.append('user-classified-article')
        if classification.get('is_actionable'):
            tags.append('actionable')
        if classification.get('priority', 5) >= 8:
            tags.append('high-priority')
    else:
        tags.append('not-article')
    
    # Prepare payload
    payload = {
        'content': content,
        'kind': classification['type'],
        'tags': tags,
        'metadata': {
            'classification_method': 'manual_user',
            'classified_at': datetime.now().isoformat(),
            **{k: v for k, v in classification.items() if v is not None}
        }
    }
    
    # Store in UMS
    try:
        response = requests.post(
            'http://127.0.0.1:8091/api/memory/store',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.ok:
            result = response.json()
            print(f"\n✅ Stored as '{classification['type']}' with ID: {result.get('id', 'unknown')}")
            return result
        else:
            print(f"\n❌ Error storing: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

def reclassify_existing(memory_id):
    """Reclassify an existing memory item"""
    try:
        # Get the existing item
        response = requests.get(f'http://127.0.0.1:8091/api/memory/search?q=id:{memory_id}')
        
        if not response.ok:
            print(f"❌ Could not find memory {memory_id}")
            return
            
        results = response.json().get('results', [])
        if not results:
            print(f"❌ No memory found with ID {memory_id}")
            return
            
        item = results[0]
        print(f"\n📝 Current content: {item['content'][:200]}...")
        print(f"📋 Current type: {item.get('category', 'unknown')}")
        
        # Get new classification
        print("\n🔄 How should this be reclassified?")
        new_classification = get_user_classification()
        
        # Update the item
        update_payload = {
            'memory_id': memory_id,
            'new_category': new_classification['type'],
            'new_tags': [new_classification['type'], 'user-reclassified'],
            'metadata_updates': {
                'reclassified_at': datetime.now().isoformat(),
                'reclassification_method': 'manual_user',
                **{k: v for k, v in new_classification.items() if v is not None}
            }
        }
        
        # Note: This would need a new API endpoint for updating classifications
        print(f"\n✅ Would update {memory_id} to type '{new_classification['type']}'")
        print("📝 Note: Reclassification API endpoint needs to be implemented")
        
    except Exception as e:
        print(f"❌ Error reclassifying: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  # Classify new content")
        print("  python3 manual_classifier.py store \"Your content here\"")
        print("  # Reclassify existing")
        print("  python3 manual_classifier.py reclassify mem_12345")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'store' and len(sys.argv) > 2:
        content = sys.argv[2]
        print(f"📝 Content to classify: {content[:200]}{'...' if len(content) > 200 else ''}")
        
        classification = get_user_classification()
        store_with_classification(content, classification)
        
    elif command == 'reclassify' and len(sys.argv) > 2:
        memory_id = sys.argv[2]
        reclassify_existing(memory_id)
        
    else:
        print("❌ Invalid command. Use 'store' or 'reclassify'")

if __name__ == "__main__":
    main()