"""
Log monitoring and alerting system for Prisma platform.
Provides real-time log analysis, alerting, and metrics collection.
"""

import time
import json
import threading
import queue
from typing import Dict, List, Any, Optional, Callable, Pattern
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re
import logging
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class LogPattern:
    """Log pattern for monitoring."""
    name: str
    pattern: str
    severity: str = "WARNING"
    threshold: int = 1
    time_window_minutes: int = 5
    enabled: bool = True
    compiled_pattern: Optional[Pattern] = field(default=None, init=False)
    
    def __post_init__(self):
        """Compile regex pattern after initialization."""
        self.compiled_pattern = re.compile(self.pattern, re.IGNORECASE)


@dataclass
class Alert:
    """Log alert."""
    id: str
    pattern_name: str
    message: str
    severity: str
    timestamp: datetime
    count: int
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class LogMetrics:
    """Log metrics for monitoring."""
    timestamp: datetime
    total_logs: int
    error_count: int
    warning_count: int
    critical_count: int
    unique_errors: int
    log_rate_per_minute: float
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class LogMonitor:
    """Real-time log monitoring and alerting system."""
    
    def __init__(self, 
                 log_file_path: str,
                 patterns: Optional[List[LogPattern]] = None,
                 alert_callback: Optional[Callable[[Alert], None]] = None,
                 metrics_interval: int = 60):
        """
        Initialize log monitor.
        
        Args:
            log_file_path: Path to the log file to monitor
            patterns: List of log patterns to monitor
            alert_callback: Callback function for alerts
            metrics_interval: Interval for collecting metrics in seconds
        """
        self.log_file_path = Path(log_file_path)
        self.patterns = patterns or []
        self.alert_callback = alert_callback
        self.metrics_interval = metrics_interval
        
        # Monitoring state
        self.running = False
        self.monitor_thread = None
        self.metrics_thread = None
        
        # Pattern matching state
        self.pattern_counts = defaultdict(lambda: defaultdict(int))
        self.pattern_timestamps = defaultdict(list)
        
        # Metrics
        self.metrics_history = deque(maxlen=100)
        self.current_metrics = LogMetrics(
            timestamp=datetime.now(),
            total_logs=0,
            error_count=0,
            warning_count=0,
            critical_count=0,
            unique_errors=0,
            log_rate_per_minute=0.0
        )
        
        # Alerts
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Log queue for processing
        self.log_queue = queue.Queue(maxsize=1000)
        
        # Setup logging
        self.logger = logging.getLogger('prisma.log_monitor')
    
    def add_pattern(self, pattern: LogPattern):
        """Add a log pattern to monitor."""
        self.patterns.append(pattern)
        self.logger.info(f"Added log pattern: {pattern.name}")
    
    def remove_pattern(self, pattern_name: str):
        """Remove a log pattern."""
        self.patterns = [p for p in self.patterns if p.name != pattern_name]
        self.logger.info(f"Removed log pattern: {pattern_name}")
    
    def start_monitoring(self):
        """Start log monitoring."""
        if self.running:
            self.logger.warning("Log monitoring is already running")
            return
        
        if not self.log_file_path.exists():
            self.logger.error(f"Log file does not exist: {self.log_file_path}")
            return
        
        self.running = True
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_logs, daemon=True)
        self.monitor_thread.start()
        
        # Start metrics thread
        self.metrics_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        self.metrics_thread.start()
        
        self.logger.info("Log monitoring started")
    
    def stop_monitoring(self):
        """Stop log monitoring."""
        if not self.running:
            return
        
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        
        self.logger.info("Log monitoring stopped")
    
    def _monitor_logs(self):
        """Monitor log file for new entries."""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Seek to end of file
                f.seek(0, 2)
                
                while self.running:
                    line = f.readline()
                    if line:
                        self._process_log_line(line.strip())
                    else:
                        time.sleep(0.1)  # Small delay when no new lines
        except Exception as e:
            self.logger.error(f"Error monitoring log file: {e}")
    
    def _process_log_line(self, line: str):
        """Process a single log line."""
        try:
            # Parse JSON log entry
            log_entry = json.loads(line)
            
            # Update metrics
            self._update_metrics(log_entry)
            
            # Check patterns
            self._check_patterns(log_entry)
            
        except json.JSONDecodeError:
            # Handle non-JSON log entries
            self._process_text_log_line(line)
        except Exception as e:
            self.logger.error(f"Error processing log line: {e}")
    
    def _process_text_log_line(self, line: str):
        """Process a text log line."""
        # Basic text log processing
        if 'ERROR' in line.upper():
            self.current_metrics.error_count += 1
        elif 'WARNING' in line.upper():
            self.current_metrics.warning_count += 1
        elif 'CRITICAL' in line.upper():
            self.current_metrics.critical_count += 1
        
        self.current_metrics.total_logs += 1
        
        # Check patterns against raw text
        for pattern in self.patterns:
            if pattern.enabled and pattern.compiled_pattern.search(line):
                self._trigger_pattern_match(pattern, line)
    
    def _update_metrics(self, log_entry: Dict[str, Any]):
        """Update metrics from log entry."""
        self.current_metrics.total_logs += 1
        
        level = log_entry.get('level', '').upper()
        if level == 'ERROR':
            self.current_metrics.error_count += 1
        elif level == 'WARNING':
            self.current_metrics.warning_count += 1
        elif level == 'CRITICAL':
            self.current_metrics.critical_count += 1
    
    def _check_patterns(self, log_entry: Dict[str, Any]):
        """Check log entry against patterns."""
        message = log_entry.get('message', '')
        
        for pattern in self.patterns:
            if not pattern.enabled:
                continue
            
            if pattern.compiled_pattern.search(message):
                self._trigger_pattern_match(pattern, log_entry)
    
    def _trigger_pattern_match(self, pattern: LogPattern, log_entry: Any):
        """Handle pattern match."""
        current_time = datetime.now()
        
        # Update pattern count
        self.pattern_counts[pattern.name]['total'] += 1
        
        # Clean old timestamps
        cutoff_time = current_time - timedelta(minutes=pattern.time_window_minutes)
        self.pattern_timestamps[pattern.name] = [
            ts for ts in self.pattern_timestamps[pattern.name] if ts > cutoff_time
        ]
        
        # Add current timestamp
        self.pattern_timestamps[pattern.name].append(current_time)
        
        # Check if threshold is exceeded
        recent_count = len(self.pattern_timestamps[pattern.name])
        
        if recent_count >= pattern.threshold:
            self._create_alert(pattern, recent_count, log_entry)
    
    def _create_alert(self, pattern: LogPattern, count: int, log_entry: Any):
        """Create an alert for pattern match."""
        alert_id = f"{pattern.name}_{int(time.time())}"
        
        # Check if similar alert already exists
        existing_alert = None
        for alert in self.active_alerts.values():
            if (alert.pattern_name == pattern.name and 
                not alert.resolved and
                (datetime.now() - alert.timestamp).seconds < 300):  # 5 minutes
                existing_alert = alert
                break
        
        if existing_alert:
            # Update existing alert
            existing_alert.count = count
            existing_alert.details['last_occurrence'] = datetime.now().isoformat()
        else:
            # Create new alert
            alert = Alert(
                id=alert_id,
                pattern_name=pattern.name,
                message=f"Pattern '{pattern.name}' matched {count} times in {pattern.time_window_minutes} minutes",
                severity=pattern.severity,
                timestamp=datetime.now(),
                count=count,
                details={
                    'pattern': pattern.pattern,
                    'threshold': pattern.threshold,
                    'time_window_minutes': pattern.time_window_minutes,
                    'sample_log_entry': str(log_entry)[:500]  # Truncate for storage
                }
            )
            
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Trigger callback
            if self.alert_callback:
                try:
                    self.alert_callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")
            
            self.logger.warning(f"Alert created: {alert.message}")
    
    def _collect_metrics(self):
        """Collect system and log metrics."""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Calculate log rate
                if len(self.metrics_history) > 0:
                    last_metrics = self.metrics_history[-1]
                    time_diff = (current_time - last_metrics.timestamp).total_seconds() / 60
                    if time_diff > 0:
                        log_diff = self.current_metrics.total_logs - last_metrics.total_logs
                        self.current_metrics.log_rate_per_minute = log_diff / time_diff
                
                # Collect system metrics
                if PSUTIL_AVAILABLE:
                    process = psutil.Process()
                    self.current_metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                    self.current_metrics.cpu_usage_percent = process.cpu_percent()
                
                # Store metrics
                metrics_copy = LogMetrics(
                    timestamp=self.current_metrics.timestamp,
                    total_logs=self.current_metrics.total_logs,
                    error_count=self.current_metrics.error_count,
                    warning_count=self.current_metrics.warning_count,
                    critical_count=self.current_metrics.critical_count,
                    unique_errors=self.current_metrics.unique_errors,
                    log_rate_per_minute=self.current_metrics.log_rate_per_minute,
                    memory_usage_mb=self.current_metrics.memory_usage_mb,
                    cpu_usage_percent=self.current_metrics.cpu_usage_percent
                )
                
                self.metrics_history.append(metrics_copy)
                self.current_metrics.timestamp = current_time
                
                time.sleep(self.metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")
                time.sleep(self.metrics_interval)
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts."""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.logger.info(f"Alert acknowledged: {alert_id}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if not self.metrics_history:
            return {}
        
        latest_metrics = self.metrics_history[-1]
        
        return {
            'timestamp': latest_metrics.timestamp.isoformat(),
            'total_logs': latest_metrics.total_logs,
            'error_count': latest_metrics.error_count,
            'warning_count': latest_metrics.warning_count,
            'critical_count': latest_metrics.critical_count,
            'log_rate_per_minute': latest_metrics.log_rate_per_minute,
            'memory_usage_mb': latest_metrics.memory_usage_mb,
            'cpu_usage_percent': latest_metrics.cpu_usage_percent,
            'active_alerts': len(self.get_active_alerts()),
            'pattern_matches': dict(self.pattern_counts)
        }


class LogAnalyzer:
    """Log analysis utilities."""
    
    @staticmethod
    def analyze_log_file(log_file_path: str, 
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Analyze log file for patterns and statistics."""
        log_file = Path(log_file_path)
        if not log_file.exists():
            return {'error': 'Log file does not exist'}
        
        stats = {
            'total_lines': 0,
            'error_count': 0,
            'warning_count': 0,
            'critical_count': 0,
            'unique_errors': set(),
            'hourly_distribution': defaultdict(int),
            'top_errors': defaultdict(int),
            'processing_time': 0
        }
        
        start_analysis = time.time()
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stats['total_lines'] += 1
                    
                    try:
                        log_entry = json.loads(line)
                        
                        # Check timestamp filter
                        if start_time or end_time:
                            timestamp_str = log_entry.get('timestamp', '')
                            if timestamp_str:
                                try:
                                    log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    if start_time and log_time < start_time:
                                        continue
                                    if end_time and log_time > end_time:
                                        continue
                                except ValueError:
                                    pass
                        
                        # Analyze log level
                        level = log_entry.get('level', '').upper()
                        if level == 'ERROR':
                            stats['error_count'] += 1
                            error_msg = log_entry.get('message', '')
                            stats['unique_errors'].add(error_msg)
                            stats['top_errors'][error_msg] += 1
                        elif level == 'WARNING':
                            stats['warning_count'] += 1
                        elif level == 'CRITICAL':
                            stats['critical_count'] += 1
                        
                        # Hourly distribution
                        timestamp_str = log_entry.get('timestamp', '')
                        if timestamp_str:
                            try:
                                log_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                hour_key = log_time.strftime('%Y-%m-%d %H:00')
                                stats['hourly_distribution'][hour_key] += 1
                            except ValueError:
                                pass
                    
                    except json.JSONDecodeError:
                        # Handle non-JSON lines
                        if 'ERROR' in line.upper():
                            stats['error_count'] += 1
                        elif 'WARNING' in line.upper():
                            stats['warning_count'] += 1
                        elif 'CRITICAL' in line.upper():
                            stats['critical_count'] += 1
        
        except Exception as e:
            return {'error': f'Error analyzing log file: {e}'}
        
        # Convert sets to counts and sort top errors
        stats['unique_error_count'] = len(stats['unique_errors'])
        stats['unique_errors'] = list(stats['unique_errors'])[:10]  # Top 10 unique errors
        stats['top_errors'] = dict(sorted(stats['top_errors'].items(), 
                                        key=lambda x: x[1], reverse=True)[:10])
        stats['hourly_distribution'] = dict(stats['hourly_distribution'])
        stats['processing_time'] = time.time() - start_analysis
        
        return stats


# Default patterns for common issues
DEFAULT_PATTERNS = [
    LogPattern(
        name="high_error_rate",
        pattern=r'"level":\s*"ERROR"',
        severity="CRITICAL",
        threshold=10,
        time_window_minutes=5
    ),
    LogPattern(
        name="database_connection_errors",
        pattern=r'database.*connection.*error|connection.*refused|timeout.*database',
        severity="ERROR",
        threshold=3,
        time_window_minutes=5
    ),
    LogPattern(
        name="memory_leak",
        pattern=r'memory.*leak|out of memory|memory.*exceeded',
        severity="CRITICAL",
        threshold=1,
        time_window_minutes=1
    ),
    LogPattern(
        name="authentication_failures",
        pattern=r'authentication.*failed|invalid.*credentials|unauthorized',
        severity="WARNING",
        threshold=5,
        time_window_minutes=10
    ),
    LogPattern(
        name="api_rate_limiting",
        pattern=r'rate.*limit|too many requests|429',
        severity="WARNING",
        threshold=3,
        time_window_minutes=5
    )
]


def create_default_monitor(log_file_path: str, 
                          alert_callback: Optional[Callable[[Alert], None]] = None) -> LogMonitor:
    """Create a log monitor with default patterns."""
    monitor = LogMonitor(log_file_path, DEFAULT_PATTERNS, alert_callback)
    return monitor
