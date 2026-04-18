# PROJECT BACKLOG
**Last Updated**: August 19, 2025  
**Purpose**: Track all unresolved issues, TODOs, and future enhancements

## Priority Levels
- **P0 (Critical)**: Blocks core functionality or causes data loss
- **P1 (High)**: Important for user experience or performance
- **P2 (Medium)**: Nice to have, improves quality
- **P3 (Low)**: Future considerations

---

## 🔴 P0 - Critical Issues

### Issue #001: Extension Integration Not Implemented
**Component**: VADER Frontend  
**Description**: "Capture via Browser" button is placeholder only  
**Impact**: Users cannot capture from paywalled/bot-protected sites  
**Proposed Solution**: 
- Build Chrome/Firefox extension with content script
- Add extension detection in frontend
- Implement POST of DOM content to `/api/capture`
**Milestone**: B

---

## 🟠 P1 - High Priority

### Issue #002: No Retry Logic for Transient Failures
**Component**: UMS Backend  
**Description**: Network timeouts fail immediately without retry  
**Impact**: Reduces capture success rate  
**Proposed Solution**:
- Implement exponential backoff
- Add configurable retry limits
- Track retry attempts in metrics
**Milestone**: B

### Issue #003: PDF Text Extraction Quality
**Component**: Capture Service  
**Description**: ArXiv PDFs extract but formatting is poor  
**Impact**: Summaries may miss key information  
**Proposed Solution**:
- Add dedicated PDF parser (PyPDF2 or pdfplumber)
- Preserve section headers and structure
- Handle multi-column layouts
**Milestone**: C

### Issue #004: No User Authentication
**Component**: System-wide  
**Description**: System assumes single local user  
**Impact**: Cannot deploy to shared environments  
**Proposed Solution**:
- Add optional auth layer
- Implement user workspaces
- Separate data by user
**Milestone**: E

### Issue #005: Missing Capture Analytics Dashboard
**Component**: VADER Frontend  
**Description**: No visibility into capture success rates over time  
**Impact**: Cannot identify trending issues  
**Proposed Solution**:
- Add `/api/capture/stats` endpoint
- Build analytics component
- Show daily/weekly trends
**Milestone**: B

---

## 🟡 P2 - Medium Priority

### Issue #006: Hardcoded User-Agent String
**Component**: Capture Service  
**Description**: Single UA string may trigger bot detection  
**Impact**: Some sites block after repeated requests  
**Proposed Solution**:
```python
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    # ... more variants
]
ua = random.choice(USER_AGENTS)
```
**Milestone**: B

### Issue #007: No Content Deduplication Across Projects
**Component**: Database  
**Description**: Same URL captured in different projects stores duplicate content  
**Impact**: Wasted storage space  
**Proposed Solution**:
- Separate content and metadata tables
- Link captures to shared content
- Update dedup logic
**Milestone**: C

### Issue #008: SSE Fallback Not Automatic
**Component**: Frontend Hook  
**Description**: SSE failure requires page reload to trigger polling  
**Impact**: Poor UX when SSE fails  
**Proposed Solution**:
- Detect SSE failure immediately
- Auto-switch to polling
- Retry SSE periodically
**Milestone**: B

### Issue #009: No Export Functionality
**Component**: System-wide  
**Description**: Cannot export captures to Markdown/JSON  
**Impact**: Data locked in system  
**Proposed Solution**:
- Add export endpoints
- Support multiple formats
- Include bulk export
**Milestone**: C

### Issue #010: Limited Error Recovery Information
**Component**: UI  
**Description**: Error messages don't suggest specific fixes  
**Impact**: Users don't know how to resolve issues  
**Proposed Solution**:
- Add help text for each error cause
- Link to troubleshooting docs
- Suggest alternative capture methods
**Milestone**: B

---

## 🟢 P3 - Low Priority

### Issue #011: No Dark/Light Theme Toggle
**Component**: VADER Frontend  
**Description**: Dark theme is hardcoded  
**Impact**: User preference not respected  
**Proposed Solution**:
- Add theme context
- Store preference in localStorage
- Update Tailwind classes
**Milestone**: D

