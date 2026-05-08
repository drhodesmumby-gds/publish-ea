# Red-team analysis: LGAM index page

## 2. The grouping principle: what's inside FT vs what's separate?

The current model puts 5 things inside Foundational Technology (Infrastructure & Hosting, AI, DevOps, End User & Productivity, Service Management) and 3 things outside it as "wider stack" layers (Integration, Security, Data & Information Technology).

**The stated distinction:** "These layers are not specific to local government." But that doesn't hold — AI, DevOps, and End-User Computing aren't specific to local government either.

**So what's the actual implicit logic?** Looking at what's inside vs outside:

| Inside FT | Outside FT |
|---|---|
| Infrastructure & Hosting | Integration |
| AI | Security |
| DevOps | Data & Info Tech |
| End User & Productivity | |
| Service Management | |

The items *inside* FT seem to share a characteristic: they're **things councils operate/own/run**. You procure cloud hosting. You buy end-user devices. You run a service desk. You might deploy AI tooling. These are assets and operational capabilities your IT team manages day-to-day.

The items *outside* seem to share a different characteristic: they're **cross-cutting concerns that constrain or connect** everything else. Integration isn't a thing you "run" the way you run a data centre — it's a property of how your systems relate. Security isn't a platform — it's a set of controls applied to everything. Data isn't a service — it flows through everything.

This maps loosely to:
- **FT = operational technology you own** (nouns: "we have cloud hosting", "we have a service desk")
- **Wider stack = architectural concerns that govern how technology works together** (verbs/adjectives: "we integrate", "we secure", "we manage data")

**But this breaks down immediately:**
- "API management and gateways" (in Integration) is definitely something you operate — you run an API gateway
- "Identity and access management" (in Security) is definitely a platform — you run Azure AD
- "Data storage and warehousing" (in Data) is absolutely infrastructure you own and operate
- "Service Management" (in FT) is arguably more of a practice/discipline than a technology platform

**The deeper tension:** the model is trying to be two things at once. The FT section describes **what councils buy and run** (a catalogue of technology assets). The wider stack sections describe **architectural disciplines** (how you approach integration, security, data). These are different types of thing, but we've put them in the same visual structure (coloured bars with expand/collapse cards), which makes them *look* equivalent when they're not.

**Possible resolutions:**

**A) Accept the current grouping but articulate the principle clearly.** Something like: "Foundational Technology describes the platforms and tools your IT team operates. The wider technology stack describes the cross-cutting disciplines that govern how those platforms work together." Then ruthlessly move anything that's an "operated platform" into FT (IAM, data warehousing, API gateway) and keep only true architectural/governance concerns in the wider stack.

**B) Flatten everything into FT as sub-domains.** Accept that the LGAM/wider distinction is internal taxonomy and doesn't help the reader. Make Integration, Security, and Data into sub-domains of Foundational Technology alongside the others. The context map simplifies. The page shortens. The grouping problem disappears.

**C) Reframe the wider stack as "disciplines" rather than "layers."** Don't call them layers at all. Call them "cross-cutting disciplines" or "architectural concerns" and present them differently — perhaps as reference guidance rather than as component catalogues. This would mean their content structure differs from FT (less "here are the cards" and more "here are the principles, patterns, and questions").

---

## 3. What IS this model?

This is the fundamental question. Right now the page is an uncomfortable hybrid:

**As an enterprise architecture model** it's incomplete — it doesn't address information architecture, application portfolio, business capability mapping, governance frameworks, or strategic alignment. EA models (TOGAF, ArchiMate) provide viewpoints, relationships, and governance mechanisms. This doesn't.

**As a technical reference model** it's too shallow — it names capabilities but doesn't describe how they compose, depend on each other, or get evaluated. A CTO can't use this to assess their estate because there's no maturity model, no dependency map, no "here's what good looks like."

**As a service delivery model** (what the LGAM originally was) it works well for the top 5 layers — you can trace a citizen interaction from channel to system. But this narrative breaks once you hit Foundational Technology, which doesn't participate in the citizen journey.

**As a procurement/market guide** it partially works — it names things councils need to buy, and the subpages link to standards and frameworks. But it doesn't tell you what to prioritise, what dependencies exist, or what maturity you need before a capability becomes relevant.

**What it actually seems to be:** a **reference taxonomy** — a shared vocabulary for talking about council technology. Its primary value is that when a council CTO, a GDS product team, a vendor, and a service manager are in a room together, they can point to the model and agree on what they're talking about. "Payments" means this. "Integration" means that. "Infrastructure & Hosting" covers these things.

**If that's the goal, then the success criteria are:**
1. Is the taxonomy complete? (Does it cover what councils actually have?)
2. Is it coherent? (Are items at consistent levels of abstraction?)
3. Is it unambiguous? (Can two people point at the same item and agree what it means?)
4. Is it useful? (Does naming and grouping things this way help people make decisions?)

