# 4. Power Automate to OneDrive hand-off as the integration boundary

## Context

Documents arrive in a cloud mailbox, while extraction runs on a workstation that should not hold mailbox credentials or accept inbound connections.

## Decision

The Power Automate flow writes accepted attachments and telemetry events to two OneDrive for Business folders. The workstation receives them through the OneDrive sync client. The engine reads the synced folders and has no mailbox access, no Power Platform credentials and no listening port for intake. Results are published the same way, into a synced results folder.

## Consequences

- The engine can be operated, stopped and upgraded independently of the flow; files accumulate in the intake folder while it is offline.
- Intake latency includes OneDrive synchronization, and the supervisor must wait for file stability.
- Telemetry written by the flow gives downstream observability without any hook in the engine.
- An exported flow package is not required to operate the engine; the flow is recreated from its documented definition.