### Issue #012: No Keyboard Shortcuts
**Component**: VADER Frontend  
**Description**: All actions require mouse  
**Impact**: Slower for power users  
**Proposed Solution**:
- Add shortcuts for capture (Cmd+K)
- Navigation shortcuts
- Help modal with shortcuts list
**Milestone**: D

### Issue #013: No Capture History Search
**Component**: Frontend/Backend  
**Description**: Cannot search previous captures  
**Impact**: Hard to find old content  
**Proposed Solution**:
- Add search endpoint
- Full-text search in SQLite
- Filter by date/project/domain
**Milestone**: C

### Issue #014: No Favicon Extraction
**Component**: Capture Service  
**Description**: Source sites shown without icons  
**Impact**: Less visual distinction  
**Proposed Solution**:
- Extract favicon URL from HTML
- Store as base64 or URL
- Display in SummaryCard
**Milestone**: D

### Issue #015: No Mobile Responsive Design
**Component**: VADER Frontend  
**Description**: UI not optimized for mobile  
**Impact**: Cannot use on phones/tablets  
**Proposed Solution**:
- Update Tailwind breakpoints
- Responsive grid layouts
- Touch-friendly buttons
**Milestone**: E

---

## 📋 Technical Debt

### TD001: Python Type Hints Missing
**Files**: All Python files  
**Impact**: Harder to maintain, no IDE support  
**Solution**: Add type hints throughout  
**Effort**: 4 hours

### TD002: No Integration Tests
**Component**: API layer  
**Impact**: Breaking changes not caught  
**Solution**: Add pytest integration suite  
**Effort**: 8 hours

### TD003: Frontend Component Tests Missing
**Component**: React components  
**Impact**: UI regressions possible  
**Solution**: Add React Testing Library tests  
**Effort**: 6 hours

### TD004: No API Documentation
**Component**: FastAPI endpoints  
**Impact**: Hard for new developers  
**Solution**: Generate OpenAPI docs  
**Effort**: 2 hours

### TD005: Inconsistent Error Handling
**Component**: Throughout codebase  
**Impact**: Unpredictable failure modes  
**Solution**: Standardize error classes  
**Effort**: 4 hours

---

## 💡 Feature Ideas (Unscoped)

### Content Enhancement
- Auto-tagging with topics/categories
- Related article suggestions
- Reading time estimates
- Highlight extraction
- Comment/annotation system

### Integration Features
- Obsidian plugin
- Notion sync
- Readwise export
- RSS feed import
- Email newsletter capture

### AI Features
- Smart summarization with GPT/Claude
- Question answering on captured content
- Content clustering
- Trend detection
- Reading recommendations

### Performance Optimizations
- Background job priority queue
- Capture request batching
- CDN for static assets
- Database query optimization
- Caching layer (Redis)

---

## 🔧 Infrastructure Improvements

### Monitoring & Observability
- Structured logging
- Metrics collection (Prometheus)
- Error tracking (Sentry)
- Performance monitoring
- Uptime monitoring

### Development Experience
- Docker containerization
- One-command setup script
- Seed data for testing
- Development/production configs
- CI/CD pipeline

### Security Enhancements
- Input sanitization
- Rate limiting
- CORS configuration
- SQL injection prevention
- XSS protection

---

## 📊 Backlog Statistics

### By Priority
- P0 (Critical): 1 issue
- P1 (High): 5 issues
- P2 (Medium): 5 issues
- P3 (Low): 5 issues
- Technical Debt: 5 items
- Feature Ideas: 15+ items

### By Component
- Backend: 8 issues
- Frontend: 7 issues
- System-wide: 3 issues
- Database: 2 issues

### By Milestone
- Milestone B: 7 issues
- Milestone C: 5 issues
- Milestone D: 3 issues
- Milestone E: 2 issues
- Unassigned: 8+ items

---

## 🎯 Next Actions

### Immediate (This Week)
1. Complete Milestone B UI enhancements
2. Implement browser extension MVP
3. Add capture metrics endpoint

### Short Term (This Month)
1. Add retry logic for failures
2. Implement UA rotation
3. Build analytics dashboard

### Long Term (This Quarter)
1. Design knowledge graph schema
2. Plan multi-user architecture
3. Evaluate AI integration options

---

*This backlog is reviewed weekly and updated after each milestone completion.*