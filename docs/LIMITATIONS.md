# FireScope AI — Limitations and Constraints

**Project:** FireScope AI (Bushfire AI)  
**Context:** ICT313 Project Solution  
**Status:** Current implementation review, October 2026

## 1. Purpose and scope

This document identifies the boundaries, uncertainties, and known gaps of FireScope AI. The application is an educational prototype combining a machine-learning risk estimate, location-based weather information, map visualisation, selected public incident information, and account-based features. It is **not** a certified bushfire forecasting system, emergency alert service, or substitute for official advice.

Statements below distinguish **observed implementation behaviour** from **unverified operational assumptions**. A feature appearing in source code does not prove it has been tested under all conditions.

## 2. Summary of limitations

| ID | Area | Current limitation | Consequence | Priority |
|---|---|---|---|---|
| L01 | Interpretation | Model output is an application-defined score, not a calibrated probability of a bushfire | Users could mistake a score for a real-world likelihood | Critical |
| L02 | Emergency decisions | AI classifications are not official Australian Fire Danger Ratings or warnings | Dangerous reliance during an emergency | Critical |
| L03 | Validation | Production V04 model metrics have not been verified in this documentation review | Predictive performance cannot be quantified reliably | High |
| L04 | Generalisation | Performance across regions, seasons, and rare severe events is not established | Potentially inconsistent estimates | High |
| L05 | Weather | Forecasts and recent weather depend on external data availability and quality | Predictions may fail or use imperfect inputs | High |
| L06 | Incident coverage | Incident integration uses NSW RFS major-incidents feed | Does not provide comprehensive Australian coverage | High |
| L07 | Incident completeness | Major-incident feeds may omit smaller, emerging, or unreported events | Absence of a marker does not mean absence of danger | Critical |
| L08 | Coordinates | Backend checks numeric types but not finite values or geographic ranges | Invalid coordinates can reach Python/external services | Medium |
| L09 | Execution reliability | No explicit timeout or termination handler is shown for spawned prediction processes | Requests may stall or consume server resources | High |
| L10 | API abuse | No rate limiter or authentication gate was verified for `/predict` | Public endpoint could be overloaded | High |
| L11 | Data access | Firestore server-side rules were not available for inspection | User-data isolation cannot be independently confirmed | High |
| L12 | Testing | No dedicated React/Express automated test suite identified | Regressions may escape detection | Medium |
| L13 | Accessibility | Formal accessibility testing has not been evidenced | Some users may encounter barriers | Medium |
| L14 | Impact | No measured reduction in fire losses or environmental damage | Sustainability impact must be described as an aim, not a proven outcome | Medium |

## 3. Machine-learning limitations

### 3.1 A score is not an event probability

The deployed prediction pipeline calculates a neural-network output and converts it to a 0–100 score. Its labels are assigned using application thresholds:

| Score | Displayed category |
|---:|---|
| Below 30 | LOW |
| 30 to below 50 | MODERATE |
| 50 to below 70 | HIGH |
| 70 and above | VERY HIGH |

These categories are **internal application classifications**, not the official Australian Fire Danger Rating System. A score of 80 must **not** be explained as an 80% probability of a fire. No probability calibration or operational certification has been established.

### 3.2 Experimental results do not validate the deployed model

The repository includes evaluation artefacts for alternative approaches:

- Stage 11 neural-network experiments (`models/stage11/experiment_results.csv`), with a best listed validation ROC-AUC of approximately **0.5923**.
- Stage 13B Random Forest experiments (`models/stage13b/results.json`), with a best listed validation ROC-AUC of approximately **0.6932**.
- Stage 14A neural-network experiments (`models/stage14a/results.json`), with a best listed validation ROC-AUC of approximately **0.6417**.

These figures concern **experimental configurations** and must not be presented as performance metrics for the deployed 15-feature V04 network. The experiments use different feature counts and architectures. For example, the Stage 14A records describe 111-feature networks, whereas the deployed V04 inference path uses 15 features.

