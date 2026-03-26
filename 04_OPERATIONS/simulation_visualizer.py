from __future__ import annotations
import math
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean, pvariance
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent

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
    dt: float = 1.0
    recovery_rate: float = 0.02
    minimal_recovery_bonus: float = 0.05
    integration_recovery_bonus: float = 0.025
    epsilon: float = 1e-6
    signal_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    activity_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    coherence_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    resource_history: deque[float] = field(default_factory=lambda: deque(maxlen=300))
    state: State = State.AKTIV
    resources: float = 0.82
    logs: list[StepLog] = field(default_factory=list)

    def moving_average(self, values: list[float]) -> float:
        return mean(values) if values else 0.0

    def compute_activity(self) -> float:
        recent = list(self.signal_history)[-self.short_window :]
        return self.moving_average(recent) if recent else 0.0

    def compute_coherence(self) -> float:
        recent = list(self.signal_history)[-self.short_window :]
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
        new_r = self.resources - 0.065 * load * self.dt + recovery * self.dt
        return max(0.0, min(1.0, new_r))

    def stable_coherence(self) -> bool:
        if len(self.coherence_history) < 6:
            return False
        recent = list(self.coherence_history)[-6:]
        return mean(recent) > 0.74

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

    def step(self, t: int, signal: float) -> StepLog:
        self.signal_history.append(signal)
        activity = self.compute_activity()
        coherence = self.compute_coherence()
        self.activity_history.append(activity)
        self.coherence_history.append(coherence)
        self.resources = self.update_resources(activity, coherence)
        self.resource_history.append(self.resources)
        self.state = self.update_state(activity, coherence, self.resources)
        log = StepLog(t=t, signal=signal, activity=activity, coherence=coherence, resources=self.resources, state=self.state)
        self.logs.append(log)
        return log

def generate_signal(t: int) -> float:
    base = 0.58 + 0.06 * math.sin(t / 6.0)
    noise = random.uniform(-0.04, 0.04)
    if 45 <= t < 95:
        stress = 0.25 + 0.10 * math.sin(t / 1.9) + random.uniform(-0.04, 0.04)
    elif 95 <= t < 145:
        stress = 0.13 + 0.05 * math.sin(t / 2.8)
    else:
        stress = 0.0
    if 145 <= t < 190:
        calm = -0.14 + random.uniform(-0.01, 0.01)
    else:
        calm = 0.0
    signal = base + noise + stress + calm
    return max(0.0, min(1.0, signal))

def run_simulation(steps: int = 220, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    organism = EVolyaOrganism()
    for t in range(steps):
        organism.step(t, generate_signal(t))
    df = pd.DataFrame([{
        "t": log.t,
        "signal": log.signal,
        "activity": log.activity,
        "coherence": log.coherence,
        "resources": log.resources,
        "state": log.state.value,
        "state_code": {"AKTIV": 2, "INTEGRATION": 1, "MINIMAL": 0}[log.state.value],
    } for log in organism.logs])
    return df

df = run_simulation()
df.to_csv(base / "organism_log.csv", index=False)

def make_plot(ycol: str, ylabel: str, title: str, filename: str):
    plt.figure(figsize=(10, 4.8))
    plt.plot(df["t"], df[ycol])
    plt.xlabel("t")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(base / filename, dpi=160)
    plt.close()

make_plot("signal", "Signal", "e-Volya Organismus – Signalstrom", "signal_plot.png")
make_plot("activity", "Aktivität", "e-Volya Organismus – Aktivitätsniveau", "activity_plot.png")
make_plot("coherence", "Kohärenz", "e-Volya Organismus – Kohärenz", "coherence_plot.png")
make_plot("resources", "Ressourcen", "e-Volya Organismus – Ressourcen", "resources_plot.png")

plt.figure(figsize=(10, 3.8))
plt.step(df["t"], df["state_code"], where="post")
plt.yticks([0, 1, 2], ["MINIMAL", "INTEGRATION", "AKTIV"])
plt.xlabel("t")
plt.ylabel("Zustand")
plt.title("e-Volya Organismus – Zustandsverlauf")
plt.tight_layout()
plt.savefig(base / "state_timeline.png", dpi=160)
plt.close()
