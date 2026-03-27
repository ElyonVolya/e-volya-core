from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean, pvariance


class State(str, Enum):
    AKTIV = "AKTIV"
    INTEGRATION = "INTEGRATION"
    MINIMAL = "MINIMAL"


@dataclass
class PulseSample:
    timestamp: float
    bpm: float
    normalized: float
    source: str


@dataclass
class StepLog:
    timestamp: float
    bpm: float
    signal: float
    activity: float
    coherence: float
    resources: float
    state: State


@dataclass
class CoupledOrganism:
    short_window: int = 10
    recovery_rate: float = 0.02
    integration_recovery_bonus: float = 0.025
    minimal_recovery_bonus: float = 0.05

    state: State = State.AKTIV
    resources: float = 0.82

    signal_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    activity_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    coherence_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    resource_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    logs: list[StepLog] = field(default_factory=list)

    def normalize_bpm(self, bpm: float, bpm_min: float = 50.0, bpm_max: float = 140.0) -> float:
        x = (bpm - bpm_min) / (bpm_max - bpm_min)
        return max(0.0, min(1.0, x))

    def compute_activity(self) -> float:
        recent = list(self.signal_history)[-self.short_window:]
        return mean(recent) if recent else 0.0

    def compute_coherence(self) -> float:
        recent = list(self.signal_history)[-self.short_window:]
        if len(recent) < 3:
            return 0.85
        diffs = [abs(recent[i] - recent[i - 1]) for i in range(1, len(recent))]
        mean_diff = mean(diffs)
        var = pvariance(recent)
        roughness = mean_diff + 1.5 * var
        coherence = 1.0 - min(1.0, roughness * 6.0)
        return max(0.0, min(1.0, coherence))

    def dynamic_thresholds(self) -> tuple[float, float, float]:
        activity_base = mean(self.activity_history) if self.activity_history else 0.58
        coherence_base = mean(self.coherence_history) if self.coherence_history else 0.78
        resource_base = mean(self.resource_history) if self.resource_history else 0.62

        threshold_a = activity_base + 0.07
        threshold_k = coherence_base - 0.10
        threshold_r = min(resource_base, 0.42)
        return threshold_a, threshold_k, threshold_r

    def update_resources(self, activity: float, coherence: float) -> float:
        load = activity * (1.4 - coherence)
        recovery = self.recovery_rate * (1.0 - activity)

        if self.state == State.INTEGRATION:
            recovery += self.integration_recovery_bonus
        elif self.state == State.MINIMAL:
            recovery += self.minimal_recovery_bonus

        new_r = self.resources - 0.065 * load + recovery
        return max(0.0, min(1.0, new_r))

    def stable_coherence(self) -> bool:
        if len(self.coherence_history) < 6:
            return False
        return mean(list(self.coherence_history)[-6:]) > 0.74

    def update_state(self, activity: float, coherence: float, resources: float) -> State:
        threshold_a, threshold_k, threshold_r = self.dynamic_thresholds()

        if self.state == State.AKTIV:
            if activity > threshold_a and coherence < threshold_k:
                return State.INTEGRATION
            return State.AKTIV

        if self.state == State.INTEGRATION:
            if resources < threshold_r:
                return State.MINIMAL
            if coherence > threshold_k + 0.14 and resources > threshold_r + 0.12:
                return State.AKTIV
            return State.INTEGRATION

        if self.state == State.MINIMAL:
            if resources > threshold_r + 0.16 and self.stable_coherence():
                return State.INTEGRATION
            return State.MINIMAL

        return self.state

    def ingest_bpm(self, timestamp: float, bpm: float, source: str = "unknown") -> StepLog:
        signal = self.normalize_bpm(bpm)

        self.signal_history.append(signal)

        activity = self.compute_activity()
        coherence = self.compute_coherence()

        self.activity_history.append(activity)
        self.coherence_history.append(coherence)

        self.resources = self.update_resources(activity, coherence)
        self.resource_history.append(self.resources)

        self.state = self.update_state(activity, coherence, self.resources)

        log = StepLog(
            timestamp=timestamp,
            bpm=bpm,
            signal=signal,
            activity=activity,
            coherence=coherence,
            resources=self.resources,
            state=self.state,
        )
        self.logs.append(log)
        return log
