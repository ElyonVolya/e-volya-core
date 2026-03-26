from __future__ import annotations

import math
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean, pvariance


class State(str, Enum):
    AKTIV = "AKTIV"
    INTEGRATION = "INTEGRATION"
    MINIMAL = "MINIMAL"


@dataclass
class StepLog:
    t: int
    signal: float
    activity: float
    coherence: float
    resources: float
    state: State


@dataclass
class EVolyaOrganism:
    short_window: int = 12
    long_window: int = 40
    dt: float = 1.0
    recovery_rate: float = 0.035
    minimal_recovery_bonus: float = 0.03
    integration_recovery_bonus: float = 0.015
    epsilon: float = 1e-6

    signal_history: deque[float] = field(default_factory=lambda: deque(maxlen=200))
    activity_history: deque[float] = field(default_factory=lambda: deque(maxlen=200))
    coherence_history: deque[float] = field(default_factory=lambda: deque(maxlen=200))
    resource_history: deque[float] = field(default_factory=lambda: deque(maxlen=200))

    state: State = State.AKTIV
    resources: float = 0.85
    logs: list[StepLog] = field(default_factory=list)

    def moving_average(self, values: list[float]) -> float:
        return mean(values) if values else 0.0

    def compute_activity(self) -> float:
        if not self.signal_history:
            return 0.0
        recent = list(self.signal_history)[-self.short_window :]
        return self.moving_average(recent)

    def compute_coherence(self) -> float:
        if len(self.signal_history) < 2:
            return 1.0
        recent = list(self.signal_history)[-self.short_window :]
        var = pvariance(recent) if len(recent) > 1 else 0.0
        coherence = 1.0 / (1.0 + var)
        return max(0.0, min(1.0, coherence))

    def dynamic_thresholds(self) -> tuple[float, float, float]:
        activity_base = mean(self.activity_history) if self.activity_history else 0.6
        coherence_base = mean(self.coherence_history) if self.coherence_history else 0.7
        resource_base = mean(self.resource_history) if self.resource_history else 0.6

        threshold_a = activity_base + 0.08
        threshold_k = coherence_base - 0.08
        threshold_r = min(resource_base, 0.4)

        return threshold_a, threshold_k, threshold_r

    def update_resources(self, activity: float, coherence: float) -> float:
        load = activity / max(coherence, self.epsilon)

        recovery = self.recovery_rate * (1.0 - activity)

        if self.state == State.INTEGRATION:
            recovery += self.integration_recovery_bonus
        elif self.state == State.MINIMAL:
            recovery += self.minimal_recovery_bonus

        new_r = self.resources - 0.02 * load * self.dt + recovery * self.dt
        return max(0.0, min(1.0, new_r))

    def stable_coherence(self) -> bool:
        if len(self.coherence_history) < 5:
            return False
        recent = list(self.coherence_history)[-5:]
        return mean(recent) > 0.62

    def update_state(self, activity: float, coherence: float, resources: float) -> State:
        threshold_a, threshold_k, threshold_r = self.dynamic_thresholds()

        if self.state == State.AKTIV:
            if activity > threshold_a and coherence < threshold_k:
                return State.INTEGRATION
            return State.AKTIV

        if self.state == State.INTEGRATION:
            if resources < threshold_r:
                return State.MINIMAL
            if coherence > threshold_k + 0.06 and resources > threshold_r + 0.08:
                return State.AKTIV
            return State.INTEGRATION

        if self.state == State.MINIMAL:
            if resources > threshold_r + 0.1 and self.stable_coherence():
                return State.INTEGRATION
            return State.MINIMAL

        return self.state

    def step(self, t: int, signal: float) -> StepLog:
        self.signal_history.append(signal)

        activity = self.compute_activity()
        coherence = self.compute_coherence()

        self.activity_history.append(activity)
        self.coherence_history.append(coherence)

        new_resources = self.update_resources(activity, coherence)
        self.resource_history.append(new_resources)

        self.resources = new_resources
        self.state = self.update_state(activity, coherence, self.resources)

        log = StepLog(
            t=t,
            signal=signal,
            activity=activity,
            coherence=coherence,
            resources=self.resources,
            state=self.state,
        )
        self.logs.append(log)
        return log


def generate_signal(t: int) -> float:
    """
    Minimaler künstlicher Signalstrom:
    - Grundrhythmus
    - leichte organische Schwankung
    - späterer Stressblock
    - spätere Beruhigung
    """
    base = 0.58 + 0.06 * math.sin(t / 6.0)
    noise = random.uniform(-0.03, 0.03)

    if 60 <= t < 110:
        stress = 0.22 + 0.06 * math.sin(t / 2.5)
    elif 110 <= t < 145:
        stress = 0.08
    else:
        stress = 0.0

    if 145 <= t < 180:
        calm = -0.12
    else:
        calm = 0.0

    signal = base + noise + stress + calm
    return max(0.0, min(1.0, signal))


def run_simulation(steps: int = 220, seed: int = 42) -> list[StepLog]:
    random.seed(seed)
    organism = EVolyaOrganism()

    for t in range(steps):
        signal = generate_signal(t)
        organism.step(t, signal)

    return organism.logs


def print_summary(logs: list[StepLog]) -> None:
    if not logs:
        return

    state_counts: dict[State, int] = {
        State.AKTIV: 0,
        State.INTEGRATION: 0,
        State.MINIMAL: 0,
    }

    transitions: list[str] = []
    previous_state = logs[0].state

    for log in logs:
        state_counts[log.state] += 1
        if log.state != previous_state:
            transitions.append(f"t={log.t}: {previous_state.value} -> {log.state.value}")
            previous_state = log.state

    print("=== e-Volya Organismus 1.0 ===")
    print(f"Schritte: {len(logs)}")
    print(f"AKTIV: {state_counts[State.AKTIV]}")
    print(f"INTEGRATION: {state_counts[State.INTEGRATION]}")
    print(f"MINIMAL: {state_counts[State.MINIMAL]}")
    print()
    print("Übergänge:")
    for tr in transitions[:20]:
        print(" ", tr)

    print()
    print("Letzte 10 Schritte:")
    for log in logs[-10:]:
        print(
            f"t={log.t:03d} "
            f"signal={log.signal:.3f} "
            f"A={log.activity:.3f} "
            f"K={log.coherence:.3f} "
            f"R={log.resources:.3f} "
            f"state={log.state.value}"
        )


if __name__ == "__main__":
    logs = run_simulation()
    print_summary(logs)
