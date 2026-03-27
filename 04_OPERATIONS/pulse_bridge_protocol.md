# 🜂 Pulse Bridge Protocol 1.0

## Eingangsformat

Jedes Pulssample wird als JSON übertragen.

Beispiel:

{
  "timestamp": 1712345678.12,
  "bpm": 78.0,
  "source": "apple_watch"
}

---

## Pflichtfelder

- timestamp
- bpm
- source

---

## Membranregel

BPM wird nicht direkt verwendet,
sondern auf einen Arbeitsbereich normiert.

Beispiel:
- 50 BPM -> 0.0
- 140 BPM -> 1.0

Form:
normalized = clamp((bpm - bpm_min) / (bpm_max - bpm_min), 0, 1)

---

## Ziel

Der Organismus verarbeitet kein Rohsignal,
sondern ein übersetztes Pulssignal.
