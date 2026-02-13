import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal, UsageLog, init_db

def hms_to_seconds(hms_str):
    try:
        h, m, s = map(int, hms_str.split(':'))
        return h * 3600 + m * 60 + s
    except Exception:
        return 0

def ingest_data(file_path: str):
    print(f"Starting ingestion from {file_path}...")
    
    # Initialize DB
    init_db()
    db = SessionLocal()
    
    try:
        df = pd.read_csv(file_path, skipinitialspace=True)
        logs = []
        for _, row in df.iterrows():
            # Parse start_time
            # Ensure we handle potential leading/trailing spaces in values too
            username = str(row['username']).strip()
            mac_address = str(row['mac_address']).strip()
            start_time_str = str(row['start_time']).strip()
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            
            usage_time_str = str(row['usage_time']).strip()
            usage_seconds = hms_to_seconds(usage_time_str)
            
            # Convert units: Assuming input is Bytes, converting to Kilobits
            # Kilobits = (Bytes * 8) / 1000
            upload_kb = (float(row['upload']) * 8) / 1000
            download_kb = (float(row['download']) * 8) / 1000
            
            log = UsageLog(
                username=username,
                mac_address=mac_address,
                start_time=start_time,
                usage_time_seconds=usage_seconds,
                upload_kb=upload_kb,
                download_kb=download_kb
            )
            logs.append(log)
            
        db.bulk_save_objects(logs)
        db.commit()
        print(f"Successfully ingested {len(logs)} records.")
    except Exception as e:
        db.rollback()
        print(f"Error during ingestion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset.csv'))
    ingest_data(csv_path)
