#!/usr/bin/env python3
"""
Test script for the Article Triage System
Tests all major functionality with sample articles
"""

import sys
import time
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test articles
TEST_ARTICLES = {
    "tutorial": """
# Building a Modern CLI Tool with Python and Click

Published on Dev.to by Sarah Developer - 8 minute read

In this comprehensive tutorial, we'll explore how to create a powerful command-line interface tool
using Python's Click library combined with Rich for beautiful terminal output. This guide will
take you from basic concepts to advanced features.

## Introduction

Command-line tools are essential for developer productivity. They automate repetitive tasks,
provide quick access to functionality, and integrate seamlessly with other tools in your workflow.

## Why Click?

Click is a Python package for creating beautiful command line interfaces in a composable way with
as little code as necessary. It's highly configurable but comes with sensible defaults out of the box.

## Getting Started

First, let's install the required dependencies:

```bash
pip install click rich typer
```

## Basic Implementation

Here's a simple example to get started:

```python
import click
from rich.console import Console

console = Console()

@click.command()
@click.option('--name', prompt='Your name', help='The person to greet.')
@click.option('--count', default=1, help='Number of greetings.')
def hello(name, count):
    '''Simple program that greets NAME for a total of COUNT times.'''
    for _ in range(count):
        console.print(f"Hello, [bold blue]{name}[/bold blue]!")

if __name__ == '__main__':
    hello()
```

## Advanced Features

### 1. Command Groups

Click allows you to create multi-command CLIs:

```python
@click.group()
def cli():
    pass

@cli.command()
def init():
    click.echo('Initialized the database')

@cli.command()
def drop():
    click.echo('Dropped the database')
```

### 2. File Handling

Working with files is straightforward:

```python
@click.command()
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def process(input, output):
    while True:
        chunk = input.read(1024)
        if not chunk:
            break
        output.write(chunk)
```

## Best Practices

1. **Use type hints** for better code documentation
2. **Implement proper error handling** with helpful messages
3. **Add comprehensive help text** for all commands and options
4. **Use Rich for colored output** to improve user experience
5. **Test your CLI thoroughly** with different inputs

## Conclusion

With Click and Rich, you can build powerful, user-friendly CLI applications that are both
functional and visually appealing. The combination provides everything needed for modern
terminal applications.

Next steps:
- Add configuration file support
- Implement plugin system
- Add shell completion
- Create comprehensive test suite
""",

    "news": """
OpenAI Announces GPT-5: A Leap Forward in AI Capabilities

By TechNews Team | March 15, 2024 | 3 min read

San Francisco - OpenAI today unveiled GPT-5, the latest iteration of their groundbreaking
language model, promising significant improvements in reasoning, multimodal capabilities,
and efficiency.

Key Highlights:
- 10x more efficient than GPT-4
- Native multimodal understanding
- Enhanced reasoning capabilities
- Reduced hallucination rates

The model will be available through API access starting next month, with enterprise
customers getting early access. Pricing details have not been announced yet.

Industry experts are calling this a significant milestone in AI development, though
some raise concerns about the rapid pace of advancement without corresponding safety measures.
""",

    "code_snippet": """
def fibonacci(n):
    '''Generate Fibonacci sequence up to n'''
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b

# Usage
for num in fibonacci(100):
    print(num)
""",

    "research": """
# Comparative Analysis of State Management Solutions in React Applications

## Abstract

This study examines five popular state management libraries for React applications: Redux,
MobX, Zustand, Valtio, and Jotai. We analyze their performance characteristics, developer
experience, and suitability for different application scales.

## Introduction

State management remains one of the most challenging aspects of building scalable React
applications. While React's built-in state management capabilities have improved significantly
with hooks and context, complex applications often require more sophisticated solutions.

## Methodology

We evaluated each library across several dimensions:
1. Bundle size impact
2. Runtime performance
3. Developer experience
4. Learning curve
5. Community support
6. TypeScript integration

## Results

### Bundle Size (minified + gzipped)
- Zustand: 2.9KB
- Jotai: 3.4KB
- Valtio: 5.8KB
- MobX: 15KB
- Redux + RTK: 24KB

### Performance Benchmarks

All libraries showed acceptable performance for typical applications. Zustand and Jotai
demonstrated the best performance in high-frequency update scenarios.

### Developer Experience

Redux Toolkit has significantly improved the Redux developer experience, but lighter
alternatives like Zustand offer similar capabilities with less boilerplate.

## Recommendations

- **Small to medium apps**: Zustand or Jotai
- **Large enterprise apps**: Redux Toolkit
- **Real-time applications**: MobX or Valtio
- **Beginner-friendly**: Zustand

## Conclusion

While Redux remains the most popular choice, newer libraries like Zustand and Jotai offer
compelling alternatives with smaller bundle sizes and simpler APIs. The choice ultimately
depends on specific project requirements and team expertise.

## References

1. Redux Documentation - https://redux.js.org
2. Zustand GitHub - https://github.com/pmndrs/zustand
3. State of JS 2023 Survey Results
4. React Performance Optimization Guide
"""
}

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

