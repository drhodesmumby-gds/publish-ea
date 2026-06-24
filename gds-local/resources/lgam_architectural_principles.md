# LGAM Architectural Principles: What Good and Bad Look Like

This document captures the highest-level architectural opinions expressed across the Local Government Architecture Model (LGAM). It serves as a consistency checklist for authoring new patterns, target state diagrams, and business area architectures.

## 1. Common Architectural Rules (Cross-Domain)

These principles apply universally across the LGAM, whether evaluating a specific council department's software footprint or designing cross-boundary data shares.

### Technical Boundaries & Gateway Topology

Where an API Gateway sits depends on the relationship between the organisations involved.

* **GOOD - Internal Decoupling (within a single organisation):** The API Gateway sits between the "Public / Presentation" tier (e.g. citizen-facing web portals, forms engines) and the "Core Back-Office" tier. It acts as an internal boundary ensuring the back-office is never directly exposed to the public internet. *(See: Planning Development Control target state.)*
* **GOOD - Cross-organisational exchange (Consumer ↔ Controller):** When one organisation (the Consumer) requests data held by another (the Controller), there should ideally be an API Gateway on both sides. The Consumer's outbound gateway manages credential lifecycle, provides a single auditable egress point for all external data requests leaving the organisation, and logs what was requested and received. The Controller's inbound gateway validates tokens, enforces rate limits and schema constraints, and generates immutable audit logs before forwarding validated requests into the Controller's internal network. Trust between the two gateways is established by registering the Consumer's Identity Provider with the Controller's gateway — this is a configuration, not a separately deployed component. Neither organisation's internal systems are directly exposed to the other. *(See: statutory_sharing_pattern.html SVG diagram.)*
* **GOOD - Shared infrastructure for multi-agency event routing:** When multiple agencies (e.g. Council, NHS Trust, Police) need to exchange events for safeguarding or shared care, the event broker and identity resolution engine should sit in shared infrastructure (e.g. a regional shared care record platform, or a jointly-governed cloud tenant) rather than hosted inside any single agency's network perimeter. This is appropriate for *asynchronous event routing* specifically; synchronous API queries between two agencies should still follow the Consumer ↔ Controller pattern above. *(See: Inter-authority partner sharing diagram.)*
* **BAD - Blurred boundaries:** Placing the API Gateway inside the Controller's core back-office boundary rather than at the organisational edge. This means internal systems are directly addressable from outside and the gateway cannot perform its trust-enforcement role before traffic hits internal services.
* **BAD - No boundary at all:** Allowing Organisation A to connect directly to Organisation B's database or internal microservices without any intermediary gateway or trust assertion layer.

### Integration & Decoupling
* **GOOD:** Systems are decoupled using a combination of Event Brokers for *internal* asynchronous routing and fan-out, and API Gateways for *external* egress/ingress and synchronous RESTful endpoints. The two mechanisms are complementary (e.g. an internal event triggers an integration service that pushes data out through the API Gateway boundary).
* **BAD:** Point-to-point "spaghetti" integrations directly connecting line-of-business applications. Relying on shared databases where multiple systems read/write to the same operational tables.
* **BAD:** Using Robotic Process Automation (RPA) as a permanent architectural solution to bridge systems that lack proper APIs.

### Data Flow & Payloads
* **GOOD:** Event-driven architectures utilising JSON payloads and webhooks to notify downstream systems of delta changes (e.g. "Household income changed").
* **GOOD:** Targeted, synchronous REST API calls to retrieve specific derived data points (e.g. `isEligible: true`) rather than pulling bulk datasets.
* **ACCEPTABLE DEVIATION:** Scheduled bulk transfers (CSV/XML) via SFTP when mandated by external bodies (e.g. Central Government departments) that lack modern API or webhook capabilities for critical functions or duties.
* **BAD:** Relying on legacy batch processing, manual CSV extracts, or nightly bulk dumps of entire datasets (e.g. 50,000 rows) *when synchronous APIs or webhooks are available and appropriate* for the consuming use case.

### Identity & Access Management (IAM)
* **GOOD:** Federated Identity (OAuth 2.0 / OIDC / SAML) providing Single Sign-On (SSO) for staff, external partners, and high-frequency agents. Access to data is gated by Role-Based (RBAC) or Attribute-Based Access Control (ABAC). Tokens must be short-lived and cryptographically signed using established formats (e.g. JWT, PASETO). If using JWT, gateways must explicitly enforce the expected signing algorithm to prevent cryptographic downgrade attacks.
* **GOOD:** Every API request carries a token that explicitly identifies the individual user *and* their professional role, enabling per-request audit trails.
* **BAD:** Siloed, system-specific local credential management forcing users to maintain multiple logins across the council estate.
* **BAD:** Hardcoded service accounts with static passwords shared between organisations, never rotated, offering no visibility into which individual end-user triggered a query.
* **BAD:** IP whitelisting as the sole access control mechanism for cross-organisational data exchange.

