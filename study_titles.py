""" Get the latest study titles from the website and add them to the master list"""


import requests
import datetime
from datetime import timedelta
from openpyxl import load_workbook
from logger import get_logger

SCRIPT_NAME = "study_titles"
logger = get_logger(SCRIPT_NAME, __file__)

def log_extra(**kwargs):
    return {"script_name": SCRIPT_NAME, **kwargs}


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
    logger.info(f"getDates dates: {dates}", extra=log_extra())
    return dates

def getAPI(url, target_dates):
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
                logger.error(f"Error processing WP post: {e}", extra=log_extra(event_type="error", error_message=str(e)))

        # Create list of studies matching our target dates
        processed_studies = []
        for date in target_dates:
            study = dates_to_studies.get(date, "No Study Available")
            processed_studies.append(study)
            if study == "No Study Available":
                logger.error(f"No study found for date: {date}",  extra=log_extra(event_type="error", error_message=f"No study found for date: {date}"))
            
        logger.info(f"Processed studies: {processed_studies}", extra=log_extra())
        return processed_studies
        
    except requests.RequestException as e:
        logger.error(f"API request failed: {e}", extra=log_extra(event_type="error", error_message=str(e)))
        return ["API Error"] * 3


def writeData(dates, studies, workbook_path):
    if len(dates) != len(studies):
        logger.warning(f"Mismatch between dates ({len(dates)}) and studies ({len(studies)})", extra=log_extra(event_type="error"))
    
    try:
        current_workbook = load_workbook(workbook_path)
        current_workbook.iso_dates = True
        worksheet = current_workbook["Studies by Date"]
        
        zippered = []
        for date, study in zip(dates, studies):
            zippered.append(date)
            zippered.append(study or "No Study")  # Handle None values
            
        logger.info(f"Writing data: {zippered}", extra=log_extra())
        worksheet.append(zippered)
        current_workbook.save(workbook_path)
        current_workbook.close()
        
    except Exception as e:
        logger.error(f"Error writing to Excel: {e}", extra=log_extra(event_type="error", error_message=str(e)))
        raise

def main():
    workbook_path = "C:/Users/KristinHoppe/OneDrive - North Country Chapel/Studies by Date.xlsx"
    url = "https://northcountrychapel.com/wp-json/wp/v2/posts?categories=48&per_page=3"
    

    try:
 
        dates = getDates()
        studies = getAPI(url, dates)
        writeData(dates, studies, workbook_path)

    except Exception as e:
        logger.error(f"Script failed: {e}",
                 extra=log_extra(event_type="script_stop", exit_status="error", error_message=str(e)))
        raise

if __name__ == "__main__":
    logger.info(f"Starting script: {SCRIPT_NAME}",
        extra=log_extra(event_type="script_start"))
    main()
    logger.info(f"Finished script: {SCRIPT_NAME}",
        extra=log_extra(event_type="script_stop", exit_status="success"))