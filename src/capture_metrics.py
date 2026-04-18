#!/usr/bin/env python3
"""
Capture Metrics Service - Milestone B2
Provides analytics and statistics for capture operations
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CaptureMetricsService:
    """Service for capture metrics and analytics"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "memories.db"
        self.db_path = str(db_path)
    
    def get_stats(self, 
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 project: Optional[str] = None) -> Dict[str, Any]:
        """
        Get capture statistics for a given time range
        
        Args:
            start_date: ISO format date string (defaults to 7 days ago)
            end_date: ISO format date string (defaults to now)
            project: Filter by project name
        
        Returns:
            Dictionary with comprehensive capture statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Default to last 7 days
            if not end_date:
                end_date = datetime.now().isoformat()
            if not start_date:
                start_date = (datetime.now() - timedelta(days=7)).isoformat()
            
            # Build query with optional project filter
            project_filter = ""
            params = [start_date, end_date]
            if project:
                project_filter = "AND project = ?"
                params.append(project)
            
            # Get overall counts
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN cause = 'ok' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END) as cached_hits,
                    SUM(CASE WHEN cause != 'ok' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN cause = 'blocked' THEN 1 ELSE 0 END) as blocked,
                    SUM(CASE WHEN cause = 'not_found' THEN 1 ELSE 0 END) as not_found,
                    SUM(CASE WHEN cause = 'server_error' THEN 1 ELSE 0 END) as server_errors,
                    SUM(CASE WHEN cause = 'timeout' THEN 1 ELSE 0 END) as timeouts,
                    SUM(CASE WHEN cause = 'invalid' THEN 1 ELSE 0 END) as invalid_urls
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ? {project_filter}
            """, params)
            
            counts = dict(cursor.fetchone())
            
            # Calculate success rate
            if counts['total_attempts'] > 0:
                counts['success_rate'] = round(
                    (counts['successful'] / counts['total_attempts']) * 100, 2
                )
                counts['cache_hit_rate'] = round(
                    (counts['cached_hits'] / counts['total_attempts']) * 100, 2
                )
            else:
                counts['success_rate'] = 0
                counts['cache_hit_rate'] = 0
            
            # Get performance metrics (excluding cached hits)
            cursor.execute(f"""
                SELECT 
                    AVG(fetch_time_ms) as avg_fetch_ms,
                    AVG(total_time_ms) as avg_total_ms,
                    MAX(fetch_time_ms) as max_fetch_ms,
                    MAX(total_time_ms) as max_total_ms
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ? 
                    AND cached = 0 
                    AND cause = 'ok'
                    {project_filter}
            """, params)
            
            perf = dict(cursor.fetchone())
            
            # Get percentiles (poor man's percentile without window functions)
            cursor.execute(f"""
                SELECT fetch_time_ms, total_time_ms
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ? 
                    AND cached = 0 
                    AND cause = 'ok'
                    {project_filter}
                ORDER BY fetch_time_ms
            """, params)
            
            fetch_times = []
            total_times = []
            for row in cursor.fetchall():
                if row['fetch_time_ms'] is not None:
                    fetch_times.append(row['fetch_time_ms'])
                if row['total_time_ms'] is not None:
                    total_times.append(row['total_time_ms'])
            
            percentiles = {}
            if fetch_times:
                fetch_times.sort()
                total_times.sort()
                
                def get_percentile(arr, p):
                    idx = int(len(arr) * p / 100)
                    return arr[min(idx, len(arr)-1)]
                
                percentiles = {
                    'p50_fetch_ms': get_percentile(fetch_times, 50),
                    'p95_fetch_ms': get_percentile(fetch_times, 95),
                    'p99_fetch_ms': get_percentile(fetch_times, 99),
                    'p50_total_ms': get_percentile(total_times, 50),
                    'p95_total_ms': get_percentile(total_times, 95),
                    'p99_total_ms': get_percentile(total_times, 99)
                }
            
            # Get top domains
            cursor.execute(f"""
                SELECT 
                    domain,
                    COUNT(*) as count,
                    SUM(CASE WHEN cause = 'ok' THEN 1 ELSE 0 END) as successful
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ? 
                    AND domain IS NOT NULL
                    {project_filter}
                GROUP BY domain
                ORDER BY count DESC
                LIMIT 10
            """, params)
            
            top_domains = []
            for row in cursor.fetchall():
                domain_stats = dict(row)
                if domain_stats['count'] > 0:
                    domain_stats['success_rate'] = round(
                        (domain_stats['successful'] / domain_stats['count']) * 100, 2
                    )
                top_domains.append(domain_stats)
            
            # Get failure breakdown by domain
            cursor.execute(f"""
                SELECT 
                    domain,
                    cause,
                    COUNT(*) as count
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ? 
                    AND cause != 'ok'
                    AND domain IS NOT NULL
                    {project_filter}
                GROUP BY domain, cause
                ORDER BY count DESC
                LIMIT 20
            """, params)
            
            failure_breakdown = [dict(row) for row in cursor.fetchall()]
            
            # Get extraction method usage
            cursor.execute(f"""
                SELECT 
                    extraction_method,
                    COUNT(*) as count
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ? 
                    AND extraction_method IS NOT NULL
                    {project_filter}
                GROUP BY extraction_method
                ORDER BY count DESC
            """, params)
            
            extraction_methods = [dict(row) for row in cursor.fetchall()]
            
            # Get time series data (hourly for last 24h, daily for older)
            recent_cutoff = (datetime.now() - timedelta(days=1)).isoformat()
            
            # Hourly for recent data
            cursor.execute(f"""
                SELECT 
                    strftime('%Y-%m-%d %H:00', timestamp) as hour,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN cause = 'ok' THEN 1 ELSE 0 END) as successful
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ?
                    AND timestamp >= ?
                    {project_filter}
                GROUP BY hour
                ORDER BY hour
            """, params + [recent_cutoff])
            
            hourly_series = []
            for row in cursor.fetchall():
                data = dict(row)
                if data['attempts'] > 0:
                    data['success_rate'] = round(
                        (data['successful'] / data['attempts']) * 100, 2
                    )
                hourly_series.append(data)
            
            # Daily for older data
            cursor.execute(f"""
                SELECT 
                    date(timestamp) as day,
                    COUNT(*) as attempts,
                    SUM(CASE WHEN cause = 'ok' THEN 1 ELSE 0 END) as successful
                FROM capture_events
                WHERE timestamp >= ? AND timestamp <= ?
                    AND timestamp < ?
                    {project_filter}
                GROUP BY day
                ORDER BY day
            """, params + [recent_cutoff])
            
            daily_series = []
            for row in cursor.fetchall():
                data = dict(row)
                if data['attempts'] > 0:
                    data['success_rate'] = round(
                        (data['successful'] / data['attempts']) * 100, 2
                    )
                daily_series.append(data)
            
            # Compile final stats
            return {
                'period': {
                    'start': start_date,
                    'end': end_date,
                    'project': project
                },
                'summary': counts,
                'performance': {
                    **perf,
                    **percentiles
                },
                'top_domains': top_domains,
                'failure_breakdown': failure_breakdown,
                'extraction_methods': extraction_methods,
                'time_series': {
                    'hourly': hourly_series,
                    'daily': daily_series
                }
            }
            
        finally:
            conn.close()
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time stats for the last hour"""
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        return self.get_stats(start_date=one_hour_ago)
    
    def aggregate_metrics(self):
        """
        Aggregate raw events into metrics table for faster queries
        This should be run periodically (e.g., every hour)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get the last aggregation time
            cursor.execute("""
                SELECT MAX(timestamp) FROM capture_metrics
            """)
            last_agg = cursor.fetchone()[0]
            
            if last_agg:
                start_time = datetime.fromisoformat(last_agg)
            else:
                # Start from the beginning of capture_events
                cursor.execute("SELECT MIN(timestamp) FROM capture_events")
                min_time = cursor.fetchone()[0]
                if min_time:
                    start_time = datetime.fromisoformat(min_time)
                else:
                    return  # No events to aggregate
            
            # Aggregate by hour
            cursor.execute("""
                INSERT OR REPLACE INTO capture_metrics (
                    date, hour, total_attempts, successful_captures, cached_hits,
                    failed_captures, blocked_count, not_found_count, server_error_count,
                    timeout_count, invalid_url_count, avg_fetch_time_ms, avg_total_time_ms
                )
                SELECT 
                    date(timestamp) as date,
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN cause = 'ok' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cached = 1 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cause != 'ok' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cause = 'blocked' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cause = 'not_found' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cause = 'server_error' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cause = 'timeout' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN cause = 'invalid' THEN 1 ELSE 0 END),
                    AVG(fetch_time_ms),
                    AVG(total_time_ms)
                FROM capture_events
                WHERE timestamp >= ?
                GROUP BY date, hour
            """, (start_time.isoformat(),))
            
            conn.commit()
            logger.info(f"Aggregated metrics from {start_time}")
            
        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
        finally:
            conn.close()

# Singleton instance
_metrics_service = None

def get_metrics_service() -> CaptureMetricsService:
    """Get or create the metrics service singleton"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = CaptureMetricsService()
    return _metrics_service