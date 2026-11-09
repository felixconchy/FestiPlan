# Diagramme de séquence — déplacer un concert

`PATCH /concerts/{id}/reschedule`. La modification est **validée au commit** de `SqlFestivalRepository.save` ; la notification n'a lieu qu'**après**, et son échec ne change pas la réponse (200 + `notification_status: "failed"`).

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant C as Contrôleur<br/>adapters/http/concerts.py
    participant UC as RescheduleConcert<br/>(cas d'utilisation)
    participant FR as FestivalRepository<br/>(SqlFestivalRepository)
    participant SR as Stage/ArtistRepository
    participant F as Festival<br/>(agrégat)
    participant D as EventDispatcher
    participant N as Notifier<br/>(EmailNotifier)

    Client->>C: PATCH /concerts/11/reschedule {start, end}
    C->>C: validation Pydantic (format)
    C->>UC: execute(RescheduleConcertCommand)
    UC->>UC: TimeSlot(start, end)
    alt fin <= début (R1)
        UC-->>C: InvalidValue
        C-->>Client: 400 Bad Request
    end
    UC->>FR: find_by_concert(11)
    FR-->>UC: Festival + concerts
    alt concert inconnu
        UC-->>C: NotFound
        C-->>Client: 404 Not Found
    end
    UC->>SR: get(stage_id), get(artist_id)
    SR-->>UC: Stage, Artist
    UC->>F: reschedule_concert(11, slot, stage, artist)
    F->>F: planning publié ? (R7)
    alt planning publié
        F-->>UC: ScheduleLocked
        UC-->>C: ScheduleLocked
        C-->>Client: 409 Conflict (utiliser la procédure published-reschedule)
    end
    F->>F: _check : R4 scène du festival, R6 période,<br/>R5 équipements, R2 scène libre, R3 artiste libre
    alt règle violée
        F-->>UC: SchedulingConflict ou RuleViolation
        UC-->>C: exception (rien n'est enregistré)
        C-->>Client: 409 Conflict ou 400 Bad Request
    end
    F->>F: applique le nouveau créneau et enregistre ConcertRescheduled
    F-->>UC: concert
    UC->>FR: save(festival)
    Note over FR: COMMIT, la modification est validée
    UC->>F: pull_events()
    UC->>D: dispatch([ConcertRescheduled])
    D->>N: notify(event)
    alt envoi réussi
        N-->>D: ok
        D-->>UC: SENT
    else panne du service
        N-->>D: NotificationError
        D->>D: journalise l'erreur (logger.exception)
        D-->>UC: FAILED
    end
    UC-->>C: OperationResult(concert, status)
    C-->>Client: 200 OK avec concert et notification_status (sent ou failed)
```
