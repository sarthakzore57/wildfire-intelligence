# Forest Fire Prediction System - Data Integration Scripts

This directory contains scripts for importing and processing fire data for the Forest Fire Prediction System.

## Available Scripts

### setup.py
Sets up the necessary directories and checks for required data files. It also configures the environment.

```bash
python setup.py
```

### init_db.py
Initializes the SQLite database by creating all necessary tables defined in the SQLAlchemy models.

```bash
python init_db.py
```

### import_historical_fire_data.py
Downloads and imports historical forest fire data from:
1. USFS Wildfire Database
2. NASA FIRMS (Fire Information for Resource Management System)

```bash
python import_historical_fire_data.py
```

### realtime_fire_data.py
Fetches real-time fire data from:
1. NASA FIRMS API
2. National Interagency Fire Center (NIFC) API
3. NOAA Weather Data

```bash
python realtime_fire_data.py
```

### run_all.py
Runs all the scripts in sequence to set up the entire system with one command.

```bash
python run_all.py
```

### retrain_global_model.py
Collects a dataset and retrains the global prediction model with versioned artifacts and registry update.

```bash
python retrain_global_model.py --dataset-source live --samples 1000
```

Historical real-data example:

```bash
python retrain_global_model.py --dataset-source historical --start-date 2025-01-01 --end-date 2025-12-31 --event-limit 200
```

## Setting Up Scheduled Jobs

To keep the system updated with real-time data and model quality, schedule both:

- `realtime_fire_data.py` for incident/risk feeds
- `retrain_global_model.py` for periodic model refresh

### Using Cron (Linux/macOS)

Edit your crontab file:
```bash
crontab -e
```

Add a line to run the script every hour:
```
0 * * * * cd /path/to/project/backend && python scripts/realtime_fire_data.py >> /path/to/project/backend/scripts/logs/realtime_cron.log 2>&1
```

Add a weekly retraining job (example every Sunday at 02:00):
```
0 2 * * 0 cd /path/to/project/backend && python scripts/retrain_global_model.py --dataset-source live --samples 2000 >> /path/to/project/backend/scripts/logs/retrain_cron.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create a new task
3. Set the trigger to run daily or hourly as needed
4. Add an action to start a program: `python` with arguments: `scripts/realtime_fire_data.py`
5. Set the start in directory: `C:\path\to\project\backend`
6. Add a second task for retraining with arguments: `scripts/retrain_global_model.py --dataset-source live --samples 2000`

## Data Sources

The scripts use the following data sources:

1. **USFS Wildfire Database**: Historical wildfire data from the US Forest Service
2. **NASA FIRMS**: Fire Information for Resource Management System, providing near real-time fire hotspot data
3. **National Interagency Fire Center**: Provides information on current wildfire incidents
4. **NOAA Weather Service**: Weather data for risk calculation

## API Keys

Some data sources require API keys. You can set these in your `.env` file:

```
NASA_FIRMS_API_KEY=your_api_key_here
NOAA_API_KEY=your_api_key_here
```

## Troubleshooting

If you encounter issues:

1. Check the log files in the `logs` directory
2. Verify your API keys are set correctly in the `.env` file
3. Ensure the database is properly initialized
4. Check network connectivity for API access
5. Make sure the script paths and imports are correct

## Example Usage

To run the complete setup process:

```bash
cd /path/to/project/backend
python scripts/run_all.py
```

To update only the real-time data:

```bash
cd /path/to/project/backend
python scripts/realtime_fire_data.py
``` 

To retrain the global model:

```bash
cd /path/to/project/backend
python scripts/retrain_global_model.py --dataset-source live --samples 1000
```
