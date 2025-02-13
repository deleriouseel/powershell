""" Get the latest study titles from the website and add them to the master list"""


import logging
import requests
import datetime
from datetime import timedelta
from openpyxl import load_workbook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="studiesByDate.log",
)

workbook = "C:/Users/Kristin/OneDrive - North Country Chapel/Studies by Date.xlsx"
url="https://northcountrychapel.com/wp-json/wp/v2/posts?categories=48&per_page=3"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# def getDates to get the previous weekend's dates
def getDates():
    #ISO 0 = year, 1 = week number, 2 = day of week
    week_day = datetime.datetime.now().isocalendar()[2]
    #friday last week, sunday this week, monday this week
    days = [2,0,-1]
    dates = []
    for day in days: 
        lastWeekend = datetime.datetime.now() - datetime.timedelta(days=week_day) - datetime.timedelta(day)
        dates.append(lastWeekend.strftime("%Y-%m-%d"))
    logging.info(dates)    
    return dates

def getAPI(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        posts = response.json()
        dates_to_studies = {}  # Dictionary to map dates to studies
        
        # Process each post
        for post in posts:
            try:
                title = post.get("title", {}).get("rendered", "Missing Title")
                date = post.get("date", "").split("T")[0]  # Get date from post, strip time
                if date:
                    dates_to_studies[date] = title
            except (KeyError, AttributeError) as e:
                logging.warning(f"Error processing post: {e}")
        
        # Get the dates we're looking for
        target_dates = getDates()
        
        # Create list of studies matching our target dates
        processed_studies = []
        for date in target_dates:
            study = dates_to_studies.get(date, "No Study Available")
            processed_studies.append(study)
            if study == "No Study Available":
                logging.warning(f"No study found for date: {date}")
            
        logging.info(f"Processed studies: {processed_studies}")
        return processed_studies
        
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return ["API Error"] * 3


def writeData(dates, studies, workbook_path):
    if len(dates) != len(studies):
        logging.warning(f"Mismatch between dates ({len(dates)}) and studies ({len(studies)})")
    
    try:
        current_workbook = load_workbook(workbook_path)
        current_workbook.iso_dates = True
        worksheet = current_workbook["Studies by Date"]
        
        zippered = []
        for date, study in zip(dates, studies):
            zippered.append(date)
            zippered.append(study or "No Study")  # Handle None values
            
        logging.info(f"Writing data: {zippered}")
        worksheet.append(zippered)
        current_workbook.save(workbook_path)
        current_workbook.close()
        
    except Exception as e:
        logging.error(f"Error writing to Excel: {e}")
        raise

def main():
    workbook_path = "C:/Users/Kristin/OneDrive - North Country Chapel/Studies by Date.xlsx"
    url = "https://northcountrychapel.com/wp-json/wp/v2/posts?categories=48&per_page=3"
    
    try:
        logging.info("Starting script")
        dates = getDates()
        studies = getAPI(url)
        writeData(dates, studies, workbook_path)
        logging.info("Script completed successfully")
        
    except Exception as e:
        logging.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()