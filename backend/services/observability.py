import time
import json
import logging
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class JSONFormatter(logging.Formatter):
    """Formats log records as structured JSON for Datadog / CloudWatch / ELK."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

class MetricsTracker:
    """
    SaaS Observability & Performance Metrics Tracker:
    Tracks provider latencies, success/failure counts, job durations, and costs.
    """
    def __init__(self):
        # provider -> list of response times in seconds
        self.provider_latencies: Dict[str, List[float]] = defaultdict(list)
        # provider -> {"success": int, "failure": int}
        self.provider_calls: Dict[str, Dict[str, int]] = defaultdict(lambda: {"success": 0, "failure": 0})
        # mode -> list of job durations in seconds
        self.job_durations: Dict[str, List[float]] = defaultdict(list)
        self.total_cost_usd = 0.0

    def record_provider_call(self, provider: str, latency_sec: float, success: bool = True):
        self.provider_latencies[provider].append(round(latency_sec, 2))
        if len(self.provider_latencies[provider]) > 100:
            self.provider_latencies[provider].pop(0)
        
        status_key = "success" if success else "failure"
        self.provider_calls[provider][status_key] += 1

    def record_job_completion(self, visual_mode: str, duration_sec: float, cost: float = 0.0):
        self.job_durations[visual_mode].append(round(duration_sec, 1))
        if len(self.job_durations[visual_mode]) > 50:
            self.job_durations[visual_mode].pop(0)
        self.total_cost_usd += cost

    def get_summary(self) -> Dict[str, Any]:
        avg_latencies = {
            p: round(sum(lats) / len(lats), 2) if lats else 0.0
            for p, lats in self.provider_latencies.items()
        }
        failure_rates = {
            p: round((counts["failure"] / (counts["success"] + counts["failure"]) * 100), 1)
            if (counts["success"] + counts["failure"]) > 0 else 0.0
            for p, counts in self.provider_calls.items()
        }
        avg_job_durations = {
            m: round(sum(durs) / len(durs), 1) if durs else 0.0
            for m, durs in self.job_durations.items()
        }

        return {
            "average_provider_latency_sec": avg_latencies,
            "provider_failure_rates_pct": failure_rates,
            "average_job_duration_sec": avg_job_durations,
            "total_observed_cost_usd": round(self.total_cost_usd, 4)
        }

metrics_tracker = MetricsTracker()
