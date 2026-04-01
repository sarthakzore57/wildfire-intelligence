# Forest Fire Prediction System

An AI-powered web application that predicts forest fire occurrences using real-time environmental data, satellite imagery, and machine learning models to provide early warnings and mitigate wildfire risks.

## Project Overview

This system analyzes weather conditions, vegetation dryness, and historical fire data to predict high-risk areas, helping governments, firefighters, and environmental organizations respond more effectively to potential fire outbreaks.

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
- SQLite for local development
- PostgreSQL for containerized deployments
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
- Docker and Docker Compose
- PostgreSQL (only required for Docker mode)
- InfluxDB (optional in local mode)

### Quickstart
To run the project locally without Docker:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

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

The default local setup uses SQLite, so PostgreSQL is not required unless you switch `USE_SQLITE=False`.

### Frontend Setup
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Set up environment variables (copy `.env.example` to `.env` and fill in values)
4. Run the development server: `npm run dev`

### Docker Setup
1. Make sure Docker and Docker Compose are installed
2. Copy the example env files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Build and start the containers:

```bash
docker compose up --build
```

Docker runs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`
- InfluxDB: `localhost:8086`

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

## Deployment

This application can be deployed using Docker containers to various cloud platforms:
- AWS
- Google Cloud Platform
- Heroku
- Firebase

Detailed deployment instructions are available in the `deployment` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
