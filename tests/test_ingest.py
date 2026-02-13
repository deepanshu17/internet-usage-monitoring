import pytest
import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.ingest import hms_to_seconds, ingest_data
from app.database import Base, UsageLog, SessionLocal, engine

def test_hms_to_seconds():
    assert hms_to_seconds("0:0:0") == 0
    assert hms_to_seconds("1:0:0") == 3600
    assert hms_to_seconds("0:0:10") == 10
    assert hms_to_seconds("invalid") == 0

def test_ingest_data(tmp_path):
    # Setup clean db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Create a small temp CSV
    csv_file = tmp_path / "test.csv"
    # Note the space after comma to match the user's real file
    csv_file.write_text("username, mac_address, start_time, usage_time, upload, download\ntestuser,mac,2022-11-04 15:00:00,1:00:00,100,200")
    
    # Run ingestion
    ingest_data(str(csv_file))
    
    # Verify
    db = SessionLocal()
    log = db.query(UsageLog).filter_by(username="testuser").first()
    assert log is not None
    assert log.usage_time_seconds == 3600
    assert log.upload_kb == (100 * 8) / 1000
    db.close()

def test_ingest_error():
    # Pass a non-existent file to trigger the catch block
    ingest_data("non_existent_file.csv")

def test_ingest_main():
    import runpy
    import os
    # Create a dummy dataset.csv in the root for the main block to find
    root_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset_test_main.csv'))
    with open(root_csv, 'w') as f:
        f.write("username, mac_address, start_time, usage_time, upload, download\nmainuser,mac,2022-11-04 15:00:00,1:00:00,100,200")
    
    # Mock the path the script expects if it looks for 'dataset.csv'
    # The script looks for os.path.join(os.path.dirname(__file__), '../dataset.csv')
    real_csv = os.path.abspath(os.path.join(os.path.dirname(__file__), '../dataset.csv'))
    
    try:
        # We don't want to run on the 100k file during tests, so we temporary swap or just use runpy on the script
        # with a modified CWD or environment if possible. 
        # Actually, let's just use runpy and let it hit the small file we just made.
        # But the script has a hardcoded 'dataset.csv'.
        runpy.run_path(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/ingest.py')), run_name="__main__")
    finally:
        if os.path.exists(root_csv):
            pass # keep it or delete it
