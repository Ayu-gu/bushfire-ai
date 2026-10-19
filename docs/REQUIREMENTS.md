# FireScope AI — Software Requirements Specification

**Project:** FireScope AI  
**Course:** ICT313  
**Development approach:** Individual, iterative development  
**Document type:** Software Requirements Specification (SRS)

---

## 1. Purpose

This document defines the functional and non-functional requirements of FireScope AI, an educational bushfire risk assessment and decision-support application.

It describes the intended behaviour of the system, its technical constraints and the criteria used to evaluate its implementation.

Requirements are based on the project's objectives and implemented application architecture.

## 2. System Overview

FireScope AI integrates a React frontend, Node.js/Express backend, Python-based environmental processing, a trained PyTorch neural network, Firebase services and external environmental and geospatial data sources.

The application allows users to select locations, request bushfire risk assessments, explore geographic information and access supporting environmental information.

Additional functionality includes account management, prediction history, saved locations and NSW Rural Fire Service incident information.

The application is an educational decision-support system, not an official emergency warning service.

## 3. Stakeholders

| Stakeholder | Primary Interest |
|---|---|
| General users | Accessible environmental risk information |
| Registered users | Account functionality and saved information |
| Developer | Maintainability, reliability and extensibility |
| Academic assessors | Evidence of software engineering knowledge and implementation |
| External data providers | Appropriate use and attribution of data |

## 4. Functional Requirements

Functional requirements describe what the system should do.

| ID | Requirement | Priority | Implementation Evidence |
|---|---|---|---|
| FR-01 | Provide a navigable web dashboard | High | React application and page navigation |
| FR-02 | Allow users to select a geographic location | High | Map and location state |
| FR-03 | Support location search | High | Header search interface |
| FR-04 | Submit geographic coordinates for risk assessment | High | POST `/predict` |
| FR-05 | Process assessment requests through the backend | High | Express and Python integration |
| FR-06 | Generate risk estimates using the trained neural network | High | PyTorch inference pipeline |
| FR-07 | Display prediction results | High | Dashboard prediction state and components |
| FR-08 | Provide interactive geographic visualisation | High | MapTiler-based mapping components |
| FR-09 | Support user authentication | High | Firebase Authentication integration |
| FR-10 | Provide account-management functionality | Medium | Settings page |
| FR-11 | Store prediction history for authenticated users | High | Firestore `predictionHistory` records |
| FR-12 | Display previous predictions | Medium | Prediction History page |
| FR-13 | Provide saved-location functionality | Medium | Saved Locations page |
| FR-14 | Retrieve NSW RFS incident information | High | GET `/api/fire-incidents` |
| FR-15 | Display incident locations on a map | High | Fire Incident Map component |
| FR-16 | Display available incident warning classifications | Medium | Fire Warnings and notification interface |
| FR-17 | Provide access to climate-related information | Medium | Climate News page |
| FR-18 | Provide project information | Low | About page |
| FR-19 | Provide a contact interface | Low | Contact page |
| FR-20 | Distinguish experimental predictions from official warnings | High | Safety notices and official-source links |

**Status note:** Implementation evidence identifies relevant code or application components. It does not independently prove that every requirement has passed formal testing.

## 5. Non-Functional Requirements

Non-functional requirements describe the quality and operational expectations of the system.

| ID | Category | Requirement | Verification Approach |
|---|---|---|---|
| NFR-01 | Usability | Navigation and primary actions should be understandable | Manual usability testing |
| NFR-02 | Responsiveness | The interface should remain usable across supported screen sizes | Responsive layout testing |
| NFR-03 | Reliability | The application should handle unsuccessful API requests gracefully | Failure and recovery tests |
| NFR-04 | Performance | Predictions and page interactions should complete within acceptable time | Response-time measurements |
| NFR-05 | Security | Authentication and user data should use appropriate access controls | Authentication and Firestore rule review |
| NFR-06 | Privacy | Credentials and sensitive configuration must not be exposed in the repository | Repository and configuration review |
| NFR-07 | Maintainability | Frontend, backend and inference responsibilities should remain separated | Architecture and code review |
| NFR-08 | Compatibility | The application should operate in modern supported browsers | Browser compatibility tests |
| NFR-09 | Availability | The deployed application should be accessible through its public domain | Production availability checks |
| NFR-10 | Data integrity | Prediction records should retain relevant assessment values | Firestore data verification |
| NFR-11 | Transparency | Predictions should be identified as experimental estimates | Interface and documentation review |
| NFR-12 | Safety | Official emergency information should remain clearly distinguishable | Warning interface inspection |

