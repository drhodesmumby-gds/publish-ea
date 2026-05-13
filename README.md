# PublishEA – OCTO Architecture Resources

## Overview

PublishEA provides a centralised collection of **enterprise architecture resources, guidance, templates, and frameworks** to be used by public sector architecture community.

The repository supports the discovery, reuse, and continuous improvement of architectural artefacts across the **wider UK Government digital ecosystem**.

---

## Contents

- [Overview](#overview)
- [Purpose](#purpose)
- [Intended Audience](#intended-audience)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Reusing These Resources](#reusing-these-resources)
- [Development Guidelines](#development-guidelines)
- [Design Standards](#design-standards)
- [Contributing](#contributing)
- [Suggesting Improvements](#suggesting-improvements)
- [Current Status](#current-status)
- [Deployment](#deployment)
- [Expected Outcomes](#expected-outcomes)
- [License](#license)
---

## Purpose

The purpose of this repository is to:

* Provide **reusable enterprise architecture resources**
* Improve **discoverability of architecture guidance**
* Support **consistent architecture practices**
* Enable **collaboration across architecture teams**

PublishEA acts as a **shared reference library for architecture artefacts and supporting materials**.

---

## Intended Audience

This repository is intended for:

* Enterprise Architects
* Solution Architects
* Technical Architects
* Digital and platform teams
* Programme delivery teams working on Digital capabilities

Resources can be **reused and adapted by teams across government services and programmes**.

---

## Key Features

* Centralised architecture resource library
* Domain-specific architectural guidance
* Capability models and frameworks
* Reusable templates and supporting artefacts
* GOV.UK design standard compliant presentation

---

## Repository Structure

| Directory/File              | Description                                                                   |
| --------------------------- | ----------------------------------------------------------------------------- |
| `index.html`                | Main landing page providing navigation to architectural domains and resources |
| `AI-Technology-Enablement/` | AI technology guidance, strategy, governance, and implementation frameworks   |
| `citizen-architecture/`     | Citizen-centric architecture guidance and supporting content                  |
| `digital-capability-model/` | Digital capability framework and maturity assessment resources                |
| `downloads/`                | Templates, documents, and downloadable artefacts                              |
| `images/`                   | Visual assets including diagrams, icons, and illustrations                    |

---

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/govuk-digital-backbone/publish-ea.git
```

### Run Locally

1. Clone the repository.
2. Navigate to the project directory.
3. Open `index.html` in a web browser.

This will load the **OCTO Architecture Resources landing page**.

---

## Reusing These Resources

The content and materials in this repository are **intended to be reused and adapted** by architecture and delivery teams.

You are encouraged to:

* Reuse architecture patterns and reference models
* Adapt templates for your projects or services
* Copy components or content into your own documentation
* Extend the frameworks with domain-specific guidance

Where possible, please **retain attribution or link back to this repository** when reusing materials.

---

## Development Guidelines

When adding or updating resources:

* Place content in the appropriate **domain directory**
* Add images to the `/images` directory
* Upload downloadable artefacts to `/downloads`
* Update navigation links if new pages are introduced
* Ensure pages render correctly across desktop and mobile

---

## Design Standards

This project follows **GOV.UK design standards**.

Key components include:

* **GOV.UK Frontend CSS framework**
* **GDS Transport font family**
* **GOV.UK colour palette** (Primary: `#1d70b8`)
* **Responsive design patterns**

Reference: [GOV.UK Design System](https://design-system.service.gov.uk/)

---

## Contributing

Contributions are welcome from architecture and delivery teams.

You can contribute by:

* Adding new architecture resources
* Improving existing guidance
* Fixing documentation or navigation
* Updating diagrams or supporting materials

### Contribution Workflow

#### 1. Fork the Repository

Create your own fork of the repository.

#### 2. Create a Branch

```bash
git checkout -b feature/add-new-architecture-resource
```

#### 3. Make Your Changes

Examples:

* Add architecture content to a domain directory
* Upload templates to `/downloads`
* Add diagrams to `/images`

#### 4. Commit Your Changes

```bash
git commit -m "Add service architecture blueprint template"
```

#### 5. Submit a Pull Request

Open a Pull Request describing:

* What was added or changed
* Why the change is useful
* Any supporting references or documentation

All contributions will be reviewed before merging.

---

## Suggesting Improvements

If you have suggestions for improvements but do not want to submit a Pull Request, you can:

1. Open a **GitHub Issue**
2. Describe the proposed improvement or resource
3. Include any supporting context or references

Examples of suggestions:

* New architecture patterns
* Additional templates
* Improvements to navigation or structure
* Capability model updates

---

## Current Status

This repository is currently in **Proof of Concept (PoC)** phase.

Content, structure, and navigation may evolve as the architecture community provides feedback.

---

## Deployment

The site is deployed using **GitHub Pages** and the domain specified in the `CNAME` file.

Deployment occurs automatically when changes are merged into the main branch.

---

## Expected Outcomes

PublishEA aims to deliver:

* A **central architecture resource platform** for the public sector
* Improved **discoverability of architectural guidance**
* Clear **capability visibility through coverage heatmaps**
* Standardised **presentation of EA content**
* A collaborative **architecture knowledge base**

---

## License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for details.
