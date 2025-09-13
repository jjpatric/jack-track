# main.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, date, timedelta
import time
import os
import pytz
from twilio.rest import Client

# --- Configuration ---
URL = "https://www.seekyoursounds.com/radio/jack969calgary"
LOG_FILE = "song_log.txt"
TIMEZONE = pytz.timezone('America/Edmonton') # Timezone for Calgary
CHECK_INTERVAL_SECONDS = 30

# --- Twilio Configuration ---
# IMPORTANT: It's recommended to use environment variables for security.
# For example: os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
# This is your Twilio phone number that sends the message
TWILIO_PHONE_NUMBER = '' # <-- IMPORTANT: REPLACE WITH YOUR TWILIO 'FROM' NUMBER
PHONE_NUMBERS_TO_TEXT = [] # <-- IMPORTANT: REPLACE WITH YOUR PHONE NUMBER(S)


def setup_driver():
    """Initializes and returns a Selenium WebDriver instance."""
    print("Setting up Selenium WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("WebDriver setup complete.")
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        print("Please ensure you have Google Chrome installed.")
        return None

def scrape_current_song(driver):
    """Scrapes the current song from the website."""
    try:
        driver.get(URL)
        time.sleep(5) # Wait for dynamic content to load
        text_section = driver.find_element(By.CLASS_NAME, "text-section")
        
        # Get all text within the div and replace newlines with ' - '
        full_text = text_section.text.strip()
        if not full_text:
            return None
            
        formatted_text = full_text.replace('\n', ' - ')
        return formatted_text
        
    except NoSuchElementException:
        print("Could not find song information on the page. The page structure might have changed.")
        return None
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None

def send_text_message(phone_number, message_body):
    """Sends a text message using the Twilio API."""
    print("="*40)
    print(f"Attempting to send SMS to: {phone_number}")
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=f"+1{phone_number}" # Assuming North American number format
        )
        print(f"SMS sent successfully! SID: {message.sid}")
    except Exception as e:
        print(f"!!! FAILED TO SEND SMS via Twilio: {e} !!!")
        print("Please check your Twilio credentials and 'From' number.")
    print("="*40)


def main_loop():
    """Main execution loop for the scraper."""
    driver = setup_driver()
    if not driver:
        return

    last_song_logged = ""
    # Initialize the date tracking for log rotation
    current_log_date = datetime.now(TIMEZONE).date()

    try:
        while True:
            now_local = datetime.now(TIMEZONE)
            
            # --- Daily Log Rotation Logic ---
            if now_local.date() > current_log_date:
                print("\n--- End of Day Detected: Rotating Log File ---")
                yesterday_str = current_log_date.strftime('%Y-%m-%d')
                archive_log_file_name = f"{LOG_FILE.split('.')[0]}_{yesterday_str}.txt"
                
                if os.path.exists(LOG_FILE):
                    os.rename(LOG_FILE, archive_log_file_name)
                    print(f"Renamed '{LOG_FILE}' to '{archive_log_file_name}'")
                
                # Reset for the new day
                last_song_logged = ""
                current_log_date = now_local.date()
                print(f"Starting fresh log for {current_log_date.strftime('%Y-%m-%d')}.\n")

            # Check 1: Is it a weekday (0=Monday, 6=Sunday)?
            is_weekday = 0 <= now_local.weekday() <= 4
            # Check 2: Is it between 8 AM and 6 PM (18:00)?
            is_active_hours = 8 <= now_local.hour < 18

            if is_weekday and is_active_hours:
                print(f"\n[{now_local.strftime('%Y-%m-%d %H:%M:%S')}] Active hours. Checking for song...")
                
                current_song = scrape_current_song(driver)

                if not current_song:
                    time.sleep(CHECK_INTERVAL_SECONDS)
                    continue

                print(f"Found song: {current_song}")

                if current_song == last_song_logged:
                    print("Song is the same as the last one logged. Skipping.")
                else:
                    song_history = []
                    if os.path.exists(LOG_FILE):
                        with open(LOG_FILE, "r", encoding="utf-8") as f:
                            song_history = f.readlines()
                    
                    repeated_timestamps = []
                    for line in song_history:
                        try:
                            timestamp_str = line.split('] ')[0][1:]
                            song_name_in_log = line.split('] ')[1].strip()
                            if song_name_in_log == current_song:
                                repeated_timestamps.append(timestamp_str)
                        except IndexError:
                            continue # Skip malformed lines
                    
                    if repeated_timestamps:
                        current_timestamp_str = now_local.strftime('%Y-%m-%d %H:%M:%S')
                        all_timestamps = repeated_timestamps + [current_timestamp_str]
                        
                        message = (f"Repeat Alert!\nSong: {current_song}\n"
                                   f"Played at: {', '.join(all_timestamps)}\n"
                                   "Text the word REPEAT and your name to 969123")
                        for PHONE_NUMBER_TO_TEXT in PHONE_NUMBERS_TO_TEXT:
                            send_text_message(PHONE_NUMBER_TO_TEXT, message)
                            time.sleep(1) # To avoid hitting rate limits

                    log_entry = f"[{now_local.strftime('%Y-%m-%d %H:%M:%S')}] {current_song}\n"
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(log_entry)
                    print(f"Logged new song: {current_song}")
                    last_song_logged = current_song

            else:
                now = datetime.now(TIMEZONE)
                # Determine the target time: 8:00 AM today
                target_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
                # If it's already past 8:00 AM, set the target for 8:00 AM tomorrow
                if now >= target_time:
                    target_time += timedelta(days=1)
                # Calculate the difference in seconds and print the result
                seconds_left = (target_time - now).total_seconds()
                print(f"[{now_local.strftime('%Y-%m-%d %H:%M:%S')}] Outside of active hours. Sleeping for {seconds_left}s")
                time.sleep(seconds_left)
                continue

            print(f"Waiting for {CHECK_INTERVAL_SECONDS} seconds...")
            time.sleep(CHECK_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nScript interrupted by user.")
    finally:
        if driver:
            print("Closing the browser.")
            driver.quit()

if __name__ == "__main__":
    # To run this, you will need to install the required libraries:
    # pip install selenium webdriver-manager pytz twilio
    for PHONE_NUMBER_TO_TEXT in PHONE_NUMBERS_TO_TEXT:
        send_text_message(PHONE_NUMBER_TO_TEXT1, "Starting Jack-Track!")
        time.sleep(1) # To avoid hitting rate limits
    main_loop()