Specific numerical performance and availability targets have not been established. Future iterations should define measurable thresholds and collect repeatable results.

## 6. Primary Use Cases

### UC-01: Assess Bushfire Risk

**Actor:** Application user

**Precondition:** The application is available and a location can be selected.

**Main flow:**

1. The user opens the dashboard or relevant assessment interface.
2. The user searches for or selects a geographic location.
3. The user initiates a risk assessment.
4. The frontend sends coordinates to the backend.
5. The backend invokes the environmental processing and prediction pipeline.
6. The application displays the returned assessment.

**Alternative flow:** If the request fails, the application should display an appropriate error instead of presenting a fabricated prediction.

### UC-02: View Fire Incidents

**Actor:** Application user

**Main flow:**

1. The user opens Fire Warnings.
2. The application requests incident information from the backend.
3. Available NSW RFS incidents are displayed on the map.
4. The user explores incident locations and classifications.
5. The user may follow a link to official emergency-service information.

**Alternative flow:** If the external feed is unavailable, the application should communicate that limitation.

### UC-03: Access Prediction History

**Actor:** Authenticated user

**Main flow:**

1. The user signs in.
2. The user completes a risk assessment.
3. The application attempts to store the prediction under the authenticated user's Firestore records.
4. The user opens Prediction History to review available records.

**Alternative flow:** If saving fails, the application should handle the failure without misrepresenting the persistence outcome.

### UC-04: Manage Account

**Actor:** Registered user

**Main flow:**

1. The user signs in using a supported authentication method.
2. The user opens the account menu.
3. The user selects My Account.
4. The application opens Settings.
5. The user accesses available account-management functionality.

## 7. Data Requirements

The system processes several categories of information.

| Data Category | Examples | Purpose |
|---|---|---|
| Geographic | Latitude, longitude, location name | Location-based assessment |
| Environmental | Temperature, humidity, wind and rainfall | Model feature engineering |
| Model output | Risk score and risk classification | Assessment presentation |
| Authentication | Firebase user identifier and account metadata | User identity |
| Prediction history | Location, result and timestamp | User-specific records |
| Incident information | Incident title, category, location and update information | NSW RFS visualisation |

The precise Firestore schema, security rules and data relationships are documented separately in `DATABASE_DESIGN.md`.

## 8. External Dependencies

FireScope AI depends on:

- Firebase Authentication and Firestore.
- MapTiler mapping and geocoding services.
- Environmental data sources used by the assessment pipeline.
- NSW Rural Fire Service incident information.
- The Linux hosting environment and backend runtime.

Service outages, rate limits, connectivity failures and upstream data changes may affect functionality.

## 9. Constraints and Assumptions

The project was developed individually within academic time and resource constraints.

The application assumes that required services and configuration are available.

The machine learning model is experimental and requires further validation before any operational use.

NSW RFS incident data does not represent complete national incident coverage. ACT emergency incident integration remains outside the implemented feed coverage.

## 10. Requirements Verification

Requirements should be assessed using documented test cases rather than implementation claims alone.

The testing report should record:

- Requirement identifier.
- Test scenario and procedure.
- Expected outcome.
- Observed outcome.
- Pass, fail or not-tested status.
- Supporting screenshots or logs.
- Known defects and limitations.

See [Testing and Validation](TESTING.md).

## 11. Traceability

| Requirement Group | Supporting Documentation |
|---|---|
| Project objectives and scope | [Project Overview](PROJECT_OVERVIEW.md) |
| System integration | [Architecture](ARCHITECTURE.md) |
| Data storage | [Database Design](DATABASE_DESIGN.md) |
| Neural network and evaluation | [Machine Learning](MACHINE_LEARNING.md) |
| Functional verification | [Testing](TESTING.md) |
| User interactions | [User Guide](USER_GUIDE.md) |
| Hosting and configuration | [Deployment](DEPLOYMENT.md) |
| Known constraints | [Limitations](LIMITATIONS.md) |

---

## 12. Conclusion

This specification establishes the expected functionality and quality characteristics of FireScope AI.

It provides a reference for system design, implementation, testing and future development.

The requirements reflect an educational machine learning application and should not be interpreted as certification for emergency-management use.
