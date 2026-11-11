# Spec Delta

## MODIFIED Requirements

### Requirement: Single deferred floating-chat mount

The root layout SHALL contain exactly one floating-chat integration mount across login
and authenticated CU09 views. When the CU03 runtime and provider configuration are
available, the mount SHALL accept messages and stream answers through the dedicated
assistant client; when the runtime, provider or configuration is unavailable, it SHALL
clearly communicate an unavailable or static fallback state, SHALL NOT fabricate answers,
and SHALL NOT connect to an unapproved provider.

#### Scenario: One functional mount when CU03 is available

- **GIVEN** the CU03 runtime and provider configuration are available
- **WHEN** the user opens login, enters CU09 or switches domiciles
- **THEN** there is exactly one floating chat mount, it accepts messages and streams answers through the dedicated client

#### Scenario: Shell reserves CU03 without pretending it is implemented

- **GIVEN** the CU03 runtime, provider or configuration is unavailable
- **WHEN** the user opens login, enters CU09 or switches domiciles
- **THEN** there is only one root chat mount with an explicit unavailable or static fallback state and no fabricated answer
