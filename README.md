# 🚢 Naval Propulsion AI: Multimodal Predictive Maintenance Pipeline

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.2+-orange.svg)](https://scikit-learn.org/)
[![SHAP](https://img.shields.io/badge/Explainable%20AI-SHAP-red.svg)](https://shap.readthedocs.io/)
[![React](https://img.shields.io/badge/Frontend-React.js-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **A production-grade, multimodal AI pipeline that fuses unstructured NLP maintenance logs with structured sensor telemetry to predict Remaining Useful Life (RUL) with SHAP-based explainability.**

## 📋 Table of Contents
- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Results & Explainability](#results--explainability)
- [Future Roadmap: Space Tech Pivot](#future-roadmap-space-tech-pivot)

---

## 🌊 The Problem
Naval propulsion systems generate massive amounts of fragmented data:
1. **Structured Telemetry**: High-frequency sensor readings (Temperatures, Pressures, RPMs).
2. **Unstructured Logs**: Human-written technician reports (e.g., *"Noticed slight vibration on port side"*).

Traditional maintenance relies on reactive fixes or simple threshold alarms, leading to costly downtime. Furthermore, "black-box" AI models are often rejected in safety-critical industries because engineers cannot trust *why* a prediction was made.

## 💡 The Solution
I engineered a **Multimodal Diagnostic Pipeline** that bridges the gap between human intuition and machine precision. 
- It uses **NLP** to extract spatial context and symptoms from technician logs.
- It maps these insights to specific physical sensors.
- It feeds this targeted data into a **Random Forest Regressor** to predict Remaining Useful Life (RUL).
- It uses **SHAP (SHapley Additive exPlanations)** to provide transparent, physics-based reasoning for every prediction.

## 🏗️ Architecture

```mermaid
graph TD
    A[Raw Technician Log] -->|NLP Enricher| B(Semantic Analysis)
    C[Sensor Telemetry CSV] -->|Preprocessing| D(Cleaned Data)
    B -->|MultiModal Mapper| E{Targeted Sensors}
    D -->|Feature Extraction| E
    E -->|Input Vector| F[Random Forest RUL Model]
    F -->|Prediction| G[Health Index %]
    F -->|SHAP Values| H[Explainability Engine]
    G --> I[React Dashboard]
    H --> I
