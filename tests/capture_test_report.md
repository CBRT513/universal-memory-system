
# UMS Capture Pipeline Test Report
**Generated**: 2025-08-19T23:07:53.380684

## Round 1 - Smoke (8 tests)

| Test Case | Status | Latency (ms) | Cached | Notes |
|-----------|--------|--------------|--------|-------|
| example.com | ✅ done | 9 | Yes | Example Domain This domain is for use in illustrat |
| Wikipedia - Ohio River | ✅ done | 1146 | No | Major river in the midwestern United States Ohio R |
| MDN JavaScript | ✅ done | 1013 | No | Learn how to program in JavaScript from the ground |
| TechCrunch Article | ❌ error | 2021 | No | Error: Client error '404 Not Found' for url 'https |
| Raw text | ✅ done | 5 | No | The Universal Memory System (UMS) is a sophisticat |
| Invalid URL | ❌ error | 1016 | No | Error: [Errno 8] nodename nor servname provided, o |
| Long article - NY Times | ❌ error | 1015 | No | Error: Client error '403 Forbidden' for url 'https |
| Marketing page - Salesforce | ✅ done | 1018 | No | We surveyed over 4,000 IT leaders worldwide to unc |

**Round 1 Summary**:
- Pass Rate: 5/8 (threshold: ≥6/8)
- Latency p50: 1016ms
- Latency p95: 2502ms (threshold: ≤8000ms)
- **Gate**: ❌ FAIL

## Round 2 - Soak & Caching (12 tests)

| Test Case | Status | Latency (ms) | Cached | Notes |
|-----------|--------|--------------|--------|-------|
| example.com | ✅ done | 6 | Yes | Example Domain This domain is for use in illustrat |
| Wikipedia - Ohio River | ✅ done | 6 | Yes | Major river in the midwestern United States Ohio R |
| MDN JavaScript | ✅ done | 6 | Yes | Learn how to program in JavaScript from the ground |
| TechCrunch Article | ❌ error | 1016 | No | Error: Client error '404 Not Found' for url 'https |
| Raw text | ✅ done | 6 | No | The Universal Memory System (UMS) is a sophisticat |
| Invalid URL | ❌ error | 1018 | No | Error: [Errno 8] nodename nor servname provided, o |
| Long article - NY Times | ❌ error | 1015 | No | Error: Client error '403 Forbidden' for url 'https |
| Marketing page - Salesforce | ✅ done | 5 | Yes | We surveyed over 4,000 IT leaders worldwide to unc |
| GitHub README | ✅ done | 1018 | No | # Anthropic Python API library   [![PyPI version]( |
| BBC News | ❌ error | 1017 | No | Error: Server error '500 Internal Server Error' fo |
| ArXiv PDF | ✅ done | 1016 | No | [Submitted on 5 Dec 2023 ( v1 ), last revised 9 De |
| Hacker News | ✅ done | 1018 | No | Man I love this I'm off to build one now, but... O |

**Round 2 Summary**:
- Pass Rate: 8/12 (threshold: ≥10/12)
- Latency p50: 1016ms
- Latency p95: 1018ms
- Cache Performance: ✅ PASS (cached items ≤2s)
- **Gate**: ❌ FAIL

## Final Verdict

**❌ NEEDS ATTENTION**

**Follow-up Actions Required**:
1. Investigate failures in Round 1 smoke tests
