# Partial Article Detection Enhancement

## Quick Code Addition for article_triage.py

Add this to the `ArticleDetector` class:

```python
def detect_partial_article(self, content: str, metadata: Dict[str, Any] = None) -> bool:
    """Detect if content appears to be a partial article"""
    
    indicators = {
        'explicit_markers': [
            '[partial]', '[excerpt]', '[selection]', 
            '...', '[...]', '...[truncated]'
        ],
        'missing_structure': {
            'no_title': not bool(re.search(r'^#\s+.+|^[A-Z][^.!?]{10,50}', content, re.MULTILINE)),
            'no_intro': not any(word in content.lower() for word in ['introduction', 'overview', 'abstract']),
            'no_conclusion': not any(word in content.lower() for word in ['conclusion', 'summary', 'takeaway']),
            'abrupt_start': content[:50].strip()[0].islower() if content else False,
            'abrupt_end': not content.rstrip().endswith(('.', '!', '?', '```'))
        }
    }
    
    # Check explicit markers
    content_lower = content.lower()
    if any(marker in content_lower for marker in indicators['explicit_markers']):
        return True
    
    # Count missing structural elements
    missing_count = sum(indicators['missing_structure'].values())
    
    # If 3+ structural elements are missing, likely partial
    return missing_count >= 3
```

## Enhanced Triage for Partial Content

```python
async def triage_content(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Enhanced triage with partial detection"""
    
    # Detect if partial
    is_partial = self.detector.detect_partial_article(content, metadata)
    
    if is_partial:
        # Adjust analysis approach
        metadata = metadata or {}
        metadata['content_completeness'] = 'partial'
        metadata['capture_hint'] = 'Consider capturing full article for better analysis'
        
        # Use quick mode for partials (less context needed)
        analysis = await self.analyzer.analyze_article_async(content, quick_mode=True)
        
        # Adjust scores for partial content
        if analysis.get('actionability_score'):
            analysis['actionability_score'] = max(1, analysis['actionability_score'] - 2)
        
        # Add partial indicator to classification
        analysis['classification'] = f"partial_{analysis.get('classification', 'reference')}"
        
        # Add note about partial content
        analysis['summary'] = f"[PARTIAL] {analysis.get('summary', '')}"
    
    # Continue with normal flow...
```

## Metadata to Track Completeness

```sql
ALTER TABLE article_metadata ADD COLUMN content_completeness TEXT DEFAULT 'complete';
ALTER TABLE article_metadata ADD COLUMN estimated_completion_percent INTEGER;
```

## CLI Enhancement for Partial Content

```python
@article.command('merge')
@click.argument('memory_ids', nargs=-1, required=True)
def article_merge(memory_ids):
    """Merge multiple partial articles into one complete article.
    
    Example:
      memory article merge id1 id2 id3
    """
    # Combine partial articles
    # Re-run triage on complete content
    # Update the metadata
```