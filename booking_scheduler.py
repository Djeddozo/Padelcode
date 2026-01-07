import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from booking_config import load_schedule

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_credentials() -> tuple[str, str]:
    email = os.environ.get("USC_EMAIL")
    password = os.environ.get("USC_PASSWORD")
    missing = [name for name, value in (("USC_EMAIL", email), ("USC_PASSWORD", password)) if not value]
    if missing:
        missing_vars = ", ".join(missing)
        raise ValueError(
            f"Missing credentials: {missing_vars}. Please set USC_EMAIL and USC_PASSWORD in the environment."
        )
    return email, password


def fill_form(
    target_time: str,
    stop_event: threading.Event,
    target_day: str,
    on_complete: Optional[Callable[[str, str], None]] = None,
) -> None:
    email, password = get_credentials()

    # Setup the WebDriver
    options = webdriver.ChromeOptions()
    options.headless = False
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.maximize_window()

    def check_stop() -> bool:
        if stop_event.is_set():
            driver.quit()
            return True
        return False

    # Timestamp
    print(f"Start login: {datetime.now()}")

    # Open the webpage
    driver.get("https://my.uscsport.nl/pages/login")

    if check_stop():
        return
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "showEmailLoginButton"))
    )

    login_button = driver.find_element(By.ID, "showEmailLoginButton")
    login_button.click()

    if check_stop():
        return
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
    if check_stop():
        return
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "tag-filterinput"))
    )

    # Locate the search button and then select padel, so that it does not have to do this at execution time
    search_button = driver.find_element(By.ID, "tag-filterinput")
    search_button.click()
    search_button.send_keys("Padel")

    # Wait for the padel category to load
    if check_stop():
        return
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "tagCheckbox193"))
    )

    # Select padel
    padel_button = driver.find_element(By.ID, "tagCheckbox193")
    padel_button.click()

    # Create variables before booking for speed
    target_day_index = DAY_NAMES.index(target_day)
    target_day_button = f'[data-test-id="day-button"][data-test-id-day-button-number="{target_day_index}"]'

    # List guests
    email_list = [
        "djeddi.noya@hva.nl",
        "stijn.mollink@gmail.com",
        "s.tuininga@hotmail.nl",
    ]

    while True:
        if check_stop():
            return
        # If booking opens
        if datetime.now().strftime("%H:%M:%S") == target_time:
            # Refresh
            driver.refresh()

            # Zoom out to see all bookings
            driver.execute_script("document.body.style.zoom='80%'")

            # Time log to check speed
            print(f"Start booking: {datetime.now()}")

            # Wait for correct date to appear and click it
            if check_stop():
                return
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, '[data-test-id="day-button"][data-test-id-day-button-number="0"]')
                )
            )
            driver.find_element(By.CSS_SELECTOR, target_day_button).click()

            # List all reserve buttons and save last one
            if check_stop():
                return
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="bookable-slot-book-button"]'))
            )
            buttons = driver.find_elements(By.CSS_SELECTOR, '[data-test-id="bookable-slot-book-button"]')
            last_button = buttons[-1]
            last_button.click()

            # Scroll pop-up window to the bottom
            if check_stop():
                return
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-test-id="details-book-button"]'))
            )
            modal = driver.find_element(By.CLASS_NAME, "modal-content")
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal)

            # Locate the add guests button and click it thrice
            invite_button = driver.find_element(
                By.CSS_SELECTOR, '[data-test-id="increase-member-invite-amount-button"]'
            )
            for _ in range(3):
                invite_button.click()

            # List the email fields and populate them
            emails = driver.find_elements(By.CSS_SELECTOR, '[data-test-id="input-email-member-invites"]')
            for field, address in zip(emails, email_list):
                field.send_keys(address)

            # Locate and click the book button
            book_button = driver.find_element(By.CSS_SELECTOR, '[data-test-id="details-book-button"]')
            if check_stop():
                return
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable(book_button))
            book_button.click()

            # Time log to check speed
            print(f"End booking: {datetime.now()}")

            # Nice print for booking
            today = datetime.today()
            day_offset = (target_day_index - today.weekday()) % 7 or 7
            day = today + timedelta(days=day_offset)
            day_str = day.strftime("%d-%m-%Y")
            print(f"Booked {target_day} {day_str} at {target_time}")

            # Wait for booking to be finished
            if check_stop():
                return
            time.sleep(10)

            # Close the browser, stop current run
            driver.quit()
            if on_complete:
                on_complete(target_day, target_time)
            break

        # Refresh often to check if booking opens
        if check_stop():
            return
        time.sleep(0.01)


class BookingScheduler:
    def __init__(self, on_complete: Optional[Callable[[str, str], None]] = None) -> None:
        self._stop_event = threading.Event()
        self._thread = None
        self._running = False
        self._on_complete = on_complete

    def start(self, email: str, password: str) -> None:
        if self._running:
            return
        if not email or not password:
            raise ValueError("Missing credentials. Provide USC_EMAIL and USC_PASSWORD or enter them in the dialog.")
        self._stop_event.clear()
        schedule.clear()
        for slot in load_schedule():
            day = slot.get("day")
            book_time = slot.get("book_time")
            if day not in DAY_NAMES or not book_time:
                continue
            try:
                book_dt = datetime.strptime(book_time, "%H:%M:%S")
            except ValueError:
                continue
            check_time = (book_dt - timedelta(minutes=1)).strftime("%H:%M:%S")
            run_day = DAY_NAMES[(DAY_NAMES.index(day) - 6) % 7].lower()
            schedule_day = getattr(schedule.every(), run_day)
            schedule_day.at(check_time).do(
                lambda target=book_time, target_day=day: fill_form(
                    target, self._stop_event, target_day, self._on_complete
                )
            )
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._running = True
        self._thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
        schedule.clear()
        self._running = False

    def is_running(self) -> bool:
        return self._running

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            schedule.run_pending()
            time.sleep(0.01)
