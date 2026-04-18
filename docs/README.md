# UMS/VADER Documentation

## Quick Start

If you're new to the project, read these in order:
1. [MILESTONE_0_FOUNDATIONS.md](milestones/MILESTONE_0_FOUNDATIONS.md) - Complete project history
2. [PROJECT_CONTINUITY_PLAN.md](PROJECT_CONTINUITY_PLAN.md) - How we work
3. [PROJECT_BACKLOG.md](PROJECT_BACKLOG.md) - What needs doing

## Project Overview

The Universal Memory System (UMS) with VADER frontend is a local-first article capture and knowledge management system. It captures web content, extracts key information, and builds a searchable knowledge base.

### Current Status
- **Milestone A**: ✅ COMPLETE - Core capture pipeline
- **Milestone B**: 🚧 IN PROGRESS - Enhanced capture & UI  
- **Milestone C**: 📋 PLANNED - Knowledge graph
- **Milestone D**: 📋 PLANNED - AI integration
- **Milestone E**: 📋 PLANNED - Collaboration

### Key Metrics (as of Aug 19, 2025)
- Capture success rate: 66%
- Performance p95: 2.5s
- Cache hits: 6ms
- Error classification: 100%
- Total captures: 548

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐
│  VADER Frontend │────▶│  UMS Backend API │
│  (React/Vite)   │◀────│  (FastAPI)       │
└─────────────────┘     └──────────────────┘
                               │
                        ┌──────▼───────┐
                        │   SQLite DB  │
                        │  (memories)  │
                        └──────────────┘
```

### Components
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8091
- **Database**: /usr/local/share/universal-memory-system/memories.db

## Development

### Prerequisites
- Python 3.13+ (Homebrew recommended)
- Node.js 18+
- SQLite3

### Quick Setup
```bash
# Backend
cd /usr/local/share/universal-memory-system
source venv/bin/activate
uvicorn src.api_service:app --host 127.0.0.1 --port 8091 --reload

# Frontend
cd /Users/cerion/Projects/vader-rnd-lab
npm install
npm run dev
```

### Running Tests
```bash
cd /usr/local/share/universal-memory-system
python tests/capture_test_suite.py
```

## API Endpoints

### Core Endpoints
- `POST /api/capture` - Submit URL or text for capture
- `GET /api/capture/{job_id}` - Check job status
- `GET /api/capture/{job_id}/stream` - SSE updates
- `GET /api/health` - System health check

### Request Example
```bash
curl -X POST http://localhost:8091/api/capture \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com", "project": "test"}'
```

### Response Example
```json
{
  "status": "done",
  "cached": false,
  "cause": "ok",
  "http_status": 200,
  "timings": {
    "fetch_ms": 1000,
    "total_ms": 1500
  },
  "result": {
    "id": "cap_20250819_abc123",
    "summary": "Article summary...",
    "source": {
      "url": "https://example.com",
      "title": "Example Article"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Port 8091 already in use**
   ```bash
   sudo lsof -i :8091
   sudo kill -9 [PID]
   ```

2. **LaunchDaemon interference**
   ```bash
   sudo launchctl unload /Library/LaunchDaemons/com.universal-memory-system.plist
   ```

3. **Python import errors**
   - Ensure using venv Python, not system Python
   - Rebuild venv if needed

4. **Tailwind CSS issues**
   - We use CDN, not build process
   - Check index.html has CDN link

## Contributing

1. Read [PROJECT_CONTINUITY_PLAN.md](PROJECT_CONTINUITY_PLAN.md)
2. Check [PROJECT_BACKLOG.md](PROJECT_BACKLOG.md) for tasks
3. Follow commit message format: `{type}: {description}`
4. Update relevant milestone docs
5. Run tests before submitting

## License

[Add license information]

## Contact

[Add contact information]

---
*For detailed project history and technical decisions, see [MILESTONE_0_FOUNDATIONS.md](milestones/MILESTONE_0_FOUNDATIONS.md)*