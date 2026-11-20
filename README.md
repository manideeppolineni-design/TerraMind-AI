# 🌍 TerraMind AI
### Agentic Satellite Intelligence and Flood Impact Analysis

TerraMind AI is an AI-powered geospatial intelligence platform designed to analyze satellite imagery, identify potential flood-affected regions, and generate geographic impact assessments using satellite data, GIS technologies, and intelligent AI agents.

## 🎯 Project Objectives

- Analyze satellite imagery for potential inundation patterns.
- Retrieve and process geospatial information.
- Generate location-specific flood impact assessments.
- Integrate rainfall indicators and historical flood information.
- Use AI agents to generate geographic intelligence reports.
- Support disaster monitoring and decision-making workflows.

## ✨ Key Features

### 🛰️ Satellite Intelligence
- Sentinel-1 satellite data integration.
- Google Earth Engine integration.
- Satellite imagery processing and analysis.
- Potential inundation identification.

### 🌧️ Flood Impact Assessment
- Rainfall assessment.
- Historical flood information.
- Geographic impact summaries.
- Potentially affected area estimation.

### 🤖 Agentic AI Intelligence
- AI-powered analysis and explanation.
- Retrieval-Augmented Generation (RAG).
- Context-aware geographic reasoning.
- Natural-language impact reports.

### 🗺️ Geospatial Intelligence
- Location search and geographic discovery.
- Latitude and longitude-based analysis.
- Geospatial data processing.
- Geographic visualization.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python, JavaScript |
| Backend | FastAPI |
| AI / Agentic AI | LangGraph, RAG, Ollama |
| Satellite Data | Sentinel-1, Google Earth Engine |
| Geospatial Processing | Rasterio, GeoPandas |
| Database | PostgreSQL, PostGIS |
| ORM | SQLAlchemy, GeoAlchemy2 |
| Frontend | HTML, CSS, JavaScript |
| AI Model | Llama 3.2 |
| Development | Git, GitHub, VS Code |

## 🏗️ System Architecture

```text
              USER
               |
               v
       TERRAMIND AI FRONTEND
          HTML / CSS / JS
               |
               v
          FASTAPI BACKEND
               |
       +-------+--------+
       |                |
       v                v
 SATELLITE DATA     GEOSPATIAL DATA
 Sentinel-1         Rasterio
 Google Earth       GeoPandas
 Engine             PostGIS
       |                |
       +-------+--------+
               |
               v
       FLOOD IMPACT ENGINE
               |
               v
         AI AGENT LAYER
       LangGraph + RAG
               |
               v
        OLLAMA / LLAMA
               |
               v
      GEOGRAPHIC IMPACT
           REPORT
```

## 📂 Project Structure

```text
TerraMind-AI/
│
├── backend/
│   ├── main.py
│   ├── ai_agent.py
│   ├── impact_assessment.py
│   └── ...
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── notebooks/
├── data/
├── requirements.txt
├── .gitignore
└── README.md
```

*This is a simplified overview. The actual repository structure may contain additional files.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/TerraMind-AI.git
cd TerraMind-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file containing the required credentials and database connection settings.

Configure Google Earth Engine authentication and PostgreSQL/PostGIS as required.

Never commit `.env` files, API keys, passwords, service-account credentials, or private keys.

### 5. Start the backend

```bash
python -m uvicorn backend.main:app --reload
```

Backend URL:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

### 6. Start the frontend

Open another terminal:

```bash
python -m http.server 5500 --directory frontend
```

Frontend URL:

http://localhost:5500

### 7. AI model configuration

TerraMind AI uses Ollama with the Llama 3.2 model.

Install and configure Ollama, then pull the model:

```bash
ollama pull llama3.2:3b
```

Ensure the Ollama service is running before using AI-powered analysis.

## 🔬 Data Sources

- Sentinel-1: Synthetic Aperture Radar satellite imagery.
- Google Earth Engine: Satellite data access and geospatial processing.
- OpenStreetMap / Photon: Geographic search information.
- Open-Meteo: Geocoding and weather-related data services.
- Historical flood datasets: Supporting historical geographic context.

## ⚠️ Disclaimer

TerraMind AI is an experimental disaster-intelligence and research platform.

Satellite-derived observations and AI-generated assessments should not be treated as verified emergency alerts, official flood warnings, or ground-truth measurements.

Results depend on data availability, satellite acquisition dates, processing methods, and geographic coverage. Independent verification is required before operational or emergency-response decisions.

## 🔮 Future Enhancements

- Real-time satellite data ingestion.
- Advanced flood segmentation using deep learning.
- Infrastructure and population exposure analysis.
- Improved geographic impact estimation.
- Multilingual AI-generated disaster reports.
- Interactive geospatial dashboards.
- Automated disaster intelligence workflows.

## 👨‍💻 Developer

**Hari Krishna Digiventi**

B.Tech – Computer Science and Engineering (AI & ML)

Areas of Interest:
- Artificial Intelligence
- Agentic AI Systems
- Geospatial Intelligence
- Machine Learning
- Satellite Image Analysis

## 📜 License

This project is currently published without an open-source license. All rights are reserved by the project author unless a license is added.

---

⭐ If you find TerraMind AI interesting, consider starring the repository and following its development.

**Building intelligent systems for a safer and more informed world. 🌍**
