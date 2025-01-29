import os
from datetime import datetime, timedelta
import logging

def find_last_consecutive_date(directory):
    """
    Find the latest consecutive date in the apwi directory.   """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename='complete_radio_files.log'
    )
    
    # Get all matching files
    logging.debug(f"Scanning directory: {directory}")
    files = [f for f in os.listdir(directory) if f.startswith('apwi') and f.endswith('.mp3')]
    logging.debug(f"Found {len(files)} matching files")
    
    # Extract dates from filenames and convert to datetime objects
    dates = []
    for file in files:
        try:
            # Extract date
            date_str = file[4:10]
            # Convert to datetime (assuming 20xx year)
            date = datetime.strptime(f"20{date_str}", "%Y%m%d")
            dates.append(date)
            logging.debug(f"Processed file: {file} -> {date.strftime('%Y-%m-%d')}")
        except ValueError:
            logging.warning(f"Could not parse date from filename: {file}")
            continue
    
    if not dates:
        logging.warning("No valid dates found in files")
        return None
    
    # Sort dates in descending order
    dates.sort(reverse=True)
    logging.info(f"Last file date: {dates[0].strftime('%Y-%m-%d')}")
    logging.info(f"First file date: {dates[-1].strftime('%Y-%m-%d')}")
    
    # Function to check if date is a weekday (0=Monday, 4=Friday)
    is_weekday = lambda d: d.weekday() <= 4
    
    latest_date = None
    for current_date in dates:
        if not is_weekday(current_date):
            logging.debug(f"Skipping weekend date: {current_date.strftime('%Y-%m-%d')}")
            continue
            
        logging.debug(f"Checking dates before: {current_date.strftime('%Y-%m-%d')} ({current_date.strftime('%A')})")
        
        # Check all weekdays before this date
        check_date = current_date
        is_consecutive = True
        
        while True:
            # Move to previous day
            check_date -= timedelta(days=1)
            
            # Skip weekends
            if not is_weekday(check_date):
                logging.debug(f"Skipping weekend: {check_date.strftime('%Y-%m-%d')}")
                continue
                
            # If we've gone back before any possible files, we're done
            if check_date < min(dates):
                logging.debug(f"Earliest date: {check_date.strftime('%Y-%m-%d')}")
                break
                
            # If this weekday's file is missing, sequence is broken
            if check_date not in dates:
                logging.debug(f"Missing file for date: {check_date.strftime('%Y-%m-%d')} ({check_date.strftime('%A')})")
                is_consecutive = False
                break
            
            logging.debug(f"Found file for date: {check_date.strftime('%Y-%m-%d')}")
        
        if is_consecutive:
            latest_date = current_date
            logging.info(f"Last consecutive date: {latest_date.strftime('%Y-%m-%d')} ({latest_date.strftime('%A')})")
            break
        else:
            logging.info(f"Date {current_date.strftime('%Y-%m-%d')} is not consecutive")
    
    if latest_date is None:
        logging.warning("No consecutive dates found")
    
    return latest_date

# Example usage:
if __name__ == "__main__":
    directory = "//10.10.0.85/APWI_backup/apwi2025" 
    result = find_last_consecutive_date(directory)
    
    if result:
        print(f"Latest consecutive date: {result.strftime('%Y-%m-%d')}")
    else:
        print("No consecutive dates found")