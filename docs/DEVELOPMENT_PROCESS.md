# FireScope AI — Development Process and Project Management

**Project:** FireScope AI / Bushfire AI  
**Course:** ICT313  
**Project type:** Individual full-stack machine learning application  
**Evidence basis:** Git history provided on 19 October 2026, inspected source code, and project functionality discussed during development.

## 1. Purpose

This document describes how FireScope AI progressed from an initial data-processing and neural network prototype to a deployed, user-facing bushfire risk assessment application. It records verifiable milestones, the iterative development approach, technical decisions, engineering challenges, and remaining work. It does not claim that formal Scrum ceremonies, fixed-length sprints, or comprehensive testing took place unless independently evidenced.

## 2. Development Approach

Development followed an **iterative, prototype-driven approach**. Early work focused on assembling data and demonstrating a prediction pipeline. Later iterations extended the model experiments, developed the web interface, connected the backend, prepared deployment, and added user-facing capabilities.

The project was undertaken individually. AI-assisted tools were used as development support; responsibility for project decisions, integration, verification, and submission remained with the student developer. The available Git record demonstrates checkpoints, but does not establish how many hours were spent or the exact date of every intermediate task.

## 3. Evidence-Based Timeline

The table below records **commit dates**, not necessarily the dates when all associated work began or was finished.

| Date (2026) | Git reference | Recorded milestone | Significance |
|---|---|---|---|
| 18 Aug | `0a9e0ec` | Initial data pipeline and PyTorch prototype | Established an early machine learning foundation. |
| 19 Aug | `28edde6` | Live bushfire risk prediction dashboard | Connected model-oriented functionality with a user interface. |
| 16 Sep | `d33c87d` | V07 dataset and geospatial pipeline checkpoint | Preserved a substantial dataset and geographic-processing iteration. |
| 23 Sep | `0cfd60e` | Node application prepared for production deployment | Advanced server-side hosting readiness. |
| 30 Sep | `0f6798a` | Replaced OpenStreetMap tiles with MapTiler | Changed the mapping implementation. |
| 30 Sep | `d5b834a` | Leaflet marker icon fix | Addressed a mapping presentation issue at that stage. |
| 6 Oct | `3042083` | Working 2D MapTiler dashboard checkpoint | Recorded a functional mapping milestone. |
| 8 Oct | `45d35e7` | README improvements | Documented architecture, model, and deployment information. |
| 14 Oct | `95e979f` | Dashboard, fire warnings, and ML experiments | Consolidated major application and research changes. |
| 14 Oct | `ef5b506` | Climate news RSS integration | Added environmental news content. |
| 14 Oct | `77d11d7` | Interactive risk map and location comparison | Extended geographic assessment functionality. |
| 14 Oct | `237c0c9` | Authentication, risk tools, and contact system | Expanded the application beyond basic predictions. |
| 14 Oct | `8bbe3fc` | Email authentication and account verification | Extended identity management. |
| 14 Oct | `d831984` | Stopped tracking developer profile photo | Reduced ongoing inclusion of a personal image in Git tracking. |

**Interpretation:** Multiple commits on 14 October show a concentrated integration/checkpoint period. They should not be interpreted as proof that all the underlying features were designed and developed in a single day.

## 4. Development Phases

### Phase 1 — Problem exploration and initial prototype

The project began by exploring how weather-related observations and machine learning could support educational bushfire risk assessment. Initial deliverables included data-processing code and a PyTorch prototype, followed by an early dashboard. The Git history places these checkpoints on 18–19 August 2026.

### Phase 2 — Data engineering and model experimentation

The repository contains scripts for dataset preparation, weather enrichment, vegetation and elevation processing, balanced or matched control generation, model comparison, ablation, and evaluation. It also contains saved neural network and Random Forest artifacts, plus temporal-model experiments.

The presence of these files demonstrates a substantial experimentation workflow; it does **not**, by itself, prove that every experiment succeeded or that every artifact was used in production. Model-specific results should be cited only after inspecting the corresponding outputs.

### Phase 3 — Backend integration and deployment preparation

The application adopted a Node.js/Express backend. For predictions, the backend launches `src/predict_api.py` using a Python child process, passing geographic coordinates and reading a JSON result. A September commit records production deployment preparation.

This approach reused the Python inference code while allowing Express to serve the web application and handle additional endpoints. The trade-off is that each prediction request starts a Python process, potentially affecting latency and concurrent-request capacity.

### Phase 4 — Geographic interface improvements

Mapping changed during development, including a recorded move to MapTiler and subsequent dashboard refinement. The project now uses geographic interaction to support location-based risk exploration.

Earlier commits referring to Leaflet do not necessarily describe the current mapping implementation; architecture documentation should reflect the code currently in use.

### Phase 5 — Feature expansion and user accounts

The October Git history records integration of climate news, fire warnings, interactive risk mapping, authentication, contact functionality, and account verification. Inspected source code also shows Firebase-backed prediction history and saved locations.

The NSW Rural Fire Service incident feed is handled separately from the experimental model output, helping distinguish official incident information from AI-generated risk estimates.

### Phase 6 — Documentation and assessment preparation

Following the application and presentation work, project documentation was organised into topic-specific Markdown files under `docs/`. These documents address project scope, requirements, architecture, database design, machine learning, development process, testing, user guidance, deployment, security, limitations, and future work.

