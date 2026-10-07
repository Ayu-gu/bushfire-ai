# 🔥 FireScope AI

## Neural Network-Based Bushfire Risk Assessment & Decision Support System

FireScope AI is a full-stack bushfire risk assessment platform that uses a trained **PyTorch neural network** to estimate bushfire risk from weather and environmental conditions.

The system combines machine learning, environmental data, geospatial analysis and an interactive web interface into a deployed decision-support platform.

**Live deployment:** https://2026s2a2.winproject.com.au/

---

## Overview

Bushfire risk is influenced by multiple interacting environmental factors rather than a single measurement such as temperature.

FireScope was developed to explore how these factors can be combined within a machine-learning pipeline and delivered through an accessible web application.

A user can select or detect a location, retrieve relevant environmental observations and run a bushfire risk assessment through the trained model. The result is presented through an interactive dashboard designed to make the underlying environmental conditions and model output easier to understand.

---

## System Architecture

```text
React Frontend / Interactive Dashboard / Leaflet Map
                        |
                    HTTP / REST
                        |
                Node.js / Express API
                        |
                 Model Invocation
                        |
                  Python Service
                        |
               Feature Engineering
                        |
              PyTorch Neural Network
                        |
                 Risk Prediction
                        |
          Environmental & Geospatial Data
```

---

## Neural Network

FireScope uses a feed-forward neural network implemented with **PyTorch**.

```text
Input: 15 features
       |
       v
Linear 15 → 32
ReLU
       |
       v
Linear 32 → 16
ReLU
       |
       v
Linear 16 → 8
ReLU
       |
       v
Linear 8 → 1
       |
       v
Bushfire Risk Prediction
```

The model operates on 15 engineered environmental features:

- Month
- Day of year
- Season
- Maximum temperature
- Minimum temperature
- Average humidity
- Maximum wind
- Rain today
- Rain over the previous 7 days
- Rain over the previous 30 days
- Days since rain
- Temperature-humidity index
- Temperature-wind index
- Humidity-wind index
- Rolling dryness

Model development includes feature preprocessing and evaluation using **accuracy, precision, recall, F1 score, ROC-AUC and confusion matrix analysis**.

---

## Key Features

- **Location-based risk assessment** — analyse conditions for a selected or detected location.
- **Interactive mapping** — React and Leaflet support geographic selection and visualisation.
- **Environmental data pipeline** — observations are transformed into the model's expected feature structure.
- **Neural network inference** — engineered features are processed by the trained PyTorch model.
- **Full-stack integration** — React, Node.js/Express and Python operate as a connected system.
- **Live Linux deployment** — the application is publicly deployed rather than operating only locally.

---

## Technology Stack

| Area | Technologies |
| --- | --- |
| Frontend | React, Vite, JavaScript, HTML, CSS |
| Mapping | Leaflet |
| Backend | Node.js, Express |
| Machine Learning | Python, PyTorch, scikit-learn |
| Data Processing | pandas, NumPy |
| API / Networking | REST, HTTP, JSON |
| Deployment | Ubuntu Linux, SSH, Nginx |
| Version Control | Git, GitHub |

---

## Deployment & Infrastructure

FireScope is deployed on an **Ubuntu Linux server**.

Deployment and troubleshooting work has included SSH administration, frontend/backend deployment, Node.js service execution, Python model integration, port and API connectivity testing, Nginx reverse-proxy configuration, persistent backend execution and frontend-to-backend communication testing.

During deployment, the backend initially terminated when its SSH terminal session ended. The issue was traced to the application process being tied to the interactive shell session. A persistent execution approach was implemented and Nginx routing was verified, restoring reliable communication between the public frontend and backend service.

This provided practical experience with the difference between software that works locally and a system that must operate reliably in a server environment.

---

## Project Structure

```text
bushfire-ai/
├── frontend-react/       # React/Vite dashboard
├── models/               # Trained model checkpoints
├── src/                  # Python model/data pipeline
├── .gitignore
├── README.md
└── package-lock.json
```

---

## Engineering Workflow

```text
Data Collection
      ↓
Data Cleaning
      ↓
Feature Engineering
      ↓
Model Training
      ↓
Model Evaluation
      ↓
Backend Integration
      ↓
Frontend Integration
      ↓
Local Testing
      ↓
Linux Deployment
      ↓
Production Troubleshooting
      ↓
Iteration
```

---

## Engineering Challenges

### Model ↔ Application Integration
The prediction pipeline transforms application inputs into the same feature representation used during training and returns model output in a form consumable by the application.

### Frontend ↔ Backend Communication
Development required testing API routes, ports and request/response behaviour across application components.

### Local ↔ Production Environment
Server processes, network ports, reverse-proxy routing and service persistence required independent troubleshooting after deployment.

### Geospatial Data
Location-based assessment required combining geographic coordinates with environmental and elevation-related data while maintaining a consistent model-input pipeline.

---

## Current Status

- [x] Trained PyTorch neural network
- [x] Environmental feature-engineering pipeline
- [x] React dashboard
- [x] Interactive Leaflet map
- [x] Location-based analysis
- [x] Node.js/Express backend
- [x] Python model integration
- [x] Linux server deployment
- [x] Nginx reverse proxy
- [x] Public live application
- [ ] Further model validation
- [ ] Expanded environmental datasets
- [ ] Additional deployment automation
- [ ] Monitoring and observability improvements

---

## Important Notice

FireScope is an **educational and experimental decision-support project**. Predictions generated by the system should not be treated as official bushfire warnings, emergency advice or a replacement for information provided by emergency services and government authorities.

---

## Live System

**FireScope AI:** https://2026s2a2.winproject.com.au/

---

## Author

**Aiigo**

Infrastructure • Software • Machine Learning