**What the model is NOT (and shouldn't try to be):**
- A maturity model (that's a layer on top)
- An implementation guide (that's what subpages are for)
- A dependency map (that's what the graph view could become)
- A procurement framework (though it can inform one)

**The user need framing:**

| User | They come to this page to... | What they need from it |
|---|---|---|
| Council CTO | Understand the full scope of what they should be thinking about | Completeness, groupings that map to how they organise their team |
| GDS product team | See where their product (Payments, Notify, One Login) fits | Clear placement in the taxonomy, understanding of the council context |
| Vendor | Understand what councils need and where their product positions | Market categories, terminology alignment |
| Service manager | Understand how technology supports their service area | The service delivery layers (top 5), links to business areas |
| CDDO/policy | A coherent picture of LG technology to inform strategy | The big picture context map, coverage assessment |

This suggests the page tries to serve too many users at surface level. The context map and taxonomy serve the CTO/CDDO/policy audience. The detailed layer content serves different audiences depending on the section (service managers for the top, architects for the bottom).

---

## 4. Duplicates — are there valid distinctions?

### Monitoring & Observability

- In FT → Infrastructure & Hosting: "Infrastructure and application monitoring, alerting, log aggregation, and performance baselining"
- In FT → DevOps: "IT monitoring and observability tooling to track system health, performance, and logs across applications and infrastructure"

**Is the distinction valid?** Barely. One emphasises infrastructure monitoring (is the server up?), the other application monitoring (is the deployment healthy?). But in practice, councils use the same tools (Datadog, Azure Monitor, Grafana) for both. This is a false split driven by copying the DCM's domain separation. **Verdict: merge into one place.**

### Identity and Access Management

- In Security layer: "Capabilities to verify identities and control access to systems... SSO, MFA..."
- Previously in our content plan as FT → Platform & Infrastructure: "Staff SSO, MFA, directory services, privileged access management"
- In LGAM Capabilities layer: "Identity" — "Councils use identity tools to check and verify who a user is"

**Is the distinction valid?** Yes — but it needs articulating:
- *Citizen identity* (the Capabilities layer "Identity" item) = verifying a citizen is who they say they are (One Login, face-to-face ID checks). This is a service delivery concern.
- *Staff IAM* (the Security/FT concern) = controlling which employees can access which systems. This is an operational security concern.

The problem is that both currently just say "identity" without making this distinction clear. **Verdict: valid split, but needs explicit labelling** ("Citizen identity verification" vs "Staff identity and access management").

### Data integration and pipelines

- In Integration layer: "Tools and processes for extracting, transforming, and loading data between systems"
- In Data & Info Tech layer: "Data storage and warehousing" — "providing scalable databases, data warehouses, and data lakes"

**Is the distinction valid?** Yes — these are genuinely different:
- Integration is about *moving data between systems* (the pipes)
- Data & Info Tech is about *storing and querying data* (the containers)

ETL/ELT sits at the boundary — it's both an integration pattern and a data management activity. But the tools are different (MuleSoft/NiFi for integration vs Snowflake/Azure Synapse for warehousing). **Verdict: valid split, but ETL/ELT should live in one place with a cross-reference to the other.**

### Geospatial

- In Data & Info Tech layer: "Data for mapping, geospatial analysis, and location based services" (very thin)
- In our adult-social-care subpage: richer treatment linking to GeoPlace, LLPG, OS data
- Not mentioned in FT or Integration despite being a platform councils operate AND an integration challenge

**Is the distinction valid?** Geospatial is genuinely cross-cutting — it's data (the datasets), platforms (ESRI ArcGIS, QGIS), and integration (LLPG/UPRN as a common key). Putting it only in Data & Info Tech is reductive. **Verdict: either give it its own sub-domain or acknowledge it as cross-cutting with a richer description.**

### Physical security and access control

- In Security layer: "badge access systems, CCTV surveillance, and facility security controls"
- Not obviously a *technology architecture* concern — this is building management

**Is this in scope?** Questionable. The model is about digital/IT technology. Physical security is facilities management. Yes, badge systems integrate with IAM, and CCTV is increasingly IP-based. But by this logic, you'd also include building management systems, fire alarms, and lifts. **Verdict: borderline — consider removing or reframing as "physical-digital convergence" if it stays.**

---

## 5. What could a council voice usefully look like?

The risk with "council voice" is that it becomes patronising ("councils should think about...") or anecdotal ("many councils find that..."). The service delivery layers avoid this because they describe *what councils actually do* — the content is inherently council-contextual.

For the wider stack, a useful council voice would add value in three specific ways:

### A) Name the council-specific pain points that make this capability matter.

Generic: "API management platforms for designing, publishing, securing, and monitoring APIs."

Council-voiced: "API management platforms for designing, publishing, securing, and monitoring APIs. In local government, most core system vendors (Civica, Capita, NEC) offer limited or inconsistent API support, making a managed API layer particularly important for councils with multi-vendor estates."

The addition is one sentence that tells you *why this matters more or differently for a council* than for a generic enterprise. Not every item needs it — only where the council context genuinely changes the picture.

### B) Flag where the council scale/context changes the typical approach.

Generic: "Security Operations Centre (SOC) capabilities... SIEM tools and threat detection platforms."

Council-voiced: "Security Operations Centre (SOC) capabilities... Most councils (particularly districts and boroughs) lack the scale to operate an in-house SOC and instead procure managed SOC services, often shared with neighbouring authorities or through regional partnerships."

This tells a council CTO: "you're not expected to build this yourself" — which is genuinely useful guidance that a generic enterprise model wouldn't give you.

### C) Connect to the council governance/accountability structure.

Generic: "Data governance and quality — tools for managing data assets consistently and ethically."

Council-voiced: "Data governance and quality — tools and processes for managing data assets consistently and ethically. In councils, data governance intersects with democratic accountability: elected members and scrutiny committees increasingly expect transparency about what data is held, how it's used, and who has access."

This surfaces the *democratic dimension* that is unique to local government and absent from private-sector or central-government models.

### Where NOT to add council voice:
- Don't add it to items where the council context is identical to any other organisation ("Data storage and warehousing" — councils use the same databases everyone else does)
- Don't add it where it would just be stating the obvious ("End-user devices — councils give staff laptops" — yes, everyone does)
- Don't add it where the pain point is universal ("Vulnerability management" — everyone needs to patch, this isn't a council-specific challenge)

**The test:** would a council CTO read this sentence and think "yes, that's specifically true for us in a way it isn't for, say, an NHS trust or a central government department"? If yes, include it. If no, the generic description is fine.
