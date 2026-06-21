# Intelligent Endpoint Security Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-platform Python security agent with AI anomaly detection and dual-mode response over a 1-month phased period.

**Architecture:** A modular Python application with an Orchestrator, independent Telemetry Monitors (File, Process, Network), an Inference Engine using Isolation Forest, and a Response Engine for auditing and user prompts.

**Tech Stack:** Python 3.10+, psutil, watchdog, scikit-learn, pandas/numpy, plyer, requests.

---

## Phase 1: Foundation & Event Schema (Week 1)

### Task 1: Core Event Schema

**Files:**
- Create: `src/models/event.py`
- Test: `tests/models/test_event.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from src.models.event import SecurityEvent

def test_security_event_creation():
    event = SecurityEvent(
        source="file",
        action="modify",
        actor_pid=1234,
        actor_name="unknown.exe",
        target="/etc/shadow",
        metadata={"size_delta": 1024, "entropy": 7.8}
    )
    assert event.source == "file"
    assert event.action == "modify"
    assert event.actor_pid == 1234
    assert event.actor_name == "unknown.exe"
    assert event.target == "/etc/shadow"
    assert event.metadata == {"size_delta": 1024, "entropy": 7.8}
    
    event_dict = event.to_dict()
    assert "timestamp" in event_dict
    assert event_dict["source"] == "file"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_event.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src'"

- [ ] **Step 3: Write minimal implementation**

```python
import datetime
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class SecurityEvent:
    source: str
    action: str
    actor_pid: int
    actor_name: str
    target: str
    metadata: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "action": self.action,
            "actor_pid": self.actor_pid,
            "actor_name": self.actor_name,
            "target": self.target,
            "metadata": self.metadata
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/models/test_event.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/models/test_event.py src/models/event.py
git commit -m "feat: implement SecurityEvent schema"
```

## Phase 2: Telemetry Monitors (Week 2)

### Task 2: Process Monitor

**Files:**
- Create: `src/monitors/process.py`
- Test: `tests/monitors/test_process.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch, MagicMock
from src.monitors.process import ProcessMonitor
from src.models.event import SecurityEvent

@patch("src.monitors.process.psutil.process_iter")
def test_process_monitor_snapshot(mock_process_iter):
    mock_proc = MagicMock()
    mock_proc.info = {
        'pid': 1234, 
        'name': 'test.exe', 
        'exe': '/path/test.exe',
        'cpu_percent': 5.0,
        'memory_info': MagicMock(rss=1024)
    }
    mock_process_iter.return_value = [mock_proc]
    
    monitor = ProcessMonitor()
    events = monitor.snapshot()
    
    assert len(events) == 1
    assert isinstance(events[0], SecurityEvent)
    assert events[0].source == "process"
    assert events[0].action == "snapshot"
    assert events[0].actor_pid == 1234
    assert events[0].actor_name == "test.exe"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/monitors/test_process.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import psutil
from typing import List
from src.models.event import SecurityEvent

