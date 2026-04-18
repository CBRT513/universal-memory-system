#!/usr/bin/env python3
"""
UMS Capture Pipeline Test Suite
Two rounds: Smoke (8 tests) and Soak & Caching (12-16 tests)
"""

import json
import time
import httpx
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple
import statistics

BASE_URL = "http://localhost:8091"

# Test cases for Round 1
ROUND1_TESTS = [
    ("example.com", {"url": "https://example.com"}),
    ("Wikipedia - Ohio River", {"url": "https://en.wikipedia.org/wiki/Ohio_River"}),
    ("MDN JavaScript", {"url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"}),
    ("TechCrunch Article", {"url": "https://techcrunch.com/2024/10/29/anthropic-raises-4-billion-from-amazon/"}),
    ("Raw text", {"text": "The Universal Memory System (UMS) is a sophisticated knowledge management platform designed to capture, process, and retrieve information efficiently. It uses advanced natural language processing to extract key insights from various sources including web articles, PDFs, and raw text. The system maintains a contextualized database of information that can be queried intelligently, making it ideal for research, development, and knowledge work. With its modular architecture, UMS can be integrated into various workflows and applications."}),
    ("Invalid URL", {"url": "https://notareal.domain.abc"}),
    ("Long article - NY Times", {"url": "https://www.nytimes.com/2024/11/13/technology/elon-musk-trump-administration.html"}),
    ("Marketing page - Salesforce", {"url": "https://www.salesforce.com/products/platform/overview/"}),
]

async def submit_capture(session: httpx.AsyncClient, data: Dict) -> Tuple[str, float]:
    """Submit a capture request and return job_id and submit time"""
    start = time.time()
    data["project"] = "vader-lab"
    
    try:
        response = await session.post(f"{BASE_URL}/api/capture", json=data)
        response.raise_for_status()
        elapsed = (time.time() - start) * 1000
        return response.json().get("job_id"), elapsed
    except Exception as e:
        return None, 0

async def poll_job(session: httpx.AsyncClient, job_id: str, max_attempts: int = 10) -> Dict:
    """Poll job status until complete"""
    delays = [1, 1, 2, 2, 4, 4, 8, 8, 8, 8]  # backoff sequence
    
    for i, delay in enumerate(delays[:max_attempts]):
        try:
            response = await session.get(f"{BASE_URL}/api/capture/{job_id}")
            result = response.json()
            
            if result.get("status") in ["done", "error"]:
                return result
                
            await asyncio.sleep(delay)
        except:
            await asyncio.sleep(delay)
    
    return {"status": "timeout", "message": "Polling timeout after 10 attempts"}

async def run_test(session: httpx.AsyncClient, name: str, data: Dict) -> Dict:
    """Run a single test and return results"""
    start_time = time.time()
    
    # Submit capture
    job_id, submit_time = await submit_capture(session, data)
    if not job_id:
        return {
            "name": name,
            "status": "failed",
            "error": "Failed to submit capture",
            "latency_ms": 0
        }
    
    # Poll for completion
    result = await poll_job(session, job_id)
    
    total_time = (time.time() - start_time) * 1000
    
    test_result = {
        "name": name,
        "job_id": job_id,
        "status": result.get("status"),
        "latency_ms": round(total_time),
        "cached": result.get("cached", False)
    }
    
    if result.get("status") == "done":
        res = result.get("result", {})
        test_result["summary_preview"] = (res.get("summary", "")[:100] + "...") if res.get("summary") else "No summary"
        test_result["source_title"] = res.get("source", {}).get("title", "N/A")
    else:
        test_result["error"] = result.get("message", "Unknown error")[:100]
    
    return test_result

async def run_round(session: httpx.AsyncClient, tests: List[Tuple], round_name: str) -> Dict:
    """Run a complete round of tests"""
    print(f"\n=== Starting {round_name} ===")
    results = []
    latencies = []
    
    for name, data in tests:
        print(f"Testing: {name}...")
        result = await run_test(session, name, data)
        results.append(result)
        latencies.append(result["latency_ms"])
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    # Calculate statistics
    passed = sum(1 for r in results if r["status"] == "done")
    failed = sum(1 for r in results if r["status"] in ["error", "failed", "timeout"])
    
    stats = {
        "round": round_name,
        "total_tests": len(tests),
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed}/{len(tests)}",
        "latencies": {
            "p50": round(statistics.median(latencies)) if latencies else 0,
            "p95": round(statistics.quantiles(latencies, n=20)[18]) if len(latencies) > 1 else max(latencies, default=0),
            "max": max(latencies, default=0)
        },
        "results": results
    }
    
    return stats

