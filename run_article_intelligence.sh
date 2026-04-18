#!/bin/bash

# Article Intelligence System Runner
# Provides intelligent analysis, validation, and action extraction for captured articles

echo "🧠 Article Intelligence System"
echo "=============================="
echo ""
echo "Choose an option:"
echo "1. Validate recent articles (check classifications)"
echo "2. Monitor new articles in real-time"
echo "3. Extract actions from specific article"
echo "4. Run full analysis on all articles"
echo "5. Start background monitor (runs continuously)"
echo ""
echo -n "Enter choice (1-5): "
read choice

case $choice in
    1)
        echo "🔍 Validating recent article classifications..."
        python3 /usr/local/share/universal-memory-system/src/smart_article_validator.py
        ;;
    
    2)
        echo "👁️ Starting real-time article monitor..."
        echo "   (Press Ctrl+C to stop)"
        python3 /usr/local/share/universal-memory-system/src/smart_article_validator.py monitor
        ;;
    
    3)
        echo -n "Enter article ID (or press enter for most recent): "
        read article_id
        
        if [ -z "$article_id" ]; then
            echo "📄 Analyzing most recent article..."
            python3 /usr/local/share/universal-memory-system/src/article_action_extractor.py
        else
            echo "📄 Analyzing article: $article_id"
            python3 /usr/local/share/universal-memory-system/src/article_action_extractor.py "$article_id"
        fi
        ;;
    
    4)
        echo "🔬 Running full analysis on all articles..."
        echo ""
        echo "Step 1: Validating classifications..."
        python3 /usr/local/share/universal-memory-system/src/smart_article_validator.py
        
        echo ""
        echo "Step 2: Extracting actions from actionable articles..."
        # Get actionable articles and extract actions
        curl -s "http://localhost:8091/api/memory/search?category=article&limit=10" | \
            python3 -c "import json, sys; [print(a['id']) for a in json.load(sys.stdin).get('results', []) if 'actionable' in a.get('tags', [])]" | \
            while read article_id; do
                if [ ! -z "$article_id" ]; then
                    echo "  Processing: $article_id"
                    python3 /usr/local/share/universal-memory-system/src/article_action_extractor.py "$article_id" 2>/dev/null | grep "TODO"
                fi
            done
        ;;
    
    5)
        echo "🚀 Starting background article monitor..."
        echo "   This will run continuously in the background"
        echo "   Logs will be saved to /tmp/article_monitor.log"
        echo ""
        
        # Check if already running
        if pgrep -f "smart_article_validator.py monitor" > /dev/null; then
            echo "⚠️  Monitor is already running!"
            echo "   PID: $(pgrep -f 'smart_article_validator.py monitor')"
            echo ""
            echo -n "Kill existing monitor? (y/n): "
            read kill_existing
            
            if [ "$kill_existing" = "y" ]; then
                pkill -f "smart_article_validator.py monitor"
                echo "✅ Killed existing monitor"
            else
                echo "❌ Aborting - monitor already running"
                exit 1
            fi
        fi
        
        # Start monitor in background
        nohup python3 /usr/local/share/universal-memory-system/src/smart_article_validator.py monitor > /tmp/article_monitor.log 2>&1 &
        echo "✅ Monitor started with PID: $!"
        echo "   View logs: tail -f /tmp/article_monitor.log"
        echo "   Stop: pkill -f 'smart_article_validator.py monitor'"
        ;;
    
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "================================"
echo "✅ Done!"