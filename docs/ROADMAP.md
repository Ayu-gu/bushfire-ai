# FireScope AI — Project Roadmap

**Project:** FireScope AI (Bushfire AI)  
**Context:** ICT313 A3 Project Solution  
**Status:** Proposed improvements; not a commitment that features are implemented  
**Last reviewed:** 19 October 2026

## 1. Purpose

This roadmap identifies practical next steps for improving the existing FireScope AI prototype. It separates current capabilities from proposed work and prioritises user safety, scientific validity, security, reliability, and maintainability. Dates are deliberately not assigned: implementation depends on available time, access to infrastructure and data, and the results of verification.

## 2. Current baseline

The project currently includes a React/Vite interface, an Express API, Python-based PyTorch inference, Firebase Authentication and Firestore-backed personal records, an interactive map, NSW Rural Fire Service incident information, and a climate-news feed. The production prediction model is the V04 neural network with 15 input features. The Git history records iterative development from 18 August to 14 October 2026.

**Important:** An AI-generated risk score is not an official Australian Fire Danger Rating, a calibrated probability of fire, or an emergency warning. Official emergency advice must take precedence.

## 3. Priority framework

| Priority | Meaning | Decision principle |
|---|---|---|
| P0 — Critical | Safety, access control, and severe reliability gaps | Address before wider public promotion |
| P1 — High | Scientific validation and core application robustness | Prioritise before expanding functionality |
| P2 — Medium | Maintainability and user experience | Deliver once core risks are controlled |
| P3 — Future research | Experimental or expansion work | Undertake only with appropriate evidence and resources |

The priority labels are proposed planning classifications, not results from a formal risk assessment.

## 4. Phase 1 — Security and operational safeguards (P0)

### 4.1 Verify Firestore access rules

**Current evidence:** The application stores prediction history and saved locations under `users/{uid}/...`, but deployed Firestore Security Rules have not been inspected.

**Proposed actions:**
- Review deployed rules in Firebase and ensure each authenticated user can access only their own records.
- Test permitted and denied reads, writes, and deletes with separate test accounts.
- Validate expected document fields and ownership constraints where appropriate.
- Record the tested rules version and outcomes in `TESTING.md` and `SECURITY.md`.

**Acceptance criteria:** Cross-account access attempts are denied by server-enforced rules; legitimate account operations continue to work.

### 4.2 Strengthen the prediction endpoint

**Current evidence:** `/predict` checks that latitude and longitude are JavaScript numbers, but explicit geographic range and finite-number checks were not observed. The Python subprocess has no confirmed execution timeout.

**Proposed actions:**
- Reject non-finite values and coordinates outside latitude `[-90, 90]` and longitude `[-180, 180]`.
- Set appropriate JSON request-size limits and a maximum prediction execution time.
- Handle subprocess startup errors, timeouts, and unexpected exits consistently.
- Review CORS origins and add proportionate request rate limiting.
- Avoid leaking internal paths or stack traces in public error messages.

**Acceptance criteria:** Invalid inputs return clear 4xx responses; failed or timed-out inference produces controlled errors without hanging requests.

### 4.3 Clarify safety messaging

**Proposed actions:**
- Keep visible disclaimers beside prediction results and warning information.
- Label NSW RFS incident data separately from AI-generated estimates.
- Provide prominent pathways to official state and territory emergency services.
- Check that stale or unavailable incident feeds are clearly identified.

**Acceptance criteria:** A user can distinguish experimental predictions from official warnings without reading technical documentation.

## 5. Phase 2 — Testing and model validation (P1)

### 5.1 Establish repeatable software tests

**Current evidence:** Vite build and Oxlint scripts exist. Three specialised Python test scripts were found. Dedicated frontend and backend automated test suites have not been identified.

**Proposed actions:**
- Add API tests for `/health`, `/predict`, `/api/fire-incidents`, and `/api/climate-news`.
- Mock external weather, fire-incident, news, and authentication dependencies.
- Add UI tests for navigation, prediction submission, errors, sign-in flows, and saved records.
- Introduce a reproducible smoke-test checklist for production deployment.
- Run `npm run build` and `npm run lint`, record their actual results, and fix failures.

**Acceptance criteria:** Core behaviours have repeatable tests; results are recorded with dates, environments, and evidence.

### 5.2 Evaluate the deployed V04 model

**Current evidence:** Experimental results are available for Stage 11, Stage 13B, and Stage 14A. These are **not** verified metrics for the deployed 15-feature V04 model.

**Proposed actions:**
- Identify the exact V04 checkpoint, training data, labels, and preprocessing version.
- Reproduce evaluation on a held-out, appropriately separated dataset.
- Report ROC-AUC, precision, recall, F1, confusion matrix, and class balance.
- Assess performance across regions, seasons, and weather conditions.
- Check score calibration; avoid interpreting sigmoid output as real-world fire probability without supporting evidence.
- Investigate leakage, temporal dependencies, geographic overlap, and class imbalance.

**Acceptance criteria:** A reproducible V04 evaluation report exists, with explicit data provenance, limitations, and uncertainty.

### 5.3 Review model selection

Stage 13B's best reported validation ROC-AUC was approximately **0.6932**, but its corresponding training ROC-AUC was approximately **0.9998**, signalling substantial generalisation concerns. Stage 11 and Stage 14A used different feature dimensions and experimental setups. Their results should not be treated as directly comparable to the deployed V04 system without matching evaluation protocols.

