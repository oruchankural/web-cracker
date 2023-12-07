import os
import sys
import mysql.connector
import random
import time
import sys

from mysql.connector import Error
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service as GeckoService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.webdriver.chrome.options import Options
from mysql.connector import Error
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime


def click_element_with_retry(driver, by, value, timeout=20):
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()
def get_process_id():
    return os.getpid()
    #return 10536
def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            database="pyhonprocessdb",
            user="root",
            password=""
        )
        if connection.is_connected():
            print("Connected to the database")
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None
def get_row_number(connection, process_id):
    try:
        cursor = connection.cursor(dictionary=True)
        sql_query = "SELECT RowNumber FROM pyhtonprocesses WHERE ProcessId = %s"
        cursor.execute(sql_query, (process_id,))
        result = cursor.fetchone()
        return result['RowNumber'] if result else None
    except Error as e:
        print(f"Error: {e}")
        return None
def get_daily_working_period(connection, process_id):
    try:
        cursor = connection.cursor(dictionary=True)
        sql_query = "SELECT DailyLoopingCount FROM pyhtonprocesses WHERE ProcessId = %s"
        cursor.execute(sql_query, (process_id,))
        result = cursor.fetchone()
        if result and 'DailyLoopingCount' in result and isinstance(result['DailyLoopingCount'], (int, float)):
            return int(result['DailyLoopingCount'])
        else:
            return None
    except Error as e:
        print(f"Error: {e}")
        return None
def insert_log(connection, row_number, message):
    try:
        cursor = connection.cursor()
        sql_query = "INSERT INTO pyhtonprocesslogs (PyhtonProcessRowNumber, Message) VALUES (%s, %s)"
        record_to_insert = (row_number, message)
        cursor.execute(sql_query, record_to_insert)
        connection.commit()
    except Error as e:
        print(f"Error: {e}")
def insert_general_log(connection,message):
    try:
        cursor = connection.cursor()
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql_query = "INSERT INTO logs (Message, Date) VALUES (%s, %s)"
        record_to_insert = (message, current_date)
        cursor.execute(sql_query, record_to_insert)
        connection.commit()
    except Error as e:
        print(f"Error: {e}")
        
def get_working_period_point(connection, process_id, type):
    try:
        cursor = connection.cursor(dictionary=True)
        sql_query = f"SELECT {type} FROM pyhtonprocesses WHERE ProcessId = %s"
        cursor.execute(sql_query, (process_id,))
        result = cursor.fetchone()
        if result and type in result and isinstance(result[type], (int, float)):
            return int(result[type])
        else:
            return None
    except Error as e:
        print(f"Error: {e}")
        return None
def generate_work_duration(connection):
    starting = get_working_period_point(connection, get_process_id(), "PeriodStarting")
    ending = get_working_period_point(connection, get_process_id(), "PeriodEnding")
    return random.randint(starting, ending)
def main():
    start_time = time.time()
    
    
    if len(sys.argv) != 3:
        print("Usage: python script.py <process_id> <keyword>")
        sys.exit(1)
        
    Id = sys.argv[1]
    listing_title = f"listing-title-{Id}"
    search_for_anything = sys.argv[2]

    connection = create_connection()
    if not connection:
        print("Error: Unable to connect to the database.")
        sys.exit(1)

    print(f"Process ID: {get_process_id()}")
    insert_general_log(connection,f"Process Id - {get_process_id()}, Id : {Id}, Keyword : {search_for_anything}")
    
    
    
    looping_count = get_daily_working_period(connection, get_process_id())
    insert_general_log(connection,f"Process Id - {get_process_id()}, Looping Count : {looping_count}")
    
    if looping_count is None:
        print("Error: Unable to retrieve looping count from the database.")
        sys.exit(1)

    max_error_count = 2
    
   
    for work_index in range(1, looping_count + 1):
        try:
            options=Options()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument('--ignore-certificate-errors')
            options.headless=True
            
            '''
                # Set your proxy details
                proxy_host = "your_proxy_host"
                proxy_port = "your_proxy_port"
                proxy_username = "your_proxy_username"
                proxy_password = "your_proxy_password"

                # Set up ChromeOptions
                chrome_options = webdriver.ChromeOptions()

                # Configure proxy
                proxy_string = f"{proxy_host}:{proxy_port}"

                # Add proxy to Chrome options
                chrome_options.add_argument(f'--proxy-server={proxy_string}')

                # If your proxy requires authentication, add the following lines
                chrome_options.add_argument(f'--proxy-auth={proxy_username}:{proxy_password}')
            '''
            # options.add_argument("--disable-application-cache") disable caching
            options.add_argument("--incognito")

            
            driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=options)
            driver.get("https://www.etsy.com")
            
            search = driver.find_element(By.NAME, "search_query")
            search.send_keys(f"{search_for_anything}")
            search.send_keys(Keys.RETURN)
            sleep(1)
    
            if connection:
                row_number = get_row_number(connection, get_process_id())
                if row_number is not None:
                    
                    found = False
                    while not found:
                        listings = driver.find_elements(By.XPATH, "//div[@class='wt-grid wt-pl-xs-0 wt-pr-xs-0 search-listings-group']//h3[@id]")
                        for listing in listings:
                            if listing.get_attribute("id") == f"{listing_title}":
                                sleep(4)
                                current_url=driver.current_url
                                page=current_url[-6:]
                                work_duration_seconds = generate_work_duration(connection)
                                current_date = time.strftime("%d-%m-%Y %H:%M:%S")
                                log_message = f"{current_date} - Worked Counter: {work_index} - Random Looping Sleep : {work_duration_seconds} - Page {page}"
                                time.sleep(work_duration_seconds)  # Wait for the specified duration in seconds
                                insert_log(connection, row_number, log_message)
                                listing.click()
                                found = True
                                break

                        if not found:
                            next_button = driver.find_element(By.XPATH, "//div//nav//ul//li[@class='wt-action-group__item-container']//following::span[text()='Next'][2]//following::span[@class='wt-icon--smaller etsy-icon']")
                            # driver.execute_script("arguments[0].scrollIntoView(true);", next_button) waiting refresh
                            next_button.click()
                            sleep(4)
                            #click_element_with_retry(driver, By.XPATH, "//div//nav//ul//li[@class='wt-action-group__item-container']//following::span[text()='Next'][2]//following::span[@class='wt-icon--smaller etsy-icon']")
                           
                            # driver.execute_script("arguments[0].scrollIntoView(true);", next_button) waiting refresh
                            # next_button.click()
                            # sleep()
                            
                            
                    sleep(5)
                    driver.quit()
                else:
                    connection.close()
                    connection = None
        except Error as e:
            insert_general_log(connection,f"Process Id - {get_process_id()}, Exception : {e}")
            max_error_count -= 1
            print(f"Work #{work_index} - Error: {e}")
            if max_error_count == 0:
                print("Exiting application due to multiple errors.")
                exit()

    elapsed_time = time.time() - start_time
    print(f"Script execution time: {elapsed_time} seconds")

if __name__ == "__main__":
    main()
