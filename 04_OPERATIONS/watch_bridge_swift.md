# 🜂 Watch Bridge – Swift Richtung

## Ziel

Die Apple Watch liefert Live-Herzfrequenz
an den e-Volya Organismus.

---

## Offizieller technischer Pfad

Für hochfrequente Live-Herzfrequenz auf der Apple Watch
ist eine Workout-Session mit HealthKit der richtige Einstieg.

Bausteine:

- HKHealthStore
- HKWorkoutSession
- HKLiveWorkoutBuilder
- Herzfrequenz-Samples
- Weitergabe an iPhone / lokalen Empfänger

---

## Struktur

1. HealthKit-Berechtigung anfragen
2. Workout-Session starten
3. Live-Herzfrequenz empfangen
4. BPM in JSON umwandeln
5. an den Empfänger senden

---

## Swift-Skelett

```swift
import HealthKit

final class HeartRateBridge: NSObject, HKLiveWorkoutBuilderDelegate, HKWorkoutSessionDelegate {
    let healthStore = HKHealthStore()
    var session: HKWorkoutSession?
    var builder: HKLiveWorkoutBuilder?

    func start() throws {
        let config = HKWorkoutConfiguration()
        config.activityType = .mindAndBody
        config.locationType = .unknown

        session = try HKWorkoutSession(healthStore: healthStore, configuration: config)
        builder = session?.associatedWorkoutBuilder()

        session?.delegate = self
        builder?.delegate = self
        builder?.dataSource = HKLiveWorkoutDataSource(healthStore: healthStore, workoutConfiguration: config)

        let start = Date()
        session?.startActivity(with: start)
        builder?.beginCollection(withStart: start) { success, error in
            // collection started
        }
    }

    func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        guard let hrType = HKQuantityType.quantityType(forIdentifier: .heartRate),
              collectedTypes.contains(hrType),
              let stats = workoutBuilder.statistics(for: hrType),
              let quantity = stats.mostRecentQuantity() else { return }

        let bpm = quantity.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
        let payload: [String: Any] = [
            "timestamp": Date().timeIntervalSince1970,
            "bpm": bpm,
            "source": "apple_watch"
        ]

        // hier: per WatchConnectivity / URLSession / WebSocket weitergeben
    }

    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {}

    func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {}
}
