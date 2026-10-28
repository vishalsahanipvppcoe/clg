# MediScan AI — Codebase Audit Report

**Audit Date:** October 2026  
**Repository:** [https://github.com/vishalsahanipvppcoe/clg](https://github.com/vishalsahanipvppcoe/clg)  
**Auditor Role:** Senior Software Engineer, QA Engineer & Technical Writer  
**Local Path:** `D:\Dusre_ka_projects_testing\shetty_project`  

---

## 1. Executive Summary

A comprehensive, risk-aware codebase audit was conducted on the **MediScan AI** project (Early Disease Detection System). The audit inspected directory structure, frontend source code, backend API implementation, machine learning inference logic, security controls, dependency declarations, and configuration files.

The project is a full-stack medical radiograph screening platform consisting of a **React 18 + Vite + Tailwind CSS** frontend and a **Python Flask + PyTorch** backend. It features multi-modality heuristic scan routing, medical image gating, multi-disease classification (CheXNet, MURA, TB-Net), explainable AI (Grad-CAM++ heatmaps), confidence interpretation with clinical uncertainty bands, and PDF clinical report generation.

---

## 2. Verification & Test Execution Results

| Check Category | Command / Inspection | Result | Findings & Details |
| :--- | :--- | :--- | :--- |
| **Python Syntax Compilation** | `python -m compileall -q backend` | **PASS** | All 40+ Python modules compiled cleanly without syntax or indentation errors. |
| **Frontend Production Build** | `npm run build` (Vite 5.4) | **PASS** | Successfully bundled 1,678 modules into production assets in 36.06s (`dist/index.html`, `dist/assets/index-*.js`, `dist/assets/index-*.css`). |
| **Frontend Static Analysis** | `npm run lint` (ESLint 9) | **FAIL (Lint)** | 11 problems (3 TypeScript errors: empty interface definitions in shadcn `command.tsx` & `textarea.tsx`, and `require()` in `tailwind.config.ts`; 8 React Fast Refresh warnings). Original code preserved per policy. |
| **Backend Automated Tests** | `pytest backend/tests/` | **BLOCKED** | Host machine Python 3.14/3.12 lacks `torch`, `flask`, and `pytest` in global scope; dependency installation is restricted by safety policy. Verified that GitHub Actions CI (`.github/workflows/backend-ci.yml`) is configured for Python 3.11 with CPU PyTorch. |
| **Security & Secrets Review** | Recursive regex inspection | **PASS** | No private API keys, tokens, hardcoded database credentials, or `.env` files detected in repository tracking. |
| **Medical Data Privacy** | Inspection of `uploads/` directories | **PASS** | Upload folders contain only `.gitkeep`. Uploaded test scans are ignored in `.gitignore` and ephemeral server uploads are securely deleted after processing with retry handlers. |
| **Git Remote Connectivity** | `git ls-remote --heads origin` | **PASS** | Remote `origin` ([https://github.com/vishalsahanipvppcoe/clg.git](https://github.com/vishalsahanipvppcoe/clg.git)) is active, authenticated, and branch `main` is published. |

---

## 3. Verified Feature Inventory

Every feature was evaluated against actual source code implementations:

| Feature Name | Implemented Status | Implementing Files | Description & Verification Evidence |
| :--- | :--- | :--- | :--- |
| **Multi-Scan Analysis API** | **Implemented** | `backend/app.py` (`/api/analyze`) | Multipart endpoint supporting PNG, JPG, JPEG, and DICOM (`.dcm`). Includes file validation, request ID tracing (`X-Request-ID`), model execution, and JSON results. |
| **Non-Medical Image Gatekeeper** | **Implemented** | `backend/models/medical_validator.py` | 7-rule heuristic statistical engine (grayscale dominance, contrast, dynamic range, exposure bounds, resolution) to reject non-medical uploads (selfies, memes) with HTTP 422 `not_medical_image`. |
| **Modality Auto-Routing** | **Implemented** | `backend/app.py` (`infer_scan_type_from_image`) | Computer vision heuristic pipeline analyzing bilateral lung symmetry, horizontal rib structures, bone edge density, and DICOM metadata to classify scans as Chest, Bone, or CT. |
| **CheXNet 14-Disease Classifier** | **Implemented** | `backend/models/chexnet_inference.py`, `backend/datasets/CheXNet/model.pth.tar` | DenseNet-121 architecture predicting 14 pathologies (Atelectasis, Cardiomegaly, Effusion, Infiltration, Mass, Nodule, Pneumonia, Pneumothorax, Consolidation, Edema, Emphysema, Fibrosis, Pleural Thickening, Hernia). Model weights (`model.pth.tar`, 84.1 MB) are present and verified. |
| **MURA Bone Abnormality Detection** | **Implemented** | `backend/models/mura_inference.py` | DenseNet-169 backbone ensembled with OpenCV edge & texture heuristics (`dl_prob * 0.70 + cv_prob * 0.30`) for musculoskeletal radiographs. |
| **Tuberculosis Screening** | **Implemented** | `backend/models/tuberculosis_inference.py` | Dedicated TB detection module with PyTorch backbone and OpenCV symmetry/intensity fallback. |
| **RSNA Intracranial Hemorrhage Detection** | **Partially Implemented** | `backend/models/rsna_inference.py` | ResNet-50 architecture and DICOM parser implemented; requires external checkpoint directory `backend/datasets/rsna18` for full runtime inference (returns 503 unavailable when weights are absent). |
| **UNet Image Segmentation** | **Partially Implemented** | `backend/models/unet_inference.py` | Encoder-decoder segmentation logic implemented; requires checkpoint `backend/datasets/UNet/MODEL.pth` to run (returns 503 unavailable when missing). |
| **Explainable AI (Grad-CAM++)** | **Implemented** | `backend/models/gradcam.py` | Second-order gradient-weighted CAM generating 3 visual modes: Overlay (smooth Gaussian heatmap), Focus (soft threshold with dimmed background), and Regions (bounding boxes on top pathological areas). Encoded as Base64 data URLs. |
| **Clinical Confidence Interpreter** | **Implemented** | `backend/models/confidence_interpreter.py` | Formats raw confidence values into clinical likelihood bands ("AI Suggests Possible Finding"), calculates uncertainty bands (±5-10%), and attaches mandatory medical disclaimers. |
| **PDF Medical Report Generator** | **Implemented** | `backend/report_generator.py` (`/api/report`) | Generates clinical summary PDF documents via `fpdf2` containing patient reference, scan metadata, findings table, risk status, and disclaimer. |
| **Interactive Medical UI** | **Implemented** | `frontend/src/` | Single-page application built with React 18, Vite, and Tailwind CSS. Features drag-and-drop upload, real-time heatmap mode switcher, interactive severity badges, and dark/light themes. Verified via production build. |
| **Model Discovery & Health Endpoints** | **Implemented** | `backend/app.py` (`/health`, `/models`) | Exposes operational health status and dynamically reports which models are currently available based on filesystem checkpoint checks. |
| **Direct Predict Endpoints** | **Implemented** | `backend/app.py` (`/predict/<model>`, `/predict/all`) | Secondary REST endpoints allowing explicit model targeting or simultaneous execution across all available models. |
| **Training & Data Download CLI** | **Planned / Missing** | Referenced in `EXPLAINATION.txt` | `backend/train_models.py` and `backend/data_pipeline/download_datasets.py` were referenced in developer notes but are absent from the repository. |

---

## 4. Security & Data Protection Review

1. **No Sensitive Medical Scans Stored**:
   - `backend/uploads/` and root `uploads/` only retain `.gitkeep` files.
   - All uploaded temporary scan files are purged immediately following prediction or upon unexpected exceptions using the `safe_remove()` retry utility.
2. **Exclusion of Large Binaries & Credentials**:
   - `.gitignore` properly excludes `*.rar`, `*.env*`, `*.pem`, `*.key`, `node_modules/`, `dist/`, and Python cache artifacts.
3. **CORS Policy**:
   - Backend CORS is configured with `CORS(app, origins="*")` for development and includes environment variable hooks (`FRONTEND_URL`) for production lockdown.
4. **Input Sanitization**:
   - File uploads are validated via `secure_filename()` to prevent directory traversal attacks.
   - Files are constrained to allowed extensions (`.png`, `.jpg`, `.jpeg`, `.dcm`) and a strict 15 MB server limit.

---

## 5. Known Limitations & Recommendations

1. **Missing Heavy Weight Checkpoints**:
   - `rsna18` (Brain CT) and `UNet` (Segmentation) models require large external checkpoint files to be placed in `backend/datasets/` to enable runtime execution.
   - The API gracefully handles this by returning HTTP 503 with `"disease": "Model Unavailable"`.
2. **Host Python Environment**:
   - Local automated testing requires a Python virtual environment with PyTorch and Flask installed. GitHub Actions CI (`.github/workflows/backend-ci.yml`) is already configured to run these tests in a clean container.
3. **Frontend Linting**:
   - 3 minor TypeScript interface / import syntax items exist in UI library files. These do not hinder Vite bundling or runtime execution.
4. **Clinical Disclaimer**:
   - MediScan AI is an educational and decision-support prototype. Predictions must not be used as standalone clinical diagnoses without professional physician review.
