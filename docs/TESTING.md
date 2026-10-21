# FireScope AI — Testing and Validation Report

**Project:** FireScope AI (Bushfire AI)  
**Course:** ICT313  
**Document type:** Test plan, available evidence, and verification register  
**Evidence reviewed:** Source-code listings, package scripts, and saved experimental metrics supplied during documentation preparation (19 October 2026).

> **Evidence rule:** A test script, an implemented feature, or a saved result file is not proof that the current application passes a test. This report labels observed evidence separately from proposed tests. Do not mark a case *Passed* without executing it and recording the outcome.

## 1. Purpose and Scope

This report documents how to verify the FireScope AI frontend, Express API, Python/PyTorch inference pipeline, Firebase-backed features, external feeds, and production deployment. It also summarises available machine-learning experiment results without attributing them to the deployed model.

Testing has three distinct dimensions:

1. **Software verification:** Does the implementation behave as specified?
2. **Integration and operational verification:** Do the components and external services work together reliably?
3. **Model evaluation:** How well does a trained model generalise to held-out data?

These questions require different evidence. A successful prediction request, for example, does not establish the statistical accuracy of the prediction.

## 2. Confirmed Testing Infrastructure

The frontend `package.json` declares the following scripts:

| Script | Command | Meaning | Current execution status |
|---|---|---|---|
| `dev` | `vite` | Development server | Not verified in this report |
| `build` | `vite build` | Production build | Passed during final deployment |
| `lint` | `oxlint` | Static analysis | Not verified in this report |
| `preview` | `vite preview` | Preview compiled frontend | Not verified in this report |
| `start` | `node backend/server.js` | Start Express backend | Not verified in this report |

Specialised Python scripts were identified:

- `src/test_local_vegetation.py`
- `src/test_ga_elevation_wcs.py`
- `src/test_vegetation_attributes.py`

Their names suggest data-source or feature-processing checks, but their contents and execution outcomes have **not** been reviewed. A dedicated React unit-test suite has not been documented. A backend automated-test suite was subsequently implemented and passed 21 of 21 tests. A test file found under `frontend-react/backend/node_modules/` belongs to a third-party dependency, not the application's own test suite.

## 3. Verification Status Summary

| Area | Evidence available | Status |
|---|---|---|
| Frontend navigation and rendering | Page components identified in `App.jsx` | Implemented; systematic test not recorded |
| Risk prediction request | `POST /predict` route and Python process integration inspected | Implemented; test not recorded |
| Prediction history | Firestore write, subscription and delete code inspected | Implemented; test not recorded |
| Saved locations | Firestore create, duplicate check, subscription and delete code inspected | Implemented; test not recorded |
| Official fire incidents | NSW RFS retrieval, validation, 60-second cache and HTTP 502 error path inspected | Implemented; test not recorded |
| Climate news | RSS parser and 15-minute cache configuration identified | Implemented; test not recorded |
| Production build | Vite production build | Passed during final deployment |
| Linting | Lint command exists | Not executed for this report |
| Deployed-model accuracy | No verified V04 evaluation report supplied | **Unknown** |
| Experimental model evaluation | Stage 11, Stage 13B, Stage 14A saved metrics reviewed | Recorded experimental evidence |

## 4. Functional Test Matrix

The following cases are **proposed verification procedures**, not completed test results. Update the last two columns after testing.

| ID | Requirement | Test procedure | Expected result | Observed result | Status |
|---|---|---|---|---|---|
| T-01 | FR-01 | Open the application and navigate among major pages | Pages render without blocking errors | Not recorded | Not tested |
| T-02 | FR-02/03 | Search for and select a valid location | Location selection updates the interface | Not recorded | Not tested |
| T-03 | FR-04/05/06 | Submit a valid location for analysis | API returns parseable JSON and UI displays result | Not recorded | Not tested |
| T-04 | FR-04 | Send `/predict` with missing/non-numeric coordinates | HTTP 400 with explanatory JSON error | Not recorded | Not tested |
| T-05 | FR-04 | Send coordinates outside valid geographic ranges | Request rejected or limitation documented | Not recorded | Not tested |
| T-06 | FR-07 | Change location while a prediction is in progress | Stale result does not overwrite newer selection | Not recorded | Not tested |
| T-07 | FR-09 | Sign in and sign out using supported methods | Authentication state changes correctly | Not recorded | Not tested |
| T-08 | FR-11/12 | Sign in, predict, open history | New record appears for the correct user | Not recorded | Not tested |
| T-09 | FR-12 | Delete a prediction-history record | Selected record disappears | Not recorded | Not tested |
| T-10 | FR-13 | Save a location twice | Duplicate is identified, not silently duplicated | Not recorded | Not tested |
| T-11 | FR-13 | Remove a saved location | Location is deleted from the user's list | Not recorded | Not tested |
| T-12 | FR-14/15 | Open Fire Warnings with working feed | Available NSW RFS incidents render on map | Not recorded | Not tested |
| T-13 | FR-14 | Simulate unavailable NSW RFS upstream | Backend returns controlled error; UI handles failure | Not recorded | Not tested |
| T-14 | FR-17 | Open Climate News | Available articles render; errors are handled | Not recorded | Not tested |
| T-15 | FR-20 | Inspect warning and prediction screens | Official warnings are distinguishable from AI estimates | Not recorded | Not tested |
| T-16 | NFR-02 | Inspect mobile and desktop layouts | Core controls remain usable | Not recorded | Not tested |
| T-17 | NFR-05 | Attempt to read another user's Firestore data | Access is denied by deployed Firestore rules | Not recorded | Not tested |
| T-18 | NFR-09 | Check live site and `/health` endpoint | Public site loads and backend responds | Not recorded | Not tested |