**Proposed actions:** Compare candidate models only under consistent splits, features, labels, and metrics. Prefer reliable generalisation and interpretability over training accuracy alone.

## 6. Phase 3 — Reliability and maintainability (P1–P2)

### 6.1 Improve observability

- Add structured backend logs without personal or secret data.
- Track request failures, upstream feed errors, inference duration, and service health.
- Distinguish live, cached, stale, and unavailable incident/news data in responses and UI.
- Document routine incident response and recovery steps.

**Acceptance criteria:** Maintainers can diagnose a failed prediction or external-feed outage without exposing sensitive information.

### 6.2 Make deployment reproducible

- Document verified Nginx and PM2 configuration values from the actual VPS, excluding secrets.
- Define supported Node.js and Python versions and dependency installation steps.
- Validate the production build and prediction path after each release.
- Maintain a rollback plan and verify backups where applicable.
- Consider automated CI checks for linting, builds, and tests.

**Acceptance criteria:** A maintainer can deploy and roll back using a reviewed checklist rather than relying on undocumented steps.

### 6.3 Reduce inference coupling

**Current approach:** Express launches a Python subprocess for predictions.

**Future option:** Evaluate a persistent Python service or worker if measured traffic and latency justify it. This is an architectural option, not a current implementation claim.

**Acceptance criteria:** Any change demonstrably improves reliability or performance and preserves prediction behaviour.

## 7. Phase 4 — User experience and accessibility (P2)

- Test keyboard navigation, focus indicators, labels, and screen-reader descriptions.
- Check contrast and avoid relying on colour alone for risk categories.
- Improve mobile layouts and loading/error states.
- Explain input data age, geographic relevance, and forecast uncertainty.
- Provide clear sign-in, email verification, password reset, and data-deletion guidance.
- Conduct short usability sessions and document feedback and resulting changes.

**Acceptance criteria:** Key workflows are understandable and usable on common devices, including with accessibility aids.

## 8. Phase 5 — Geographic and data coverage (P2–P3)

**Current evidence:** Live incident integration uses the NSW Rural Fire Service feed; this does not constitute nationwide coverage.

**Proposed actions:**
- Assess official incident feeds for additional Australian jurisdictions, including licensing, formats, update intervals, and reliability.
- Clearly identify coverage boundaries for each feed.
- Investigate authoritative vegetation, terrain, and historical fire datasets where permitted.
- Add source attribution and timestamps for externally supplied information.
- Evaluate regional differences before extending claims about model applicability.

**Acceptance criteria:** New regions are added only when their data coverage, provenance, and limitations are documented and tested.

## 9. Phase 6 — Research and responsible expansion (P3)

Possible research directions include:

- Improved spatiotemporal validation and independent evaluation datasets.
- Comparison with interpretable baselines and established fire-weather indicators.
- Uncertainty estimates and model explanations validated for usefulness.
- Monitoring for data drift and seasonal performance changes.
- Privacy-conscious user research to evaluate whether the tool improves understanding.

**Boundary:** None of these research directions imply that FireScope AI can predict the location or timing of future fires with operational reliability. Such claims would require substantially stronger evidence and appropriate expert review.

## 10. Suggested delivery sequence

| Order | Deliverable | Evidence of completion |
|---|---|---|
| 1 | Firestore rules audit | Tested allow/deny scenarios |
| 2 | API validation, timeouts, error handling | Repeatable negative and failure tests |
| 3 | Safety labels and official-source distinction | UI review and user comprehension checks |
| 4 | Core API/UI smoke tests | Logged test runs and outcomes |
| 5 | Deployed V04 model evaluation | Reproducible metrics and limitations |
| 6 | Deployment and monitoring improvements | Verified runbook and recovery exercise |
| 7 | Accessibility and usability review | Findings and resolved issues |
| 8 | Additional geographic coverage | Source-specific validation and attribution |

This sequence is indicative; urgent vulnerabilities or new evidence may change the order.

## 11. Risks and dependencies

| Dependency | Risk if unavailable | Mitigation |
|---|---|---|
| Firebase administrative access | Cannot verify deployed security rules | Request authorised access; document unverified status |
| Representative evaluation data | Misleading claims about model performance | Report gaps explicitly; defer accuracy claims |
| External APIs and feeds | Stale or missing information | Timeouts, caching policy, visible source status |
| VPS configuration access | Incomplete deployment verification | Preserve known facts and validate with authorised operator |
| Development time | Scope expansion displaces safety work | Complete P0/P1 items before optional features |

## 12. Documentation maintenance

Update the following documents as improvements are actually implemented:

- `REQUIREMENTS.md` — new or changed requirements.
- `ARCHITECTURE.md` — system design changes.
- `DATABASE_DESIGN.md` — schema and rule changes.
- `MACHINE_LEARNING.md` — model or feature changes.
- `TESTING.md` — executed tests and verified evaluation results.
- `DEPLOYMENT.md` — confirmed operational procedures.
- `SECURITY.md` — controls and audit evidence.
- `LIMITATIONS.md` — unresolved and resolved limitations.
- `USER_GUIDE.md` — user-facing behaviour changes.

A roadmap item should be marked **complete only after implementation and verification**, not when it has merely been planned.

## 13. Conclusion

FireScope AI provides a working educational prototype combining an interactive interface, live external information, user accounts, and machine-learning-based risk estimates. Its next stage should focus on proving the reliability, security, and scientific validity of those capabilities before pursuing broader coverage or more sophisticated models. This roadmap offers a practical direction while keeping planned work clearly separate from demonstrated functionality.
