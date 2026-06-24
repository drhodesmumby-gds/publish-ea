# Development Control Diagrams: Model-Driven Architecture Views

## Context

The Development Control page (`ba-pd-development-control.html`) contains 9 inline SVG architecture diagrams showing anti-patterns and target states for each phase of a planning application lifecycle. These have visual issues (text overlaps, truncation, spacing) and accuracy gaps (missing Payment Gateway, GOV.UK Notify, oversimplified AI/ML flow, missing officer review checkpoints).

Rather than fixing the hand-crafted SVGs, we're replacing them with a model-driven approach that separates the architecture model (source of truth) from the visual rendering (presentation).

## Architecture

### Source of truth: Structurizr DSL

A single `.dsl` file defines the Development Control architecture model using C4 semantics:
- **Software systems**: Rules Engine, Workflow Engine, Spatial DB, EDRMS, Payment Gateway, GOV.UK Notify, Public Register, Event Broker, API Gateway, AI Extraction Service
- **External systems**: Statutory Consultees (Environment Agency, Historic England, PINS), planning.data.gov.uk, Applicant/Agent, Officer, The Public
- **Relationships**: Typed and directional (submits to, queries, publishes to, replicates from, routes to)
- **Boundaries**: Public/Presentation, Integration, Core Back-Office, External

The model uses Structurizr's view definitions to specify which elements appear in each diagram:
- One System Context view (overview)
- Per-phase Container views (showing internal components and data flows)

### Rendering: D2

D2 source files are generated from the Structurizr model via a Python script. D2 provides:
- Named, styled connections with labels
- Grouping boxes (maps to C4 boundaries)
- Layers (maps to CTO/EA views)
- Theming (GOV.UK colour palette)

### Pipeline

```
_build/_diagrams/
├── model.dsl              # Structurizr DSL — the single source of truth
├── theme.d2               # GOV.UK colour palette and font config
├── generate.py            # Reads DSL, writes D2 files, calls d2 CLI
├── views/
│   ├── overview-strategic.d2    # Generated
│   ├── overview-detailed.d2     # Generated
│   ├── p1-anti.d2              # Generated
│   ├── p1-target-strategic.d2  # Generated
│   ├── p1-target-detailed.d2   # Generated
│   └── ...                     # One per diagram variant
└── output/
    ├── overview-strategic.svg   # Rendered by d2
    ├── overview-detailed.svg    # Rendered by d2
    └── ...
```

`build.py` calls `generate.py` as part of the build. The output SVGs are referenced by the page source via `<img>` or inlined.

### Two-view toggle (CTO / EA)

Each diagram slot in the HTML contains two `<div>` elements:
```html
<div class="arch-diagram-container" data-diagram="overview">
  <div class="diagram-view diagram-view--strategic">
    <!-- strategic SVG -->
  </div>
  <div class="diagram-view diagram-view--detailed" hidden>
    <!-- detailed SVG -->
  </div>
</div>
```

A page-level toggle button switches all diagrams between views by toggling a class on the `<body>`:
```css
body.diagram-detailed .diagram-view--strategic { display: none; }
body.diagram-detailed .diagram-view--detailed { display: block; }
```

Anti-pattern diagrams don't have two views — they show the problematic state at one level only.

## Content: What the diagrams should show

### Overview diagram

**Strategic (CTO)**: System Context level. Shows:
- Applicant/Agent → Rules Engine (PlanX) → API Gateway → Workflow Engine
- Workflow Engine ↔ Spatial DB, EDRMS, Payment Gateway
- Workflow Engine → Event Broker → planning.data.gov.uk, PINS, GOV.UK Notify
- Public Register ← (async replica) ← Workflow Engine
- Statutory Consultees ↔ API Gateway
- Boundary boxes: Public-facing | Integration | Core Back-Office | External

**Detailed (EA)**: Adds:
- Data standards labels on connections (MHCLG schema, GeoJSON, OCDS)
- Officer review checkpoint between AI extraction and Workflow
- CDN/edge caching layer in front of Public Register
- Specific API protocols (REST, Webhooks, OIDC)

### Phase 1: Pre-application & Submission