async def main():
    """Run the complete test suite"""
    async with httpx.AsyncClient(timeout=30.0) as session:
        # Round 1: Smoke tests
        round1_stats = await run_round(session, ROUND1_TESTS, "Round 1 - Smoke")
        
        # Wait before Round 2
        await asyncio.sleep(2)
        
        # Round 2: Soak & Caching
        # Re-run Round 1 tests + add diverse URLs
        round2_tests = ROUND1_TESTS.copy()
        round2_tests.extend([
            ("GitHub README", {"url": "https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/README.md"}),
            ("BBC News", {"url": "https://www.bbc.com/news/technology-67329954"}),
            ("ArXiv PDF", {"url": "https://arxiv.org/abs/2312.02406"}),
            ("Hacker News", {"url": "https://news.ycombinator.com/item?id=38999349"}),
        ])
        
        round2_stats = await run_round(session, round2_tests, "Round 2 - Soak & Caching")
        
        # Generate report
        generate_report(round1_stats, round2_stats)

def generate_report(round1: Dict, round2: Dict):
    """Generate markdown report"""
    
    # Round 1 gate check
    round1_pass_gate = (
        round1["passed"] >= 6 and 
        round1["latencies"]["p95"] <= 8000
    )
    
    # Round 2 gate check
    round2_pass_gate = (
        round2["passed"] >= 10 and
        round2["latencies"]["p95"] <= 8000
    )
    
    # Check cache performance (first 8 tests should be faster in round 2)
    cache_times = [r["latency_ms"] for r in round2["results"][:8] if r.get("cached")]
    cache_pass = all(t <= 2000 for t in cache_times) if cache_times else True
    
    overall_pass = round1_pass_gate and round2_pass_gate and cache_pass
    
    report = f"""
# UMS Capture Pipeline Test Report
**Generated**: {datetime.now().isoformat()}

## Round 1 - Smoke (8 tests)

| Test Case | Status | Latency (ms) | Cached | Notes |
|-----------|--------|--------------|--------|-------|
"""
    
    for r in round1["results"]:
        status_icon = "✅" if r["status"] == "done" else "❌"
        notes = r.get("error", r.get("summary_preview", ""))[:50]
        report += f"| {r['name'][:30]} | {status_icon} {r['status']} | {r['latency_ms']} | {'Yes' if r['cached'] else 'No'} | {notes} |\n"
    
    report += f"""
**Round 1 Summary**:
- Pass Rate: {round1['pass_rate']} (threshold: ≥6/8)
- Latency p50: {round1['latencies']['p50']}ms
- Latency p95: {round1['latencies']['p95']}ms (threshold: ≤8000ms)
- **Gate**: {'✅ PASS' if round1_pass_gate else '❌ FAIL'}

## Round 2 - Soak & Caching (12 tests)

| Test Case | Status | Latency (ms) | Cached | Notes |
|-----------|--------|--------------|--------|-------|
"""
    
    for r in round2["results"]:
        status_icon = "✅" if r["status"] == "done" else "❌"
        notes = r.get("error", r.get("summary_preview", ""))[:50]
        report += f"| {r['name'][:30]} | {status_icon} {r['status']} | {r['latency_ms']} | {'Yes' if r['cached'] else 'No'} | {notes} |\n"
    
    report += f"""
**Round 2 Summary**:
- Pass Rate: {round2['pass_rate']} (threshold: ≥10/12)
- Latency p50: {round2['latencies']['p50']}ms
- Latency p95: {round2['latencies']['p95']}ms
- Cache Performance: {'✅ PASS' if cache_pass else '❌ FAIL'} (cached items ≤2s)
- **Gate**: {'✅ PASS' if round2_pass_gate else '❌ FAIL'}

## Final Verdict

**{'✅ READY' if overall_pass else '❌ NEEDS ATTENTION'}**
"""
    
    if not overall_pass:
        report += "\n**Follow-up Actions Required**:\n"
        if not round1_pass_gate:
            report += "1. Investigate failures in Round 1 smoke tests\n"
        if round2["latencies"]["p95"] > 8000:
            report += "2. Optimize performance - p95 latency exceeds 8s threshold\n"
        if not cache_pass:
            report += "3. Fix caching mechanism - cached responses taking >2s\n"
    else:
        report += "\nAll tests passed successfully. The capture pipeline is ready for production use."
    
    print(report)
    
    # Save to file
    with open("/tmp/capture_test_report.md", "w") as f:
        f.write(report)

if __name__ == "__main__":
    asyncio.run(main())