### 3.3 Overfitting and distribution shift

A Stage 13B Random Forest recorded training accuracy near **99.7%** but validation accuracy near **62.5%**. This is evidence of a substantial training-to-validation generalisation gap for that experimental model. It does not establish that the production model overfits to the same degree.

Weather patterns, vegetation, ignition sources, land management, and climate conditions vary over time and location. Model performance may degrade outside the conditions represented in training data. Reliable deployment would require independent, appropriately separated evaluation, including geographic and temporal holdouts.

### 3.4 Limited causal information

Weather-derived variables and time-of-year features cannot fully describe ignition events, human activity, fuel continuity, vegetation management, terrain, suppression operations, or the rapidly changing behaviour of an active fire. Even an accurately computed score cannot capture all determinants of bushfire occurrence and severity.

## 4. Geographic and data coverage

### 4.1 Prediction locations

The Express `/predict` handler accepts `latitude` and `longitude` only when both values have JavaScript type `number`. The inspected code does **not** additionally check `Number.isFinite`, latitude range **−90 to 90**, longitude range **−180 to 180**, or an Australia-only boundary. Therefore, the endpoint is not demonstrated to enforce an Australian geographic scope.

This is an input-validation gap, **not evidence that the model is valid worldwide**. Predictions outside the model's intended training geography should not be considered reliable without separate evaluation.

### 4.2 Live incidents

The backend retrieves incident information from the **NSW Rural Fire Service major-incidents GeoJSON feed**. This source does not amount to a complete national incident system, and the app must not imply it includes every incident in the ACT or other states and territories.

Incident reporting can be delayed, changed, unavailable, or incomplete. Feed timestamps and the source should be made visible where practical. A map without a nearby incident marker is **not** a declaration of safety.

### 4.3 External data dependencies

Prediction input collection relies on external weather information, including Open-Meteo data; Bureau of Meteorology observations may be presented as supplementary context. Weather forecasts are estimates and can change. External APIs may enforce limits, experience outages, or change response formats.

The climate-news feed provides informational articles, not authoritative warnings or real-time operational intelligence. The presence of a news article should not influence emergency decisions without verification from official sources.

## 5. Application and infrastructure limitations

### 5.1 Prediction process management

The inspected Express handler launches `.venv/bin/python src/predict_api.py` for each request using `child_process.spawn()`. It collects standard output and standard error and returns an error if the process exits unsuccessfully or produces invalid JSON.

No explicit child-process timeout, concurrency limit, output-size limit, or `error` event handler was visible in the inspected endpoint. These are reliability risks that should be addressed before a high-traffic deployment. This observation is limited to the supplied code excerpt and prior code review.

### 5.2 Input validation and public access

The endpoint rejects non-number coordinate values, but does not show finite-number or valid-range checks. CORS is enabled in the backend, and no explicit rate-limiting middleware was identified in the reviewed code. Authentication for account features does not automatically protect a public prediction endpoint.

Possible improvements include schema validation, per-client rate limits, request timeouts, bounded child-process concurrency, and consistent error handling. Implementing these controls requires code changes and separate regression tests; they are **recommendations**, not completed work.

### 5.3 Authentication and Firestore

The frontend implements Firebase Authentication and uses user-specific Firestore paths for prediction history and saved locations. However, no `firestore.rules` file or Firebase configuration deployment file was found in the inspected repository. Consequently, the actual deployed Firestore rules and user-data access restrictions remain **unverified**.

Client-side path selection is not a security boundary. The deployed Firebase rules should be reviewed in the Firebase console and tested using two distinct test accounts and the Firebase Emulator Suite where feasible. Never include private keys or credentials in test evidence.

### 5.4 Testing and deployment evidence

The frontend package defines build and lint commands, but their presence does not prove successful execution against the current working tree. Specialised Python scripts exist for vegetation and elevation-related checks, but no dedicated automated frontend or backend API test suite was identified in the file search.

