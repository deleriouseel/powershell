import os
import sys
from datetime import datetime, timedelta

def find_last_consecutive_info(base_directory):
    try:
        # Get all matching files from both 2024 and 2025 directories
        all_files = []
        for year in ['2024', '2025']:
            directory = os.path.join(base_directory, f'apwi{year}')
            if os.path.exists(directory):
                files = [f for f in os.listdir(directory) if f.startswith('apwi') and f.endswith('.mp3')]
                all_files.extend([os.path.join(directory, f) for f in files])

        # Extract dates from filenames and convert to datetime objects
        dates = []
        for file in all_files:
            try:
                filename = os.path.basename(file)
                date_str = filename[4:10]
                date = datetime.strptime(f"20{date_str}", "%Y%m%d")
                dates.append(date)
            except ValueError:
                continue

        if not dates:
            return None, None

        # Sort dates in descending order
        dates.sort(reverse=True)

        # Function to check if date is a weekday (0=Monday, 4=Friday)
        is_weekday = lambda d: d.weekday() <= 4

        latest_date = None
        for current_date in dates:
            if not is_weekday(current_date):
                continue

            # Check all weekdays before this date
            check_date = current_date
            is_consecutive = True

            while True:
                check_date -= timedelta(days=1)

                if not is_weekday(check_date):
                    continue

                if check_date < min(dates):
                    break

                if check_date not in dates:
                    is_consecutive = False
                    break

            if is_consecutive:
                latest_date = current_date
                break

        if latest_date is None:
            return None, None

        # Calculate days since last file
        current_date = datetime.now()
        days_since = (current_date - latest_date).days
        days_remaining = -days_since

        return latest_date, days_remaining

    except Exception:
        return None, None

def print_days_remaining():
    latest_date, days_remaining = find_last_consecutive_info(base_directory)
    if days_remaining is None:
        print(-1)
        exit(1)
    print(days_remaining)
    exit(0)

def print_last_date():
    latest_date, _ = find_last_consecutive_info(base_directory)
    if latest_date is None:
        print(-1)
        exit(1)
    print(latest_date.strftime("%Y-%m-%d"))
    exit(0)

if __name__ == "__main__":
    base_directory = "/mnt/APWI_backup"

    if len(sys.argv) > 1 and sys.argv[1] == "date":
        print_last_date()
    else:
        print_days_remaining()
