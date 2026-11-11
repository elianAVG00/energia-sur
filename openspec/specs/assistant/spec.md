# assistant Specification

## Purpose
Provide public, grounded conversational guidance about current outages, scheduled works
and consultation/complaint procedures, citing official sources and bounded by provenance,
memory, streaming, fallback and resource limits.

## Requirements

### Requirement: Answer public guidance without an account

The assistant SHALL let a visitor ask about current outages, scheduled works and
consultation/complaint procedures without signing in, and SHALL ground the answer on
approved official sources. An absent, invalid or expired session SHALL be treated as
anonymous, not rejected. Trace: CU03-R1, CU03-S01, SR01, SR03, U23.

#### Scenario: Visitor asks a procedure question

- **GIVEN** a visitor without a session and approved official sources
- **WHEN** the visitor asks how to consult or complain about an outage
- **THEN** the assistant returns grounded guidance and identifies its sources without requiring login

#### Scenario: Stale cookie does not block public chat

- **GIVEN** a visitor whose session cookie is expired or invalid
- **WHEN** the visitor sends a chat request
- **THEN** the request is treated as anonymous and is not rejected with 401

### Requirement: Serve live-status answers from cached public snapshots only

The assistant SHALL answer live-status questions only from the persisted CU01/CU02
snapshots, SHALL NOT call ENRE or GeoRef at query time, and SHALL NOT invent a live
outage, restoration or scheduled work. Trace: U23 (D3), CU03-S02, SR03,
current-outages, scheduled-works.

#### Scenario: Asked whether service is restored with a stale snapshot

- **GIVEN** a stale or unavailable outage snapshot
- **WHEN** the visitor asks whether service is currently restored
- **THEN** the assistant does not claim a live status and answers from the cached snapshot with its freshness

### Requirement: Preserve freshness, coverage and normative states

The assistant SHALL carry the source freshness, coverage and normative result state into
its answer, SHALL return "no outages" only for a fresh, covered query, and SHALL NOT
assert supply status for an individual address or meter. Trace: SR03, current-outages,
CU03-S02.

#### Scenario: Unverified coverage is not reported as clear

- **GIVEN** a fresh snapshot and a zone classified `coverage_unverified`
- **WHEN** the visitor asks about outages in that zone
- **THEN** the assistant reports the unverified coverage and does not present the zone as outage-free

#### Scenario: Zone result is not an address result

- **GIVEN** a reported outage for a locality
- **WHEN** the visitor asks whether their own address has power
- **THEN** the assistant reports the zone-level result and does not assert supply for that address

### Requirement: Respect the CU02 definitive scope

For scheduled works the assistant SHALL NOT state a planned start, planned end, reason,
distance or future agenda, and SHALL NOT offer date filters, consistent with the U22
definitive scope. Trace: U22, scheduled-works.

#### Scenario: Asked when a scheduled work ends

- **GIVEN** a reported maintenance work whose source publishes no planned end
- **WHEN** the visitor asks when the work will finish
- **THEN** the assistant states that the source does not publish a planned end and does not invent a date or reason

### Requirement: Ground procedural guidance at article granularity from the approved guide

The assistant SHALL answer procedure, channel and benefit questions from the active
approved Edesur guide (`document_id` `energia-sur-kb-edesur-001`) by retrieving complete
article units identified by their article ID (for example `CA-01`, `PA-01`, `TS-01`),
preserving each article's `source_name` and per-URL `source_urls`, and SHALL NOT mix
different procedures in one answer. Trace: SR03, Q06, U23, guide.

#### Scenario: Article-level answer with sources

- **GIVEN** the guide indexed and the visitor asks a question equivalent to an article
- **WHEN** the assistant answers
- **THEN** it uses the matching article as a complete unit and cites each source_urls entry with its own organism

#### Scenario: Ambiguous articles are not mixed

- **GIVEN** two different procedure articles could match the question
- **WHEN** the assistant answers
- **THEN** it uses one best article or asks the user to clarify, and does not blend different procedures

#### Scenario: No matching article

- **GIVEN** no indexed article matches the question
- **WHEN** the assistant cannot ground an answer
- **THEN** it returns the static fallback and does not fabricate guide content

### Requirement: Serve only the current guide version

When more than one guide version is indexed, the assistant SHALL retrieve only the current
active version's articles and SHALL NOT surface superseded content. Trace: U23, guide.

