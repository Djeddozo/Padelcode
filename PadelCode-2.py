import os
import time
import schedule
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

weekday_convert = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def get_credentials():
    email = os.environ.get("USC_EMAIL")
    password = os.environ.get("USC_PASSWORD")
    missing = [name for name, value in (("USC_EMAIL", email), ("USC_PASSWORD", password)) if not value]
    if missing:
        missing_vars = ", ".join(missing)
        raise ValueError(
            f"Missing credentials: {missing_vars}. Please set USC_EMAIL and USC_PASSWORD in the environment."
        )
    return email, password

def fill_form(target_time):
    email, password = get_credentials()

    # Setup the WebDriver
    options = webdriver.ChromeOptions()
    options.headless = False
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()


    # Timestamp
    print(f"Start login: {datetime.now()}")

    # Open the webpage
    driver.get("https://my.uscsport.nl/pages/login")

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "showEmailLoginButton")) 
    )

    login_button = driver.find_element(By.ID, "showEmailLoginButton")
    login_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "email"))  
    )

    # Log in by filling the fields and clicking login
    email_field = driver.find_element(By.ID, "email")
    email_field.send_keys(email)
    email_field = driver.find_element(By.ID, "password")
    email_field.send_keys(password)
    submit_button = driver.find_element(By.ID, "submit")
    submit_button.click()

    # Wait for search category to load 
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "tag-filterinput"))
    )

    # Locate the search button and then select padel, so that it does not have to do this at execution time
    search_button = driver.find_element(By.ID, "tag-filterinput")
    search_button.click()
    search_button.send_keys("Padel")

    # Wait for the padel category to load 
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "tagCheckbox193"))
    )
    
    # Select padel
    padel_button = driver.find_element(By.ID, "tagCheckbox193")
    padel_button.click()

    # Create variables before booking for speed
    weekday = datetime.today().weekday()
    target_day_button = f'[data-test-id="day-button"][data-test-id-day-button-number="{weekday}"]'

    # List guests
    email_list = [
        "djeddi.noya@hva.nl",
        "stijn.mollink@gmail.com",
        "s.tuininga@hotmail.nl"
    ]

    while True:
        # If booking opens
        if datetime.now().strftime("%H:%M:%S") == target_time:
            # Refresh
            driver.refresh()

            # Zoom out to see all bookings
            driver.execute_script("document.body.style.zoom='80%'")

            # Time log to check speed
            print(f"Start booking: {datetime.now()}")

            # Wait for correct date to appear and click it
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="day-button"][data-test-id-day-button-number="0"]')))
            driver.find_element(By.CSS_SELECTOR, target_day_button).click()

            # List all reserve buttons and save last one
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="bookable-slot-book-button"]')))
            buttons = driver.find_elements(By.CSS_SELECTOR, '[data-test-id="bookable-slot-book-button"]')
            last_button = buttons[-1]
            # # Scroll to last one and click it
            # # driver.execute_script("arguments[0].scrollIntoView();", last_button)
            # WebDriverWait(driver, 3).until(EC.element_to_be_clickable(last_button))
            last_button.click()

            # Scroll pop-up window to the bottom
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="details-book-button"]')))
            modal = driver.find_element(By.CLASS_NAME, "modal-content")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)

            # Locate the add guests button and click it thrice
            invite_button = driver.find_element(By.CSS_SELECTOR, '[data-test-id="increase-member-invite-amount-button"]')
            for _ in range(3):
                invite_button.click()

            # List the email fields and populate them
            emails = driver.find_elements(By.CSS_SELECTOR, '[data-test-id="input-email-member-invites"]')
            for field, address in zip(emails, email_list):
                field.send_keys(address)

            # Locate and click the book button
            book_button = driver.find_element(By.CSS_SELECTOR, '[data-test-id="details-book-button"]')
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable(book_button))
            book_button.click()

            # Time log to check speed
            print(f"End booking: {datetime.now()}")

            # Nice print for booking
            day = datetime.today() + timedelta(days=7)
            day_str = day.strftime('%d-%m-%Y')
            print(f"Booked {weekday_convert[weekday]} {day_str} at {target_time}")

            # Wait for booking to be finished
            time.sleep(10)

            # Close the browser, stop current run
            driver.quit()
            break

        # Refresh often to check if booking opens
        time.sleep(0.01)


if __name__ == "__main__":
    # List your bookings and start 1 minute early
    # schedule.every().sunday.at("11:59:00").do(lambda: fill_form("12:00:00"))
    schedule.every().tuesday.at("19:59:00").do(lambda: fill_form("20:00:00"))
    schedule.every().friday.at("19:59:00").do(lambda: fill_form("20:00:00"))

    
    # Possible test line
    # schedule.every().wednesday.at("19:59:00").do(fill_form("17:00:00"))-
    
    # Refresh to check if booking should be prepared
    while True:
        schedule.run_pending()
        time.sleep(0.01)
