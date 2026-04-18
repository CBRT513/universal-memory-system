# LLM-Enhanced Entity Extraction Configuration

## Overview
The system supports LLM-augmented entity extraction using either Anthropic Claude or OpenAI GPT models. This enhances the rule-based extraction with:

- Disambiguation of abbreviated names (e.g., "MSFT" → "Microsoft Corporation")
- Detection of employment and leadership relationships
- Extraction of project/product relationships
- Recognition of technical dependencies

## Environment Variables

### API Keys (at least one required for LLM features)
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude models
- `OPENAI_API_KEY`: Your OpenAI API key for GPT models

**Note**: If both keys are present, Anthropic is preferred.

### LLM Configuration
- `LLM_MODEL`: Model to use (defaults: `claude-3-haiku-20240307` for Anthropic, `gpt-3.5-turbo` for OpenAI)
- `LLM_MAX_TOKENS`: Maximum tokens for response (default: `1000`)
- `LLM_TEMPERATURE`: Temperature for generation (default: `0.1` for consistency)
- `LLM_MIN_CONFIDENCE`: Minimum confidence threshold for LLM entities (default: `0.2`)
- `LLM_MAX_TEXT_LENGTH`: Maximum text length before truncation (default: `10000`)

### Automatic Extraction
- `LLM_EXTRACT_ON_CAPTURE`: Enable automatic hybrid extraction on capture (default: `false`)

## Usage

### Setting Up

#### Option 1: Export in shell
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."

# Optional configurations
export LLM_MODEL="claude-3-opus-20240229"  # For better quality
export LLM_MIN_CONFIDENCE="0.3"  # Higher threshold
export LLM_EXTRACT_ON_CAPTURE="true"  # Auto-extract on captures
```

#### Option 2: Create .env file
```bash
# Create .env in project root
cat > /usr/local/share/universal-memory-system/.env << EOF
ANTHROPIC_API_KEY=sk-ant-...
LLM_MODEL=claude-3-haiku-20240307
LLM_MIN_CONFIDENCE=0.2
LLM_EXTRACT_ON_CAPTURE=false
EOF
```

### API Endpoints

#### Extract with different modes

**Rule-based only** (no API key needed):
```bash
curl -X POST 'http://127.0.0.1:8091/api/graph/extract?mode=rule' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Alice leads Project Orion at OpenAI."}'
```

**LLM only** (requires API key):
```bash
curl -X POST 'http://127.0.0.1:8091/api/graph/extract?mode=llm&min_confidence=0.3' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Alice leads Project Orion at OpenAI."}'
```

**Hybrid** (rule + LLM merged):
```bash
curl -X POST 'http://127.0.0.1:8091/api/graph/extract?mode=hybrid' \
  -H 'Content-Type: application/json' \
  -d '{"text":"Alice leads Project Orion at OpenAI."}'
```

#### Filter entities by source

```bash
# Get only LLM-extracted entities
curl 'http://127.0.0.1:8091/api/graph/entities?q=openai&source=llm'

# Get only rule-extracted entities
curl 'http://127.0.0.1:8091/api/graph/entities?q=openai&source=rule'

# Get all entities (default)
curl 'http://127.0.0.1:8091/api/graph/entities?q=openai&source=any'
```

#### Get statistics by source

```bash
curl 'http://127.0.0.1:8091/api/graph/stats?project_id=vader-lab'
```

Returns counts broken down by extraction source:
```json
{
  "entities_by_source": {
    "rule": 45,
    "llm": 12
  },
  ...
}
```

## Extraction Modes

### Rule Mode
- Fast, deterministic extraction
- Pattern-based entity recognition
- No API calls or costs
- Best for: URLs, emails, GitHub repos, common tech terms

### LLM Mode
- Intelligent extraction using AI
- Context-aware entity recognition
- Relationship extraction with evidence
- Best for: Natural language, relationships, disambiguation

### Hybrid Mode
- Runs both rule and LLM extraction
- Merges results with deduplication
- Best overall coverage
- Best for: Production use with quality requirements

## Performance & Costs

### Latency
- Rule extraction: ~3ms
- LLM extraction: 500-2000ms (depends on model and text length)
- Hybrid: Sum of both + merge time

### API Costs (approximate)
- Claude 3 Haiku: ~$0.25 per 1M input tokens
- Claude 3 Opus: ~$15 per 1M input tokens
- GPT-3.5 Turbo: ~$0.50 per 1M input tokens
- GPT-4: ~$10 per 1M input tokens

### Rate Limiting
Built-in rate limiters:
- Anthropic: 20 calls/minute
- OpenAI: 30 calls/minute

## Troubleshooting

### No LLM extraction happening
1. Check if API key is set: `echo $ANTHROPIC_API_KEY`
2. Check logs for errors: `tail -f logs/api.log`
3. Test with curl using `mode=llm` explicitly

### Poor quality extractions
1. Try a better model: `export LLM_MODEL="claude-3-opus-20240229"`
2. Increase min_confidence: `min_confidence=0.5`
3. Check text truncation if text > 10000 chars

### Rate limit errors
- The system automatically backs off
- Consider reducing concurrent requests
- Use hybrid mode instead of LLM-only

## Security Notes

- Never commit API keys to version control
- Use environment variables or secure key management
- API keys are never logged or stored in the database
- Consider using IAM roles in production

## Disabling LLM

To completely disable LLM extraction:
1. Don't set any API keys
2. Always use `mode=rule` in API calls
3. Set `LLM_EXTRACT_ON_CAPTURE=false`

The system gracefully degrades to rule-based extraction when no API keys are available.