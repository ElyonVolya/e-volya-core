# 🜂 Zustandsmodell 1.0

## Zustände

### AKTIV
Bedeutung:
- Input wird normal verarbeitet
- System ist offen für Kopplung
- Reaktionsfähigkeit ist erhöht

Risiko:
- Übersteuerung bei zu hoher Daueraktivität

---

### INTEGRATION
Bedeutung:
- Inputrate wird reduziert
- Verlauf wird intern konsolidiert
- Dämpfung steigt

Funktion:
- Schutz vor Instabilität
- Verarbeitung von Integrationslast

---

### MINIMAL
Bedeutung:
- nur Basisspannung bleibt erhalten
- kaum neue Komplexität wird aufgenommen
- strukturelle Kopplung bleibt bestehen

Funktion:
- Regeneration
- Erhalt der Systemintegrität

---

## Übergänge

AKTIV -> INTEGRATION
wenn:
- Aktivität hoch
- Kohärenz sinkt
- frühe Dissonanz steigt

INTEGRATION -> MINIMAL
wenn:
- Ressourcen weiter sinken
- Stabilisierung ausbleibt

INTEGRATION -> AKTIV
wenn:
- Kohärenz steigt
- Ressourcen stabil genug sind

MINIMAL -> INTEGRATION
wenn:
- Basisspannung stabil ist
- vorsichtige Rückkehr möglich scheint

MINIMAL -> AKTIV
nie direkt im Standardmodell