The known production stack uses Nginx, PM2, Node/Express, Python, and React static assets; actual VPS configuration, uptime, backup and rollback execution, and security hardening were not independently verified in this documentation review.

## 6. Usability, accessibility, and privacy

- **Accessibility:** No formal WCAG audit, keyboard-only walkthrough, screen-reader test, or contrast test has been evidenced. Map controls and colour-coded risk categories warrant special review.
- **Mobile responsiveness:** Interface behaviour on a representative range of devices has not been documented with test evidence.
- **Privacy:** Account-linked locations and prediction history may reveal patterns about users. Retention, deletion, access rules, and privacy notices require a deliberate review.
- **Terminology:** The phrase “fire risk” is easy to overinterpret. Interfaces should consistently state that scores are experimental estimates, not official alerts.
- **User expectations:** Map pins, forecasts, and incident data have different update frequencies. Their timestamps and origins should not be conflated.

## 7. Safety and responsible use

**FireScope AI is for educational exploration and project demonstration.** Do not use its risk categories to decide whether to evacuate, travel through a fire-affected area, conduct hazard reduction, or ignore an official warning.

For actual emergencies, follow emergency services and official Australian state or territory fire-authority advice. In Australia, call **000** for an immediate emergency.

Suggested interface disclosure:

> FireScope AI provides experimental, weather-informed bushfire risk estimates for educational use only. Its scores are not official fire danger ratings or emergency warnings. Always follow your local emergency services and fire authority.

## 8. Prioritised mitigation plan

| Priority | Proposed action | Suggested verification evidence |
|---|---|---|
| P0 | Display unambiguous educational-use and emergency-service notices near prediction results and incident maps | Screenshot and usability check |
| P0 | Verify deployed Firestore rules enforce ownership-based reads and writes | Emulator tests and redacted rules review |
| P1 | Validate finite coordinate values and geographic bounds | Automated negative API tests |
| P1 | Add Python subprocess timeout, error handler, and concurrency protection | Timeout/failure simulations |
| P1 | Add API rate limiting and review CORS policy | Load tests and response checks |
| P1 | Establish independent evaluation of the exact V04 production checkpoint | Reproducible metrics, split strategy, confusion matrix |
| P1 | Clarify NSW-only incident feed coverage and display freshness | UI and feed-failure tests |
| P2 | Add frontend and backend regression suites | CI logs and test reports |
| P2 | Conduct accessibility and mobile usability audits | Recorded checklist and issue log |
| P2 | Review location-history retention and deletion behaviour | Privacy review and account tests |

These items are **proposed improvements**, not claims of implementation.

## 9. Evaluation boundaries for the academic submission

The project demonstrates a functioning integration of a web interface, geospatial interaction, external data services, authentication features, and Python/PyTorch inference. This engineering achievement is distinct from demonstrating scientifically validated bushfire prediction capability.

The academic report should avoid unsupported claims about:

1. Production-model accuracy, ROC-AUC, recall, or calibration.
2. Nationwide completeness of incident reporting.
3. Guaranteed protection of Firestore data before rule verification.
4. Continuous service availability or load capacity.
5. Quantified reductions in fire incidents, losses, emissions, or biodiversity damage.

The appropriate conclusion is that FireScope AI is an **educational proof of concept** with a defined path toward stronger validation, resilience, security, and user safety.

## 10. Related documentation

- [`MACHINE_LEARNING.md`](MACHINE_LEARNING.md) — model pipeline and experiment distinctions.
- [`TESTING.md`](TESTING.md) — evidence, planned tests, and verification gaps.
- [`SECURITY.md`](SECURITY.md) — authentication, data access, and security review.
- [`DEPLOYMENT.md`](DEPLOYMENT.md) — application runtime and operational considerations.
- [`ROADMAP.md`](ROADMAP.md) — planned improvements (to be completed).

---

**Evidence basis:** Repository code excerpts and command outputs supplied during the October 2026 documentation review. This document records current known limitations; it is not an independent security audit, model certification, or production acceptance test.