**Anti-pattern**: Generic E-Form → PDF (loses structured data) + free-text address (no UPRN)

**Target Strategic**: Agent (OIDC) → Rules-as-code engine → [Geospatial API, Payment Gateway, Workflow Engine]

**Target Detailed**: Adds:
- UPRN lookup step (Gazetteer API)
- Fee calculation logic (schedule-based, pulled from planning portal)
- MHCLG schema validation before workflow ingestion
- Document upload → EDRMS (separate from structured data path)

### Phase 2: Validation & Triage

**Anti-pattern**: Officer manually redraws polygons from PDF, emails agents for missing info

**Target Strategic**: Unstructured docs → AI Extraction → [Geospatial (GeoJSON), Workflow (metadata)]

**Target Detailed**: Adds:
- Officer review checkpoint (AI outputs are *suggested*, officer confirms/amends)
- Confidence scoring on AI extraction
- Fallback: if extraction confidence < threshold → manual validation queue
- Missing info → automated GOV.UK Notify request to agent (not manual email)

### Phase 3: Consultation & Assessment

**Anti-pattern**: Public register queries contend with back-office DB; consultee PDFs sent manually

**Target Strategic**: Protected Primary DB → async read-replica → Edge Cache / Public Register; Statutory Bodies ↔ API Gateway ↔ Primary DB

**Target Detailed**: Adds:
- Neighbour notification via GOV.UK Notify (not letters)
- Statutory consultation: webhook notification to EA/HE with structured payload
- Consultation response ingestion (often unstructured — links back to Phase 2 AI extraction for processing responses)
- Statutory deadline tracking in Workflow (8-week / 13-week clock)
- Public comment moderation queue

### Phase 4: Determination & Post-Decision

**Anti-pattern**: Officer manually approves, system generates PDF notice, manual ZIP bundle emailed to PINS on appeal

**Target Strategic**: Workflow (Status: Determined) → Event Broker → [planning.data.gov.uk, PINS API, GOV.UK Notify]

**Target Detailed**: Adds:
- Decision Notice generation from structured conditions (not free-text PDF)
- Digital signing / sealing of legal notice
- Section 106 / CIL obligations → Finance system integration
- Enforcement conditions → monitoring schedule (future phase)
- Appeal bundle: automatic API transfer to PINS with full case metadata

## GOV.UK Theme for D2

```d2
# theme.d2
classes: {
  public: {
    style.fill: "#f3f2f1"
    style.stroke: "#0b0c0c"
  }
  system: {
    style.fill: "#ffffff"
    style.stroke: "#1d70b8"
    style.stroke-width: 2
  }
  system-green: {
    style.fill: "#ffffff"
    style.stroke: "#00703c"
    style.stroke-width: 2
  }
  antipattern: {
    style.fill: "#ffffff"
    style.stroke: "#d4351c"
    style.stroke-width: 2
  }
  database: {
    shape: cylinder
    style.fill: "#ffffff"
    style.stroke: "#505a5f"
  }
  boundary: {
    style.fill: "#f8f8f8"
    style.stroke: "#b1b4b6"
    style.stroke-dash: 4
  }
  external: {
    style.fill: "#f3f2f1"
    style.stroke: "#0b0c0c"
  }
}
```

## Dependencies

- **D2 CLI**: Install via `brew install d2` (macOS) or download binary. Required for SVG generation.
- **Python 3**: Already available (build.py uses it). `generate.py` parses the DSL and writes D2 files.
- **Structurizr DSL**: No runtime dependency — we parse it ourselves in Python for the subset we need (workspace, model, views). Full Structurizr CLI is NOT required.

## Verification

1. Run `python3 _build/_diagrams/generate.py` — should produce D2 files in `views/` and SVGs in `output/`
2. Run `python3 _build/build.py` — page builds with new diagram references
3. Open `preview/ba-pd-development-control.html` — verify:
   - All diagrams render (no broken images)
   - Strategic/Detailed toggle works
   - GOV.UK colour palette is consistent
   - No text truncation or overlaps
   - Relationships are readable and directional
4. Content review: check each diagram against the content spec above
5. Regression: existing pages unaffected (they don't use the diagram system)