**Known input-validation gap:** The inspected Express route verifies numeric latitude and longitude but does not enforce valid geographic ranges. T-05 should be treated as an open validation requirement until addressed and retested; it is not marked as passed.

## 5. Suggested Reproducible Checks

Run these only when ready to test, and capture the actual output, date and environment. The commands below are examples; they have **not** been executed as part of this report.

### 5.1 Frontend build and lint

```bash
cd ~/Desktop/bushfire-ai/frontend-react
npm run build
npm run lint
```

Record the exit status and any warnings. A successful build checks bundling, not end-to-end application behaviour.

### 5.2 Backend health and input handling

With the backend running locally, for example on its default port 3015:

```bash
curl -i http://localhost:3015/health
curl -i -X POST http://localhost:3015/predict \
  -H 'Content-Type: application/json' \
  -d '{"latitude":"invalid","longitude":149.13}'
```

The inspected code specifies a JSON health response and HTTP 400 for non-numeric coordinates. Verify the actual responses and preserve the output. Do not run repeated live prediction tests unnecessarily; they depend on external weather data and start a Python process.

### 5.3 Manual verification record

For each completed test, retain: test ID, date/time, Git commit hash, environment (local or VPS), steps, expected output, actual output, status, and screenshot or log path. Avoid publishing authentication tokens, private account details or user data.

## 6. Machine Learning Evaluation Evidence

### 6.1 Critical model distinction

The inspected production prediction path is:

`src/predict_api.py` → `src/predict_location.py` → `models/bushfire_model_v04.pth`

The deployed-code model definition uses **15 inputs → 32 → 16 → 8 → 1**, with ReLU hidden activations and sigmoid applied to the output logit. The saved results below concern **other experiments** with different feature dimensions and architectures. They must **not** be presented as performance metrics for V04.

### 6.2 Stage 11: Neural network architecture comparison

Source: `models/stage11/experiment_results.csv` (reported validation metrics).

| Experiment | Architecture | Validation accuracy | Validation F1 | Validation ROC-AUC |
|---|---|---:|---:|---:|
| `large_128_64_32` | 16–128–64–32–1 | 0.5634 | 0.6125 | 0.5923 |
| `boss_512_256_128_64` | 16–512–256–128–64–1 | 0.5620 | 0.6046 | 0.5908 |
| `xl_256_128_64` | 16–256–128–64–1 | 0.5692 | 0.5956 | 0.5904 |
| `medium_64_32_16` | 16–64–32–16–1 | 0.5537 | 0.6574 | 0.5782 |
| `baseline_32_16_8` | 16–32–16–8–1 | 0.5505 | 0.5999 | 0.5778 |

These are **16-input experimental models**, not the 15-input V04 production model. The highest validation F1 in this table is not the highest validation ROC-AUC; metric choice changes how models rank.

### 6.3 Stage 13B: Random Forest comparison

Source: `models/stage13b/results.json`.

| Experiment | Train accuracy | Validation accuracy | Validation F1 | Train ROC-AUC | Validation ROC-AUC | AUC gap |
|---|---:|---:|---:|---:|---:|---:|
| `RF_A_current` | 0.9970 | 0.6251 | 0.6484 | 0.9998 | 0.6932 | 0.3066 |
| `RF_B_depth20_leaf5` | 0.8260 | 0.6273 | 0.6818 | 0.9374 | 0.6918 | 0.2457 |
| `RF_C_depth15_leaf10` | 0.7070 | 0.6172 | 0.6864 | 0.8349 | 0.6830 | 0.1519 |
| `RF_D_depth10_leaf15` | 0.6498 | 0.6031 | 0.6862 | 0.7543 | 0.6674 | 0.0869 |

**Interpretation:** The nearly perfect training performance of `RF_A_current` contrasts with materially lower validation results. The large train–validation ROC-AUC gap is consistent with a generalisation/overfitting concern, though a full diagnosis would require review of the data split, feature engineering and training procedure. Increasing regularisation reduces the gap in these experiments but does not establish deployment suitability.

### 6.4 Stage 14A: Neural network tournament

Source: `models/stage14a/results.json`.

| Experiment | Architecture | Validation accuracy | Validation F1 | Validation ROC-AUC | AUC gap |
|---|---|---:|---:|---:|---:|
| `NN_256_128_64` | 111–256–128–64–1 | 0.5908 | 0.6109 | 0.6417 | 0.0504 |
| `NN_128_64_32` | 111–128–64–32–1 | 0.5952 | 0.6479 | 0.6412 | 0.0502 |
| `NN_512_256_128_64` | 111–512–256–128–64–1 | 0.5981 | 0.6523 | 0.6341 | 0.0276 |