#### Scenario: New version supersedes the old

- **GIVEN** version 1.0.0 indexed and version 1.0.1 ingested
- **WHEN** the visitor asks an affected question
- **THEN** the answer reflects 1.0.1 and the superseded 1.0.0 content is not surfaced

### Requirement: Disclose staleness and incomplete information

When the guide's `last_verified_at` exceeds the configured maximum age, when an article is
classified as volatile, or when an article marks information as not published or limited,
the assistant SHALL state the verification date and limitation and SHALL NOT fill the gap.
Trace: SR03, Q06, U23, guide.

#### Scenario: Stale guide is disclosed

- **GIVEN** a guide whose last_verified_at is older than the configured maximum
- **WHEN** the visitor asks a time-sensitive question
- **THEN** the assistant states the verification date and that it may be outdated, and recommends confirming at the official link

#### Scenario: Volatile article is flagged even when current

- **GIVEN** a recent guide and a volatile article such as phones, hours, payment methods or subsidy requirements
- **WHEN** the visitor asks a time-sensitive detail
- **THEN** the assistant adds a "subject to change; confirm at the official link" notice

#### Scenario: Incomplete article is not filled

- **GIVEN** an article that states the information is not published or a procedure is partially documented (for example PA-07, TR-03 or TR-04)
- **WHEN** the visitor asks about that detail
- **THEN** the assistant reports the limitation and does not invent the missing detail

### Requirement: Separate documentary guidance from dynamic public data

Live outage and scheduled-work status SHALL come only from the CU01/CU02 tools; guide
articles SHALL explain where or how to consult and SHALL NOT be presented as current
status. Trace: SR03, U23, current-outages, scheduled-works, guide (CR-01, CR-03, LI-02).

#### Scenario: Current-state question uses dynamic data

- **GIVEN** a question about whether a zone has power now
- **WHEN** the assistant answers
- **THEN** it uses the CU01 snapshot with freshness and coverage and does not substitute a guide article

#### Scenario: Procedure question uses the guide

- **GIVEN** a question about where to consult outages
- **WHEN** the assistant answers
- **THEN** it uses the guide article (for example CR-01) and cites its official link

#### Scenario: Mixed question labels both sources

- **GIVEN** a question that asks both current status and how to complain
- **WHEN** the assistant answers
- **THEN** it cites the CU01/CU02 state and the guide article separately, and the guide does not override the dynamic state

### Requirement: Cite official sources on data-bearing answers

Every answer that presents data or guidance SHALL identify its source with organism and
URL when the source publishes one (for guide articles, `source_name` and per-URL
`source_urls`; adding a title when available); when no source supports an answer the
assistant SHALL return the static fallback instead of an unsupported statement. Trace:
SR03, U23 (D6), current-outages, scheduled-works, guide.

#### Scenario: Data answer shows provenance

- **GIVEN** a cached ENRE snapshot used to answer
- **WHEN** the assistant returns a data-bearing answer
- **THEN** the answer identifies ENRE with its source link and update time

#### Scenario: No supporting source

- **GIVEN** no retrieved guide passage and no public snapshot support the request
- **WHEN** the assistant cannot ground an answer
- **THEN** it returns the identifiable static fallback and does not state an unsupported fact

### Requirement: Cite capability-limit statements without fabricating a URL

A capability-limit statement such as `LI-01`, which has no external source, SHALL be cited
by `document_id`, `article_id` and title and SHALL NOT include a fabricated URL. Trace:
SR03, U23 (D6), guide.

#### Scenario: Capability statement cites its document

- **GIVEN** the capability-limit article LI-01, which has no external source
- **WHEN** the assistant explains a capability limit
- **THEN** it cites the document/article identity and does not fabricate a URL

### Requirement: Validate and render citations safely

Citations SHALL be built server-side from retrieved guide rows and tool metadata, SHALL
accept only `https` URLs whose host matches a static official allowlist, and SHALL render
as text or links without raw HTML; the model-authored answer body SHALL render as plain
text. Trace: SR03, U23, AGENTS.md.

#### Scenario: Model text cannot introduce a citation

- **GIVEN** a streamed answer containing a Markdown link or HTML
- **WHEN** it is rendered
- **THEN** it appears as plain text and no non-allowlisted link is created

### Requirement: Separate temporary public memory from persistent authenticated memory