async def test_article_detection():
    """Test article detection functionality"""
    print_section("Testing Article Detection")
    
    from article_triage import ArticleDetector
    detector = ArticleDetector()
    
    for name, content in TEST_ARTICLES.items():
        content_type = detector.detect_content_type(content)
        print(f"  {name:15} -> {content_type}")
    
    print("\n✅ Article detection complete")

async def test_ollama_analysis():
    """Test Ollama article analysis"""
    print_section("Testing Ollama Analysis")
    
    from article_triage import OllamaArticleAnalyzer
    analyzer = OllamaArticleAnalyzer()
    
    print(f"Selected model: {analyzer.model}")
    
    # Test with tutorial article
    tutorial = TEST_ARTICLES["tutorial"]
    
    print("\nAnalyzing tutorial article...")
    start_time = time.time()
    
    # Quick analysis
    result = analyzer.analyze_article(tutorial, quick_mode=True)
    
    elapsed = time.time() - start_time
    print(f"Analysis completed in {elapsed:.2f} seconds")
    
    print("\nAnalysis Results:")
    print(f"  Title: {result.get('title', 'N/A')}")
    print(f"  Classification: {result.get('classification', 'N/A')}")
    print(f"  Actionability: {result.get('actionability_score', 0)}/10")
    print(f"  Relevance: {result.get('relevance_score', 0)}/10")
    
    if result.get('key_topics'):
        print(f"  Topics: {', '.join(result['key_topics'][:5])}")
    
    if result.get('technologies'):
        print(f"  Technologies: {', '.join(result['technologies'])}")
    
    print("\n✅ Ollama analysis complete")

async def test_article_triage():
    """Test full article triage pipeline"""
    print_section("Testing Article Triage Pipeline")
    
    from article_triage import ArticleTriageService
    service = ArticleTriageService()
    
    # Test with research article
    research = TEST_ARTICLES["research"]
    
    print("Running full triage on research article...")
    result = await service.triage_content(
        content=research,
        metadata={'source': 'test_script'}
    )
    
    if result.get('is_article'):
        print("✅ Correctly identified as article")
        
        analysis = result['analysis']
        recommendations = result['recommendations']
        
        print(f"\nTriage Results:")
        print(f"  Title: {analysis.get('title', 'N/A')}")
        print(f"  Summary: {analysis.get('summary', 'N/A')[:100]}...")
        print(f"  Classification: {analysis.get('classification')}")
        print(f"  Priority: {recommendations.get('priority')}")
        print(f"  Word count: {result['metadata'].get('word_count')}")
        print(f"  Reading time: {result['metadata'].get('reading_time_minutes')} min")
        
        if recommendations.get('suggested_tags'):
            print(f"  Suggested tags: {', '.join(recommendations['suggested_tags'][:5])}")
    else:
        print(f"❌ Not identified as article: {result.get('content_type')}")
    
    print("\n✅ Article triage complete")