Documentation completeness and software verification are separate matters: a written feature description is not evidence of a passed test.

## 5. Project Organisation and Version Control

Git was used to preserve project milestones and track changes. The supplied log shows an initial commit on 18 August and later checkpoints through 14 October 2026. The repository uses descriptive commit messages for many significant changes, including mapping, deployment, authentication, and documentation.

At the time of the supplied `git status --short` output, the working tree contained **uncommitted modifications** to:

- `frontend-react/src/App.jsx`
- `frontend-react/src/components/Header.jsx`
- `frontend-react/src/components/Header.css`
- `frontend-react/src/pages/Contact.jsx`

The `docs/` directory was also **untracked**. These changes are not yet established as part of the committed Git history. Their exact functionality and production deployment status must be verified separately before submission claims are finalised.

## 6. Key Engineering Decisions

| Decision | Reason or practical benefit | Trade-off / consideration |
|---|---|---|
| React and Vite frontend | Component-based UI and production build workflow | Requires frontend build and deployment coordination. |
| Express backend | Centralised HTTP endpoints and static serving | API reliability depends on Node runtime and configuration. |
| Python process invocation for inference | Reuses PyTorch pipeline without another HTTP service | Process startup and concurrency overhead. |
| Firebase Authentication and Firestore | Supports accounts and user-specific records | Access control depends on correctly configured security rules. |
| MapTiler-based maps | Supports geographic exploration | External service availability and configuration dependency. |
| NSW RFS incident feed | Adds official incident context | NSW-specific coverage; feed availability is external. |
| Topic-specific Markdown documentation | Makes technical evidence easier to navigate and maintain | Documents must be kept consistent with evolving code. |

## 7. Technical Challenges and Responses

### Integrating different programming environments

The application combines browser-based JavaScript, a Node.js server, and Python/PyTorch. The solution uses a defined prediction endpoint and JSON exchange between Node and Python. This avoids embedding machine learning logic directly in the frontend.

### Managing geographic data and external services

Location-based predictions require coordinates and environmental data. Mapping and weather services introduce dependencies outside the project's control. The backend and interface need to handle unsuccessful requests without displaying fabricated results.

### Evolving the mapping interface

The Git history records a move from earlier map tiles to MapTiler, plus further dashboard refinement. This illustrates iterative replacement and improvement rather than a single fixed design.

### Balancing model research with product delivery

The repository contains numerous experimental models and datasets, while the inspected production inference path loads `models/bushfire_model_v04.pth`. Keeping experiments separate from the deployed model helps prevent misleading descriptions of production behaviour.

### Preserving safety distinctions

Official incident reports and experimental risk predictions serve different purposes. The application must make clear that its model outputs are not official warnings or evacuation advice.

### Privacy and repository hygiene

A commit records the decision to stop tracking a developer profile photo. Stopping future tracking does not necessarily remove the file from older Git history. A history audit would be required before claiming complete removal.

## 8. Quality Assurance and Verification

The development record shows implementation and iteration, but does not provide a complete formal test log. Consequently, this document does not claim that all functional or non-functional requirements have passed.

The separate testing report should connect requirements to reproducible procedures, observed outcomes, dates, environments, and evidence. Priority areas include prediction error handling, Firebase user-data isolation, mapping, incident-feed failures, mobile responsiveness, and production behaviour.

## 9. Individual Contribution and AI-Assisted Development

The project was developed as an approved individual academic project. The student developer coordinated the problem definition, integration of components, selection of features, iterative changes, repository maintenance, and project delivery. AI assistance supported aspects of the development and documentation workflow.

Specific contribution claims should be supported by project records and should not imply that every code line was written without assistance. Any required institutional AI-use declaration should be completed in accordance with course guidance.

## 10. Current Status and Outstanding Work

Based on the supplied evidence, the application has a deployed public address, a documented source repository, and an implemented production inference path. The following remain important documentation and verification tasks:

1. Record test cases and actual observed results.
2. Verify Firestore security rules and account isolation.
3. Verify current deployment configuration and whether uncommitted changes are deployed.
4. Reconcile README model-feature descriptions with the 15 features in `src/predict_location.py`.
5. Confirm numerical model evaluation results before publishing performance claims.
6. Review documentation links and package the required academic submission format.

These are **remaining checks**, not claims that the features are broken.

## 11. Lessons and Process Reflection

The Git timeline illustrates how a small prototype can grow into a multi-layer application through successive checkpoints. The project also shows the importance of separating experimental research from production behaviour, tracking external dependencies, and recording the evidence behind technical claims.

A future iteration would benefit from a more explicit issue backlog, milestone acceptance criteria, automated tests, and regular documentation updates alongside code changes.

## 12. Supporting Documents

- [Project Overview](PROJECT_OVERVIEW.md)
- [Requirements](REQUIREMENTS.md)
- [Architecture](ARCHITECTURE.md)
- [Machine Learning](MACHINE_LEARNING.md)
- [Testing](TESTING.md)
- [Deployment](DEPLOYMENT.md)
- [Security](SECURITY.md)
- [Limitations](LIMITATIONS.md)
- [Roadmap](ROADMAP.md)

---

**Evidence limitation:** This document is grounded in the Git output and code excerpts supplied during documentation preparation. It is not a substitute for an independently audited development diary, a verified production release log, or a formal testing report.