### Data Minimisation & Derived Data
* **GOOD:** Architectures should support exposing *derived* data (e.g. "Is over 65: True") rather than raw data (e.g. "Date of Birth: 12/04/1958") wherever the consuming use case permits it. This fulfils the UK GDPR data minimisation principle technically, not just procedurally.
* **BAD:** Returning entire raw records (e.g. full financial history, full care record) when the consumer only needs to verify a single eligibility criterion.

### Governance Sequencing
* **GOOD:** Legal basis and information governance must be established *before* any technical integration is built. The architecture must explicitly trace back to a documented lawful basis (e.g. DEA 2017 Part 5 gateway, UK GDPR public task) before data flows commence.
* **BAD:** "Build first, govern later" — IT teams building APIs or automated transfers because an operational team requested them, with the Information Governance team only discovering the pipeline during an audit or a breach.
* **BAD:** Relying on broad "implied consent" buried in the council's privacy notice to share data with third parties, rather than utilising explicit statutory gateways.

### Audit & Accountability
* **GOOD:** Immutable, timestamped audit logs recording every data access event, tied to the specific user-assertion (not just a service account). Logs are stored in a SIEM or equivalent immutable store to satisfy Subject Access Requests (SARs) and ICO investigations.
* **BAD:** No audit trail, or audit logs that only record the service account used rather than the individual end-user who triggered the query.

### Data Cataloguing & Discoverability
* **GOOD:** Shared data assets are described in catalogues conforming to the Cross-Government Metadata Exchange Model (DCAT v3). API schemas are published as machine-readable OpenAPI 3 specifications. Consuming developers can auto-generate client code from the spec.
* **BAD:** Schemas agreed via email or spreadsheet with no machine-readable definition. When the source system upgrades and a column changes, downstream integrations break silently.

### Master Data, State, & Standards
* **GOOD:** Utilising Master Data Management (MDM) for identity resolution to create "Golden Records". Adopting national identifiers (UPRN for property, NHS Number for health) and open data standards (Open311, Open Referral UK).
* **GOOD:** Explicitly defining the System of Record (SoR) for each data domain. State replication across systems is minimised and explicitly managed (e.g., via event streams) rather than relying on ambiguous two-way syncs.
* **BAD:** Inventing proprietary data schemas or local data models when a national or open standard already exists for that domain.
* **BAD:** Deterministic exact-string matching for citizen records (e.g. demanding exact First Name, Last Name, DOB matches), which fails to account for typos, aliases, or missing data and causes high rates of false negatives.
* **BAD:** Ambiguous data ownership where multiple systems claim to hold the "master" record, leading to untraceable data drift.
### Security & Infrastructure
* **GOOD:** Cloud-first (or hybrid) hosting leveraging public cloud platforms (Azure, AWS) with Internet-first connectivity and Zero-Trust network models (post-PSN).
* **GOOD:** Mutual TLS (mTLS) for machine-to-machine authentication at organisational boundaries, combined with OAuth 2.0 token validation for user-level authorisation.

### Resilience & Observability
* **GOOD:** Designing for failure by including Dead Letter Queues (DLQs) for asynchronous events, explicit retry mechanisms for synchronous APIs, and system health monitoring.
* **BAD:** Architecting only for the "happy path" with no defined error handling or alerting when external integrations fail.

---

## 2. Domain-Specific Rules

These principles represent specific applications of the common rules within distinct business or functional domains.

### Data Sharing & Information Governance
* **GOOD:** Utilising scalable Information Governance frameworks (like SAVVI) to standardise DPIAs and DSAs across similar purposes.
* **GOOD:** DSAs that explicitly mandate the technical *Assertion* mechanism (e.g. OAuth 2.0 federation) and *Role* requirements, not just the legal basis and data items.
* **BAD:** Over-sharing raw operational records or entire case histories across multi-agency boundaries.
* **BAD:** Point-to-point justification; drafting bespoke DPIAs and DSAs from scratch for every minor data share between the same agencies.

### Planning & Development (Development Control)
* **GOOD:** Decoupling the citizen/agent-facing submission portal from the transactional back-office using a Rules Engine API, with the API Gateway sitting in an "Integration" zone between them.
* **GOOD:** Using Machine Learning to parse unstructured attachments (like PDF site plans) into structured geospatial and metadata payloads at the point of ingestion.
* **BAD:** Manual polygon drawing by council officers, manual fee calculation, and manual re-keying of application data from portal PDFs.
* **BAD:** Generating zipped email exports and static PDFs to execute statutory consultations, rather than triggering automated egress to external APIs via the internal Event Broker and external API Gateway.

### Adult Social Care & Multi-Agency Partnerships
* **GOOD:** Event-driven shared infrastructure (e.g. a "Data Trust") providing a unified, read-only Shared Care Record view of a citizen's interactions across the local partnership (Council, NHS, Police) using pub/sub brokers and identity resolution engines.
* **BAD:** Manually downloading updates from the CQC provider register or health partners and running scripts to patch the local adult social care database.
