# 🔧 Capture Job Automation Playbook

## API Endpoints
- **Base URL**: `http://localhost:8091`
- **Fallback ports**: 8092, 8093 (if 8091 refuses connection)

## Automation Flow

### 1. Submit Capture Request
```bash
curl -X POST http://localhost:8091/api/capture \
  -H 'Content-Type: application/json' \
  -d '{"url": "...", "text": "...", "notes": "...", "project": "vader-lab"}'
```
- Record the returned `job_id`
- Either `url` or `text` is required (not both)

### 2. Poll for Status
```bash
curl -s http://localhost:8091/api/capture/{job_id}
```
- Poll until `status` is `"done"` or `"error"`
- Use backoff intervals: 1s → 2s → 5s → 10s
- Timeout after 60 seconds total

### 3. Handle Success (status = "done")
- Extract from response:
  - `result.id` - Capture ID
  - `result.summary` - Generated summary
  - `result.source` - Source metadata (url, domain, title, author)
  - `result.project` - Project association
- Save to project memory
- Mark job complete

### 4. Handle Failure (status = "error")
- Log the error message
- Retry once with exponential backoff
- If still failing after retry, check service health
- Only escalate if service is down for >60s

### 5. Service Health Check
```bash
curl -s http://localhost:8091/api/health
```
Expected response: `{"status": "healthy", ...}`

## Autonomy Rules
1. **Never ask user to run curl** - Execute directly
2. **Auto-retry on transient failures** - Network errors, timeouts
3. **Auto-fallback to alternate ports** - If 8091 refuses, try 8092, 8093
4. **Only escalate when truly broken** - Service unreachable >60s or repeated failures
5. **Handle duplicates gracefully** - API returns cached results for recent URLs

## Error Handling Matrix
| Error | Action | Escalate? |
|-------|--------|-----------|
| Connection refused | Try fallback ports | After all ports fail |
| 404 Not Found | URL doesn't exist - normal | No |
| 500 Server Error | Retry with backoff | After 3 retries |
| Timeout | Retry with longer timeout | After 60s total |
| "Readability" error | Check dependencies | Yes - code issue |

## Example Implementation
```python
async def capture_with_retry(url=None, text=None, notes=None, max_retries=3):
    ports = [8091, 8092, 8093]
    
    for port in ports:
        for attempt in range(max_retries):
            try:
                # Submit job
                response = await submit_capture(port, url, text, notes)
                job_id = response['job_id']
                
                # Poll for completion
                result = await poll_job_status(port, job_id)
                
                if result['status'] == 'done':
                    return result['result']
                    
            except ConnectionError:
                if port == ports[-1] and attempt == max_retries - 1:
                    raise  # Escalate only after all options exhausted
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
    raise Exception("All capture attempts failed")
```

## Testing Commands
```bash
# Test with URL
curl -X POST http://localhost:8091/api/capture \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/article"}'

# Test with raw text
curl -X POST http://localhost:8091/api/capture \
  -H 'Content-Type: application/json' \
  -d '{"text":"Article content here...", "notes":"Testing"}'

# Check job status
curl http://localhost:8091/api/capture/job_xxxxx

# Stream real-time updates (SSE)
curl -N http://localhost:8091/api/capture/job_xxxxx/stream
```

---
*This playbook enables fully autonomous capture operations without user intervention.*