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

# def getAPI(num,url):
def getAPI(url):
    response = requests.get(url,headers=headers)
    if response.status_code == 200:
        studies = response.json()
        studies = [post["title"]["rendered"] for post in studies]
        studies.reverse()
        logging.info(studies)
        return studies

    else:
        logging.error(f"Error: {response.status_code} - {response.reason}")
    


# def writeData():
def writeData(dates,studies, workbook):
    current_workbook = load_workbook(workbook)
    current_workbook.iso_dates = True
    worksheet = current_workbook["Studies by Date"]
    
    zippered = []
    for date,study in zip(dates,studies):
        zippered.append(date)
        zippered.append(study)
    logging.info(zippered)
    worksheet.append(zippered)
    current_workbook.save(workbook)
    current_workbook.close()


try: 
    dates = getDates()
    studies = getAPI(url)

    writeData(dates,studies,workbook)
except Exception as e:
    logging.error(e)

