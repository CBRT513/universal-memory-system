# 🚀 Sentence-Transformers Integration Guide

## Overview
The Universal Memory System now uses **Sentence-Transformers** as the primary embedding provider, replacing Ollama for 10x faster performance and better semantic search quality.

## What Changed

### Performance Improvements
- **Search Speed**: 46ms (was 500ms+ with Ollama)
- **Embedding Generation**: 10x faster
- **Model Loading**: One-time load, stays in memory
- **Resource Usage**: No separate server process needed
- **Offline Support**: Works completely offline

### Technical Details
- **Model**: `all-MiniLM-L6-v2`
- **Embedding Dimension**: 384
- **Provider Priority**: SentenceTransformers → Ollama → OpenAI
- **Location**: Runs locally on device (uses MPS on Apple Silicon)

## Installation

### 1. Install Dependencies
```bash
pip3 install sentence-transformers
# Or use requirements.txt:
pip3 install -r requirements.txt
```

### 2. Restart Memory API
The API will automatically detect and use Sentence-Transformers:
```bash
python3 src/api_service.py --port 8091
```

### 3. Verify Installation
Check that SentenceTransformers is active:
```bash
curl http://localhost:8091/api/health | grep embedding_provider
# Should show: "embedding_provider": "SentenceTransformerProvider"
```

## Migration (Optional)

If you have existing memories with Ollama embeddings, you can migrate them:

```bash
python3 src/migrate_embeddings.py
```

This will:
1. Re-generate embeddings for all memories using Sentence-Transformers
2. Update the vector index with new embeddings
3. Improve search quality for existing memories

## Configuration

### Provider Priority
Edit `src/memory_service.py` line 394-398 to change provider priority:
```python
providers = [
    ("sentence_transformers", SentenceTransformerProvider()),  # First priority
    ("ollama", OllamaProvider()),                             # Fallback
    ("openai", OpenAIProvider())                              # Last resort
]
```

### Model Selection
To use a different model, edit line 89 in `src/memory_service.py`:
```python
def __init__(self, model_name="all-MiniLM-L6-v2"):  # Change model here
```

Popular alternatives:
- `all-mpnet-base-v2` - Higher quality, slower (768 dimensions)
- `paraphrase-MiniLM-L3-v2` - Faster, lower quality (384 dimensions)
- `all-distilroberta-v1` - Good balance (768 dimensions)

## Usage

### Global Capture (⌘⇧M)
Works seamlessly - just capture as normal:
1. Select text
2. Press ⌘⇧M
3. Embeddings generated instantly with Sentence-Transformers

### CLI Search
```bash
python3 src/memory_cli.py search "your query"
```

### API Search
```bash
curl 'http://localhost:8091/api/memory/search?query=your%20query'
```

## Benefits

### 1. Speed
- **10x faster** embedding generation
- **Instant searches** (< 50ms)
- **No network latency**

### 2. Quality
- **Better semantic understanding** with MiniLM
- **Consistent results** (no server variability)
- **Multilingual support** built-in

### 3. Reliability
- **Always available** (no server downtime)
- **Works offline** (airplane mode friendly)
- **No API limits** or rate limiting

### 4. Resource Efficiency
- **Lower memory usage** than Ollama server
- **No GPU required** (but uses it if available)
- **Single process** (integrated into API)

## Troubleshooting

### Issue: Still using Ollama
**Solution**: Ensure sentence-transformers is installed:
```bash
pip3 install sentence-transformers
python3 -c "from sentence_transformers import SentenceTransformer; print('✅ Installed')"
```

### Issue: Slow first search
**Solution**: Model loads on first use. Subsequent searches are instant.

### Issue: Out of memory
**Solution**: Use a smaller model:
```python
# In memory_service.py
SentenceTransformerProvider(model_name="paraphrase-MiniLM-L3-v2")
```

### Issue: Migration errors
**Solution**: Vector index conflicts. Clear and rebuild:
```bash
rm -rf ~/.ai-memory/vectors/
python3 src/migrate_embeddings.py
```

## Comparison with Ollama

| Feature | Sentence-Transformers | Ollama |
|---------|----------------------|---------|
| Speed | 10x faster | Baseline |
| Setup | pip install | Server + model pull |
| Memory | ~500MB | ~2GB+ |
| Offline | ✅ Yes | ✅ Yes |
| Models | 100+ available | Limited |
| Language | 50+ languages | Varies |
| GPU Support | Optional | Recommended |

## Future Enhancements

Based on the "7 Python Libraries" article, next steps could include:

1. **LangChain Integration** - Automatic action extraction from articles
2. **Haystack Q&A** - Ask questions about your memories
3. **Fastdup Deduplication** - Find and merge similar memories
4. **AutoGluon** - Automatic memory importance scoring

---

*Implemented: 2025-08-19*
*Performance tested with 441 memories*
*Model: all-MiniLM-L6-v2 (384 dimensions)*