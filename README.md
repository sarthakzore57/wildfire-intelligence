# Forest Fire Prediction System

An AI-powered web application that predicts forest fire occurrences using real-time environmental data, satellite imagery, and machine learning models to provide early warnings and mitigate wildfire risks.

## Project Overview

This system analyzes weather conditions, vegetation dryness, and historical fire data to predict high-risk areas, helping governments, firefighters, and environmental organizations respond more effectively to potential fire outbreaks.

## Problem Statement

The Forest Fire Prediction System is designed to leverage real-time environmental data, satellite imagery, and historical fire records to identify fire-prone regions at an early stage. The proposed platform combines predictive analytics with a cloud-based application architecture to support more accurate fire-risk monitoring and earlier warning generation. By bringing together meteorological parameters, remote-sensing indicators, and historical incident patterns, the system aims to help operators monitor wildfire conditions through a single digital interface.

## Work Completed Till Date

- Built the frontend application using React and Vite with dedicated pages for login, registration, dashboard, alerts, profile, historical data, and fire-risk visualization.
- Implemented the backend API using FastAPI with structured routes for authentication, users, fire-risk zones, fire incidents, alerts, and prediction workflows.
- Integrated Firebase-based storage for core application data, including user records, fire-risk zones, incidents, saved regions, and alerts.
- Added authentication flow for operator account creation, login, protected routes, and current-user access.
- Implemented fire-risk management flows, including viewing zones, viewing incidents, saving monitored regions, and managing alerts.
- Added prediction endpoints that simulate fire-risk scoring and fire-spread forecasting to validate the end-to-end application flow.
- Connected the frontend to backend APIs so that the interface can consume authentication, risk, incident, and alert data from the server.
- Cleaned the project structure by removing unused Docker, duplicate, debug, and stray test files from the repository.
- Updated project documentation for the current local setup and Firebase-based backend configuration.

## Current Status

The project currently has a working full-stack structure with a usable interface, backend service layer, API integration, and Firebase connectivity. The present prediction workflow is a prototype implementation that demonstrates the expected system behavior and data flow, but it is not yet a finalized machine learning model trained on production wildfire datasets.

## Remaining Work

- Enable and finalize Google Cloud Firestore in the Firebase project for persistent production use.
- Replace prototype prediction logic with trained machine learning models for real fire-risk estimation.
- Complete ingestion and preprocessing pipelines for live meteorological and satellite data sources.
- Migrate or refactor older SQL-oriented utility scripts so they align fully with the Firebase-based backend.
- Add stronger validation, better operator-facing error messages, and production-ready alert delivery workflows.
- Improve testing coverage for backend APIs, data services, and frontend user flows.

### Target Audience

- Government Agencies: For disaster preparedness and resource allocation
- Firefighters: To prioritize high-risk zones for monitoring and response
- Environmental Organizations: To track fire risks and advocate for preventive measures
- General Public: For awareness of fire risks in their area

## Features

- Real-Time Fire Risk Dashboard with interactive maps showing fire risk zones
- Early Warning System with alerts via email, SMS, or in-app notifications
- Fire Spread Prediction simulation based on current conditions and historical data
- Historical Fire Analysis to view past fire incidents and patterns
- User Customization for monitored regions and alert thresholds

Dashboard:
<img width="1763" alt="Screenshot 2025-03-28 at 5 20 50 PM" src="https://github.com/user-attachments/assets/22e434b0-da40-4af9-a86c-f69c5fbd2bd1" />


Fire Risk Map with spread predictor:
<img width="1782" alt="Screenshot 2025-03-28 at 5 21 47 PM" src="https://github.com/user-attachments/assets/adcf8904-c5ce-440d-881f-cb39f4d4bcbd" />
<img width="1458" alt="Screenshot 2025-03-28 at 5 22 27 PM" src="https://github.com/user-attachments/assets/109d1c48-a2b9-43b2-a36e-aec02bce6bd1" />


Alerts:
<img width="1781" alt="Screenshot 2025-03-28 at 5 22 54 PM" src="https://github.com/user-attachments/assets/1f4b6ed0-c532-4ff3-9fe6-6030dbf9e076" />


Profile Page:
<img width="1781" alt="Screenshot 2025-03-28 at 5 23 10 PM" src="https://github.com/user-attachments/assets/c8891142-d4c7-46f6-9063-0573f9d7e9d8" />

## Tech Stack

### Frontend
- React.js for interactive UI
- Vite for the modern frontend build/dev server
- D3.js, Leaflet.js for visualizations and maps
- Tailwind CSS for styling

### Backend
- FastAPI with Python
- Firebase Firestore for primary application data
- InfluxDB for time-series data

### AI/ML
- TensorFlow/PyTorch for model training and inference
- Models for satellite imagery analysis, time-series forecasting, and fire spread simulation

### Data Sources
- Satellite Data: NASA FIRMS, Sentinel-2, MODIS, VIIRS
- Meteorological Data: NOAA, ECMWF, NWS APIs
- Historical Fire Data: Kaggle datasets, government records

## Setup and Installation

### Prerequisites
- Python 3.12 recommended
- Node.js 22 recommended
- InfluxDB (optional in local mode)
- Firebase service-account credentials JSON

### Quickstart
To run the project locally:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# add your Firebase service account JSON here:
# backend/app/core/config/firebase-credentials.json

# backend
cd backend
py -3.12 -m venv .venv312
.venv312\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open:
- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`

### Backend Setup
1. Clone the repository
2. Navigate to the backend directory: `cd backend`
3. Create a virtual environment: `py -3.12 -m venv .venv312`
4. Activate the virtual environment:
   - Windows: `.venv312\Scripts\activate`
   - Unix/MacOS: `source .venv312/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Set up environment variables (copy `.env.example` to `.env` and fill in values)
7. Run the development server: `python -m uvicorn app.main:app --reload`

The backend now uses Firebase/Firestore as its primary database, so make sure `backend/.env` points to a valid Firebase credentials JSON file.

### Frontend Setup
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Set up environment variables (copy `.env.example` to `.env` and fill in values)
4. Run the development server: `npm run dev`

## Data Integration

The system includes scripts for importing and processing fire data:

### Available Scripts

- `scripts/setup.py`: Sets up the necessary directories and checks for required data files
- `scripts/init_db.py`: Initializes the database with required tables
- `scripts/import_historical_fire_data.py`: Imports historical fire data from USFS and NASA FIRMS
- `scripts/realtime_fire_data.py`: Fetches real-time fire data from NASA FIRMS, NIFC, and NOAA

### Running Data Scripts

To run the data scripts individually:

```bash
cd backend
.venv312\Scripts\python scripts/setup.py
.venv312\Scripts\python scripts/init_db.py
.venv312\Scripts\python scripts/import_historical_fire_data.py
.venv312\Scripts\python scripts/realtime_fire_data.py
```

For automatic updates, set up a cron job (Linux/macOS) or Task Scheduler (Windows) to run `realtime_fire_data.py` periodically.

### API Keys

Some data sources require API keys. Set these in your `.env` file:

```
NASA_FIRMS_API_KEY=your_api_key_here
NOAA_API_KEY=your_api_key_here
```

## API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
