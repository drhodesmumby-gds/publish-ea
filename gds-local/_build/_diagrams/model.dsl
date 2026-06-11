workspace "Development Control" "Target architecture for the planning application lifecycle" {

    model {
        # Actors
        applicant = person "Applicant / Agent" "Citizens, architects, or planning agents submitting applications"
        officer = person "Officer" "Council planning officer performing validation, assessment, and determination"
        public = person "The Public" "Members of the public viewing the planning register and submitting comments"
        statutoryBodies = softwareSystem "Statutory Consultees" "Environment Agency, Historic England, Highways, etc." "external"

        # Core systems
        rulesEngine = softwareSystem "Rules Engine" "Dynamic rules-as-code frontend (e.g. PlanX) for intelligent application submission" "system-green"
        apiGateway = softwareSystem "API Gateway" "Central integration layer routing requests between presentation and back-office" "integration"
        workflowEngine = softwareSystem "Workflow Engine" "Core case management system managing statutory timelines, tasks, and determination (e.g. BOPS)" "system"
        spatialDb = softwareSystem "Spatial Database" "UPRN/USRN gazetteer, site boundaries, constraint polygons, local plan designations" "database"
        edrms = softwareSystem "EDRMS" "Document and records management for plans, drawings, decision notices, correspondence" "database"
        paymentGateway = softwareSystem "Payment Gateway" "Fee calculation and collection (GOV.UK Pay or council payment platform)" "system"
        publicRegister = softwareSystem "Public Register" "Edge-cached read-replica serving the public planning register" "system-green"
        eventBroker = softwareSystem "Event Broker" "Pub/sub system firing events on status changes (e.g. determined, appealed)" "system"
        aiExtraction = softwareSystem "AI Extraction" "Computer vision + LLM pipeline extracting structured data from unstructured PDFs (e.g. i.AI Extract)" "system"
        notify = softwareSystem "GOV.UK Notify" "Government notification service for emails, letters, and SMS" "external"

        # External endpoints
        planningData = softwareSystem "planning.data.gov.uk" "MHCLG national planning data platform" "external"
        pins = softwareSystem "PINS" "Planning Inspectorate appeals system" "external"

        # Phase 1 relationships: Pre-application & Submission
        applicant -> rulesEngine "Submits application via" "HTTPS / OIDC"
        rulesEngine -> spatialDb "Queries constraints, UPRN lookup" "REST API / GeoJSON"
        rulesEngine -> paymentGateway "Calculates and collects fee" "REST API"
        rulesEngine -> apiGateway "Sends structured JSON payload" "REST / MHCLG schema"
        apiGateway -> workflowEngine "Creates case record" "REST API"
        applicant -> edrms "Uploads supporting documents" "HTTPS"

        # Phase 2 relationships: Validation & Triage
        edrms -> aiExtraction "Sends unstructured PDFs for processing" "Internal API"
        aiExtraction -> spatialDb "Outputs GeoJSON site boundary" "REST API"
        aiExtraction -> workflowEngine "Outputs structured metadata (suggested)" "REST API"
        officer -> workflowEngine "Reviews AI suggestions, confirms/amends" "UI"
        workflowEngine -> notify "Requests missing info from agent" "REST API"

        # Phase 3 relationships: Consultation & Assessment
        workflowEngine -> publicRegister "Replicates case data asynchronously" "Event / CDC"
        public -> publicRegister "Views applications, submits comments" "HTTPS"
        workflowEngine -> apiGateway "Sends consultation requests" "REST API"
        apiGateway -> statutoryBodies "Routes structured consultations" "Webhooks / REST"
        statutoryBodies -> apiGateway "Returns consultation responses" "Webhooks / REST"
        workflowEngine -> notify "Sends neighbour notifications" "REST API"

        # Phase 4 relationships: Determination & Post-Decision
        officer -> workflowEngine "Records determination decision" "UI"
        workflowEngine -> eventBroker "Fires determination event" "Pub/Sub"
        eventBroker -> planningData "Publishes structured decision" "REST / MHCLG schema"
        eventBroker -> pins "Transfers appeal bundle" "REST API"
        eventBroker -> notify "Triggers decision notification" "REST API"
    }

    views {
        systemContext workflowEngine "overview-strategic" "Strategic overview of Development Control architecture" {
            include *
            exclude aiExtraction
            exclude officer
        }

        systemContext workflowEngine "overview-detailed" "Detailed overview including AI extraction and officer checkpoints" {
            include *
        }

        systemContext rulesEngine "p1-target-strategic" "Phase 1: Submission target architecture (strategic)" {
            include applicant rulesEngine spatialDb paymentGateway apiGateway workflowEngine edrms
        }

        systemContext rulesEngine "p1-target-detailed" "Phase 1: Submission target architecture (detailed)" {
            include applicant rulesEngine spatialDb paymentGateway apiGateway workflowEngine edrms
        }

        systemContext aiExtraction "p2-target-strategic" "Phase 2: Validation target architecture (strategic)" {
            include edrms aiExtraction spatialDb workflowEngine
        }

        systemContext aiExtraction "p2-target-detailed" "Phase 2: Validation target architecture (detailed)" {
            include edrms aiExtraction spatialDb workflowEngine officer notify
        }

        systemContext workflowEngine "p3-target-strategic" "Phase 3: Consultation target architecture (strategic)" {
            include workflowEngine publicRegister public apiGateway statutoryBodies
        }

        systemContext workflowEngine "p3-target-detailed" "Phase 3: Consultation target architecture (detailed)" {
            include workflowEngine publicRegister public apiGateway statutoryBodies notify
        }

        systemContext eventBroker "p4-target-strategic" "Phase 4: Determination target architecture (strategic)" {
            include workflowEngine eventBroker planningData pins notify officer
        }

        systemContext eventBroker "p4-target-detailed" "Phase 4: Determination target architecture (detailed)" {
            include workflowEngine eventBroker planningData pins notify officer edrms
        }
    }
}