class ProcessMonitor:
    def snapshot(self) -> List[SecurityEvent]:
        events = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info']):
            try:
                info = proc.info
                events.append(SecurityEvent(
                    source="process",
                    action="snapshot",
                    actor_pid=info['pid'],
                    actor_name=info['name'] or "unknown",
                    target=info['exe'] or "unknown",
                    metadata={
                        "cpu_percent": info.get('cpu_percent', 0.0),
                        "memory_rss": info.get('memory_info').rss if info.get('memory_info') else 0
                    }
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return events
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/monitors/test_process.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/monitors/test_process.py src/monitors/process.py
git commit -m "feat: implement ProcessMonitor snapshot"
```

## Phase 3: AI Inference Engine (Week 3)

### Task 3: Inference Engine Isolation Forest

**Files:**
- Create: `src/engine/inference.py`
- Test: `tests/engine/test_inference.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
import numpy as np
from src.engine.inference import InferenceEngine
from src.models.event import SecurityEvent

def test_inference_engine_train_and_score():
    engine = InferenceEngine()
    events = [
        SecurityEvent("process", "start", 100, "a.exe", "t1", {"cpu_percent": 1.0, "memory_rss": 100}),
        SecurityEvent("process", "start", 101, "b.exe", "t2", {"cpu_percent": 2.0, "memory_rss": 200}),
        SecurityEvent("process", "start", 102, "c.exe", "t3", {"cpu_percent": 1.5, "memory_rss": 150})
    ]
    engine.train(events)
    
    anomaly = SecurityEvent("process", "start", 999, "malware.exe", "t4", {"cpu_percent": 99.0, "memory_rss": 999999})
    score = engine.score(anomaly)
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/engine/test_inference.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List
from src.models.event import SecurityEvent

class InferenceEngine:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False

    def _vectorize(self, event: SecurityEvent) -> np.ndarray:
        cpu = event.metadata.get("cpu_percent", 0.0)
        mem = event.metadata.get("memory_rss", 0.0)
        return np.array([[cpu, mem]])

    def train(self, events: List[SecurityEvent]):
        if not events:
            return
        vectors = np.vstack([self._vectorize(e) for e in events])
        self.model.fit(vectors)
        self.is_trained = True

    def score(self, event: SecurityEvent) -> float:
        if not self.is_trained:
            return 0.0
        vec = self._vectorize(event)
        # decision_function returns <0 for anomalies, >0 for normal.
        raw_score = self.model.decision_function(vec)[0]
        # raw_score is usually between -0.5 and 0.5. Map to 0-1.
        anomaly_score = 0.5 - (raw_score) 
        return max(0.0, min(1.0, anomaly_score))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/engine/test_inference.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/engine/test_inference.py src/engine/inference.py
git commit -m "feat: implement AI Inference Engine"
```

## Phase 4: Response Engine & UI (Week 4)

### Task 4: Response Engine Audit and Alert

**Files:**
- Create: `src/response/engine.py`
- Test: `tests/response/test_engine.py`

- [ ] **Step 1: Write the failing test**

```python
import pytest
from unittest.mock import patch, MagicMock
from src.response.engine import ResponseEngine
from src.models.event import SecurityEvent

@patch("plyer.notification.notify")
def test_response_engine_action(mock_notify):
    engine = ResponseEngine(audit_log_path=":memory:")
    
    # Normal event
    event1 = SecurityEvent("file", "read", 111, "app.exe", "file.txt", {})
    engine.handle_event(event1, score=0.1)
    mock_notify.assert_not_called()
    
    # Anomalous event
    event2 = SecurityEvent("process", "start", 999, "malware.exe", "mal.exe", {})
    engine.handle_event(event2, score=0.9)
    mock_notify.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/response/test_engine.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
import sqlite3
import json
try:
    import plyer.notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False

from src.models.event import SecurityEvent

class ResponseEngine:
    def __init__(self, audit_log_path: str = "audit.db"):
        self.conn = sqlite3.connect(audit_log_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                source TEXT,
                action TEXT,
                actor_pid INTEGER,
                actor_name TEXT,
                target TEXT,
                metadata TEXT,
                score REAL
            )
        ''')
        self.conn.commit()

    def handle_event(self, event: SecurityEvent, score: float):
        # Audit
        self.conn.execute('''
            INSERT INTO events (timestamp, source, action, actor_pid, actor_name, target, metadata, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (event.timestamp, event.source, event.action, event.actor_pid, event.actor_name, event.target, json.dumps(event.metadata), score))
        self.conn.commit()

        # Prompt
        if score >= 0.85 and HAS_PLYER:
            plyer.notification.notify(
                title="Security Alert",
                message=f"High anomaly detected in {event.actor_name} (Score: {score:.2f})",
                app_name="Intelligent Security Agent",
                timeout=10
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/response/test_engine.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/response/test_engine.py src/response/engine.py
git commit -m "feat: implement Response Engine with audit and alerts"
```