These experiments use **111 inputs**, substantially different from the deployed V04 feature set. They are useful evidence of experimentation but are not directly comparable to V04 without matched datasets, splits and evaluation conditions.

### 6.5 Metric interpretation

- **Accuracy:** Fraction of classifications that match the evaluation labels.
- **Precision:** Fraction of predicted positive cases that are actually positive.
- **Recall:** Fraction of actual positive cases detected.
- **F1:** Harmonic mean of precision and recall.
- **ROC-AUC:** Ability to rank positive cases above negative cases across thresholds.
- **Train–validation gap:** Difference between performance on training and validation data; a large gap can indicate weak generalisation.

Validation results alone do not establish performance on new locations, unseen fire seasons or operational emergency decisions. Dataset construction, spatial/temporal leakage, class balance, calibration and independent hold-out evaluation should be assessed before making stronger claims.

### 6.6 Unverified production-model evaluation

**No verified accuracy, F1, precision, recall or ROC-AUC has been supplied for `bushfire_model_v04.pth`.** Do not transfer Stage 11/13B/14A numbers to V04. A future evaluation should load the exact V04 checkpoint, reproduce its 15-feature preprocessing, evaluate on an appropriate untouched dataset, and save metrics plus confusion matrix and methodology.

## 7. Reliability, Security and Data-Quality Tests Still Needed

Important future checks include external API timeouts, missing or null weather values, malformed upstream responses, concurrent prediction requests, stale-request handling, cache freshness, authentication flows, Firestore security-rule enforcement, duplicate-location handling, responsive layouts, and production restart behaviour.

The Python weather request shown in the inspected inference code uses a 30-second timeout. The Express prediction route does not show a dedicated child-process timeout. These observations warrant explicit timeout and failure-path tests.

## 8. Defect and Risk Register

| ID | Finding | Evidence | Priority | Resolution status |
|---|---|---|---|---|
| D-01 | Latitude/longitude geographic bounds not checked in inspected Express route | `frontend-react/backend/server.js` | Medium | Open |
| D-02 | No dedicated prediction child-process timeout identified | `frontend-react/backend/server.js` | Medium | Open |
| D-03 | No verified deployed V04 evaluation metrics supplied | Evidence review | High for predictive claims | Open |
| D-04 | No dedicated frontend UI automated-test suite documented; backend suite now has 21 passing tests | Final test verification | Medium | Partially addressed |
| D-05 | Published Firestore rules reviewed; independent cross-user runtime tests outstanding | Final security verification | High for privacy assurance | Partially addressed |

These are documented findings or verification gaps, **not** claims of observed production incidents.

## 9. Evidence Log Template

Copy this table into a dated testing log as tests are executed:

| Date | Test ID | Commit | Environment | Actual result | Status | Evidence file |
|---|---|---|---|---|---|---|
| — | — | — | — | Not yet recorded | Not tested | — |

Use only observed outcomes. A screenshot should demonstrate the actual state of the application and should not contain private user information.

## 10. Acceptance and Next Steps

Before calling the system fully verified, prioritise: (1) build and lint checks; (2) a recorded happy-path prediction; (3) invalid-input and upstream-failure cases; (4) authenticated history and saved-location workflows; (5) Firestore rule tests; and (6) independent evaluation of the exact V04 checkpoint.

A credible academic submission can report incomplete testing as long as the distinction between **implemented**, **observed**, **evaluated**, and **not tested** remains explicit.

## 11. Related Documents

- [Requirements](REQUIREMENTS.md)
- [System Architecture](ARCHITECTURE.md)
- [Machine Learning](MACHINE_LEARNING.md)
- [Database Design](DATABASE_DESIGN.md)
- [Security](SECURITY.md)
- [Limitations](LIMITATIONS.md)

---

## Final Verification Results — October 2026

### Automated backend tests

Command:

`node --test frontend-react/backend/tests/*.test.js`

**Result: 21 tests passed out of 21.**

Eight additional structural safety checks were also completed.

### Firebase integration testing

The account deletion workflow was tested with two disposable Firebase accounts.

Verified outcomes:

- Authenticated deletion requests were processed.
- Firestore account deletion jobs completed.
- Disposable users' Firebase Authentication accounts were removed.
- Associated user records were removed.

### Production verification

- React/Vite production build completed successfully.
- Backend dependencies installed successfully.
- PM2 reported the production backend online.
- The public website returned HTTP 200.
- The unauthenticated account deletion endpoint rejected requests with HTTP 401.
- The account deletion recovery scheduler started successfully.

### Remaining testing limitations

- No independent, comprehensive cross-user Firestore rules test suite has been documented.
- No complete automated frontend UI test suite has been documented.
- The final production deployment verification does not independently establish the predictive accuracy of the trained V04 machine-learning model.
- The Vite build reported a JavaScript chunk-size warning; this was not a build failure.