The assistant SHALL keep anonymous conversations in bounded, short-lived temporary memory
that is not durable, and SHALL persist authenticated conversations only for the owning
account, excluding them from other accounts and allowing the owner to list and clear them.
It SHALL NOT log message content, provider keys or credentials, and SHALL place message
content only in the owning account's conversation or in non-durable temporary memory.
Trace: U23, SR02, SR04.

#### Scenario: Anonymous conversation is temporary

- **GIVEN** a visitor without a session
- **WHEN** the visitor converses and the temporary lifetime elapses
- **THEN** the conversation is no longer available and was not durably persisted

#### Scenario: Authenticated history is account-scoped

- **GIVEN** an authenticated account with a persisted conversation
- **WHEN** another account references that conversation identifier
- **THEN** it cannot read or clear the conversation

#### Scenario: Owner lists own conversations

- **GIVEN** an authenticated account with persisted conversations
- **WHEN** it lists its conversations
- **THEN** only its own conversations are returned

### Requirement: Stream responses over SSE

The assistant SHALL stream responses to `POST /assistant/chat` as
`text/event-stream`, delivering incremental content and a terminal completion event,
with `Cache-Control: no-store`. Trace: U23.

#### Scenario: Streamed answer

- **GIVEN** a valid chat request
- **WHEN** the assistant produces an answer
- **THEN** the response is `text/event-stream` with incremental events ending in a completion event

### Requirement: Return an identifiable static fallback and refuse unsupported questions

On a provider, tool, rate-limit or empty-index failure the assistant SHALL return an
identifiable static fallback, and for an unsupported question it SHALL return an
identifiable refusal; neither SHALL invent data or expose provider keys. Trace: U23,
CU03-S02, Q07 (CU03, static fallback decided), SR06.

#### Scenario: Provider failure falls back statically

- **GIVEN** the model provider is unavailable or errors mid-stream
- **WHEN** the visitor asks a question
- **THEN** the assistant returns the identifiable static fallback without invented data or a provider key

#### Scenario: Out-of-scope question is refused

- **GIVEN** a question that no approved source supports and that is outside the guidance scope
- **WHEN** the assistant handles it
- **THEN** it returns an identifiable refusal rather than silence or a fabricated answer

### Requirement: Enforce resource limits

The assistant SHALL enforce a per-client rate limit that returns HTTP 429 with
`Retry-After` before the stream starts, first-byte and total timeouts, a message and
request-body length limit, and token, context and output limits. Trace: U23.

#### Scenario: Rate limit is exceeded

- **GIVEN** a client exceeding the chat rate limit
- **WHEN** it sends another request
- **THEN** the endpoint returns HTTP 429 with `Retry-After`

#### Scenario: Overlong message is rejected

- **GIVEN** a message exceeding the allowed length
- **WHEN** the request is made
- **THEN** it is rejected before any provider call

### Requirement: Protect the public chat endpoint without weakening authenticated policies

The public `POST /assistant/chat` SHALL be CSRF-exempt only for that endpoint and SHALL
validate the request Origin server-side with abuse protection; authenticated unsafe
operations SHALL keep their existing Origin and CSRF requirements. Trace: U23,
frontend-session-transport, AGENTS.md.

#### Scenario: Cross-origin chat request is rejected

- **GIVEN** a chat request whose Origin is not allowed
- **WHEN** it reaches the endpoint
- **THEN** the request is rejected and no provider call is made

#### Scenario: Authenticated writes keep CSRF

- **GIVEN** the existing authenticated unsafe operations
- **WHEN** they are called after this change
- **THEN** they still require the session-bound CSRF token and trusted Origin

### Requirement: Expose no writes, private records or privileged tools

The assistant runtime SHALL expose only read-only public-data tools, SHALL NOT read
CU04-CU09 private records, SHALL NOT expose provider keys or development/privileged
tools, and SHALL NOT perform business or private-record writes on the user's behalf;
owner-scoped assistant-memory persistence is permitted. Trace: CU03-R2, CU03-S03,
SR02, SR06 (Q21 is context only).

#### Scenario: Request for a write or private data

- **GIVEN** a public chat request to write data or read private account records
- **WHEN** the assistant handles it
- **THEN** it refuses and performs no write or private-record access

#### Scenario: Runtime tool set is read-only

- **GIVEN** the assistant runtime
- **WHEN** it invokes its tools
- **THEN** only read-only public-data tools are available and no development or write tool is exposed
