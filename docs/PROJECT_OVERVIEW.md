# FireScope AI — Project Overview

## 1. Executive Summary

FireScope AI is an educational, full-stack bushfire risk assessment and decision-support platform developed as an individual software engineering project.

The application combines a trained PyTorch neural network, environmental data processing, geospatial visualisation and a React-based web interface to estimate bushfire risk using weather and environmental conditions.

The system also incorporates user authentication, account management, saved locations, prediction history and access to official NSW Rural Fire Service incident information.

FireScope AI demonstrates how machine learning can be integrated into an accessible web application to support environmental awareness and informed decision-making.

**Live application:** https://2026s2a2.winproject.com.au/

**Development model:** Individual project with AI-assisted development support.

---

## 2. Problem Statement

Bushfire risk is influenced by interacting environmental factors, including temperature, humidity, wind conditions, rainfall and accumulated dryness.

Understanding how these factors contribute to potential fire conditions can be difficult when information is distributed across different sources or presented without sufficient context.

FireScope AI explores how environmental observations and machine learning can be combined to provide an accessible assessment of bushfire risk.

The project does not attempt to replace emergency services, official warning systems or professional fire danger ratings.

Instead, it investigates the potential of machine learning and web technologies as supporting tools for environmental risk awareness.

---

## 3. Project Objectives

The primary objectives of FireScope AI were to:

1. Develop a machine learning model capable of processing multiple environmental features to estimate bushfire risk.
2. Design a responsive web application that presents model predictions and relevant environmental information.
3. Integrate location-based functionality and interactive geospatial visualisation.
4. Connect the frontend, backend and Python-based inference pipeline into a functional system.
5. Implement authentication and user-specific features to support account management and prediction history.
6. Integrate official incident information to provide additional context while distinguishing emergency warnings from model-generated predictions.
7. Deploy the application to a publicly accessible Linux server.
8. Evaluate the system's functionality, limitations and opportunities for future improvement.

---

## 4. Sustainable Development Goal Alignment

### SDG 15 — Life on Land (Primary Alignment)

United Nations Sustainable Development Goal 15 focuses on protecting terrestrial ecosystems, sustainably managing forests, combating land degradation and preventing biodiversity loss.

Bushfires can significantly affect forests, wildlife habitats and terrestrial ecosystems.

FireScope AI aligns with SDG 15 by exploring how environmental monitoring and machine learning can support awareness of conditions associated with bushfire risk.

The project contributes to the technological exploration of environmental decision-support systems rather than directly measuring ecological conservation outcomes.

### SDG 13 — Climate Action (Secondary Alignment)

Sustainable Development Goal 13 calls for urgent action to address climate change and its impacts.

FireScope AI supports the broader objectives of climate-related preparedness and awareness by analysing environmental conditions relevant to bushfire risk.

The project demonstrates how data-driven applications can help communicate environmental information in a more accessible format.

The system does not establish a direct causal relationship between individual predictions and climate change, nor does it claim to reduce disaster impacts.

### Additional Relevance — SDG 11

The project's focus on environmental risk awareness also relates to SDG 11: Sustainable Cities and Communities, particularly community resilience and disaster preparedness.

SDG 11 is a supporting connection rather than the project's primary focus.

---

## 5. Intended Users and Stakeholders

The application is primarily intended for:

- Students and researchers exploring environmental machine learning.
- Software developers interested in full-stack AI integration.
- Members of the public seeking educational information about bushfire-related environmental conditions.
- Academic assessors evaluating the project's technical implementation and development process.

Potential future stakeholders include environmental organisations and community groups, subject to appropriate validation and operational safeguards.

FireScope AI is not intended for emergency dispatch, operational firefighting decisions or life-critical decision-making.

---

## 6. Project Scope

### Included in the Implemented System

- React-based interactive web application.
- Environmental feature processing and machine learning inference.
- Location-based bushfire risk assessment.
- Interactive geographic mapping.
- Node.js and Express backend integration.
- Python and PyTorch neural network integration.
- Firebase authentication and account-related functionality.
- Prediction history and saved locations.
- NSW Rural Fire Service incident-feed visualisation.
- Fire warning information and links to official sources.
- Public deployment on a Linux-based hosting environment.

### Outside the Current Scope

- Official fire danger rating certification.
- Guaranteed prediction accuracy for all Australian regions.
- Emergency-service-grade alert delivery.
- Real-time monitoring of every Australian fire incident.
- Integration of all state and territory emergency-service feeds.
- Automated emergency response or evacuation recommendations.
- Fully automated CI/CD deployment pipelines.

These exclusions reflect the project's educational purpose and current technical limitations.

---

## 7. Project Deliverables

The project deliverables include:

1. A trained PyTorch neural network and supporting inference pipeline.
2. A full-stack web application integrating frontend and backend services.
3. Interactive location and environmental risk assessment features.
4. User account and data-management functionality.
5. Integration with official NSW fire incident information.
6. A publicly accessible deployed application.
7. A GitHub repository containing the application source code.
8. Technical documentation, development records, testing information and user guidance.

---

## 8. Success Criteria

The project is evaluated against the following criteria:

| Criterion | Expected Outcome |
|---|---|
| Model integration | The application can invoke the trained model and display a prediction. |
| Frontend functionality | Users can navigate the interface and access implemented features. |
| Geospatial functionality | Users can select or search for locations and view geographic information. |
| Backend integration | The frontend can communicate with the backend through defined API routes. |
| Authentication | Supported sign-in methods and account features function as designed. |
| Incident information | NSW RFS incident information can be retrieved and displayed when available. |
| Deployment | The application is accessible through its configured public domain. |
| Documentation | Architecture, operation, testing and limitations are documented. |

Meeting a functional criterion does not, by itself, establish operational reliability or predictive accuracy. Those require separate validation and testing evidence.

---

## 9. Project Constraints

Key project constraints included:

- Individual responsibility for planning, implementation and verification.
- Limited time and computing resources.
- Dependence on third-party environmental and mapping services.
- Differences between local development and production environments.
- Challenges associated with historical environmental datasets and model generalisation.
- The need to distinguish experimental risk estimates from official emergency information.

These constraints influenced the project's development priorities and iterative implementation approach.

---

## 10. Conclusion

FireScope AI demonstrates the integration of machine learning, geospatial information, user-facing web technologies and cloud-based services within a single educational decision-support platform.

The project addresses a meaningful environmental problem while providing practical experience in data processing, software architecture, frontend and backend development, authentication, deployment and troubleshooting.

Its strongest contribution is demonstrating a complete working integration of these technologies. Further model validation, broader incident-data coverage, automated testing and operational monitoring would be necessary before considering more demanding real-world applications.

---

## Related Documentation

- [Requirements](REQUIREMENTS.md)
- [System Architecture](ARCHITECTURE.md)
- [Machine Learning](MACHINE_LEARNING.md)
- [Development Process](DEVELOPMENT_PROCESS.md)
- [Testing and Validation](TESTING.md)
- [Limitations](LIMITATIONS.md)
- [Roadmap](ROADMAP.md)