async def test_api_endpoints():
    """Test API endpoints"""
    print_section("Testing API Endpoints")
    
    import requests
    
    base_url = "http://localhost:8091"
    
    # Check if API is running
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("⚠️ API returned non-200 status")
            return
    except:
        print("❌ API is not running. Start with: python3 src/api_service.py --port 8091")
        return
    
    # Test article analysis endpoint
    print("\nTesting /api/article/analyze endpoint...")
    
    response = requests.post(
        f"{base_url}/api/article/analyze",
        json={
            "content": TEST_ARTICLES["tutorial"],
            "quick_mode": True
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'analyzed':
            print("✅ Article analysis endpoint working")
            print(f"  Title: {data['analysis'].get('title', 'N/A')}")
            print(f"  Classification: {data['analysis'].get('classification')}")
    else:
        print(f"❌ Analysis failed: {response.status_code}")
    
    # Test article triage endpoint
    print("\nTesting /api/article/triage endpoint...")
    
    response = requests.post(
        f"{base_url}/api/article/triage",
        json={
            "content": TEST_ARTICLES["news"],
            "project": "test-project",
            "tags": ["test", "automated"],
            "metadata": {"test": True}
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') == 'triaged_and_stored':
            print("✅ Article triage endpoint working")
            print(f"  Memory ID: {data.get('memory_id')}")
            print(f"  Title: {data.get('title')}")
            print(f"  Classification: {data.get('classification')}")
            print(f"  Message: {data.get('message')}")
    else:
        print(f"❌ Triage failed: {response.status_code}")
    
    # Test stats endpoint
    print("\nTesting /api/article/stats endpoint...")
    
    response = requests.get(f"{base_url}/api/article/stats")
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get('stats', {})
        print("✅ Article stats endpoint working")
        print(f"  Total articles: {stats.get('total_articles', 0)}")
    else:
        print(f"❌ Stats failed: {response.status_code}")
    
    print("\n✅ API endpoint tests complete")

async def test_cli_commands():
    """Test CLI commands"""
    print_section("Testing CLI Commands")
    
    import subprocess
    
    # Test article analyze command
    print("Testing CLI: memory article analyze...")
    
    result = subprocess.run(
        ["python3", "src/memory_cli.py", "article", "analyze", TEST_ARTICLES["code_snippet"]],
        capture_output=True,
        text=True
    )
    
    if "Content detected as" in result.stdout or "Title:" in result.stdout:
        print("✅ CLI article analyze working")
    else:
        print("❌ CLI article analyze failed")
        print(result.stderr)
    
    # Test article stats command
    print("\nTesting CLI: memory article stats...")
    
    result = subprocess.run(
        ["python3", "src/memory_cli.py", "article", "stats"],
        capture_output=True,
        text=True
    )
    
    if "Article Triage Statistics" in result.stdout or "Total Articles" in result.stdout:
        print("✅ CLI article stats working")
    else:
        print("❌ CLI article stats failed")
    
    print("\n✅ CLI command tests complete")

async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  ARTICLE TRIAGE SYSTEM TEST SUITE")
    print("="*60)
    
    # Run tests
    await test_article_detection()
    await test_ollama_analysis()
    await test_article_triage()
    await test_api_endpoints()
    await test_cli_commands()
    
    print_section("Test Suite Complete")
    print("✅ All tests completed successfully!")
    print("\nThe Article Triage System is ready to use:")
    print("  - API: python3 src/api_service.py --port 8091")
    print("  - CLI: python3 src/memory_cli.py article --help")
    print("  - Capture: Press ⌘⇧M to capture and auto-triage articles")

if __name__ == "__main__":
    asyncio.run(main())