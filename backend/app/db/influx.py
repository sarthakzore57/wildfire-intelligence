import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if influxdb_client is available
try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
    INFLUXDB_AVAILABLE = True
except ImportError:
    logger.warning("InfluxDB client library not installed. Time-series data features will be disabled.")
    INFLUXDB_AVAILABLE = False

from app.core.config import settings

def get_influxdb_client():
    """
    Return a client for InfluxDB operations.
    Returns None if InfluxDB client is not available.
    """
    if not INFLUXDB_AVAILABLE:
        logger.warning("InfluxDB client not available. Returning None.")
        return None
    
    try:
        client = InfluxDBClient(
            url=settings.INFLUXDB_URL, 
            token=settings.INFLUXDB_TOKEN, 
            org=settings.INFLUXDB_ORG
        )
        return client
    except Exception as e:
        logger.error(f"Error connecting to InfluxDB: {e}")
        return None

def get_write_api():
    """
    Return a write API instance for InfluxDB.
    Returns None if InfluxDB client is not available.
    """
    client = get_influxdb_client()
    if client is None:
        return None
    
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        return write_api
    except Exception as e:
        logger.error(f"Error getting write API: {e}")
        return None

def get_query_api():
    """
    Return a query API instance for InfluxDB.
    Returns None if InfluxDB client is not available.
    """
    client = get_influxdb_client()
    if client is None:
        return None
    
    try:
        query_api = client.query_api()
        return query_api
    except Exception as e:
        logger.error(f"Error getting query API: {e}")
        return None 