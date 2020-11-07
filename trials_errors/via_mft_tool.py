from utils import *
import selenium_scraper as ss
from selenium.webdriver.common.keys import Keys
from time import sleep
import pyperclip

if __name__ == '__main__':
    ss.read_profile_urls()
    ss._format_profile_urls()

    driver = ss.build_driver()
    try:
        while len(ss.profile_urls) >= 1:
            driver.get("https://search.google.com/test/mobile-friendly")
            input_url = driver.find_element_by_css_selector("input[aria-label='Enter a URL to test']")
            input_url.send_keys(ss.profile_urls[0])
            input_url.send_keys(Keys.ENTER)

            while "?id=" not in driver.current_url:
                sleep(5)

            html_tab = ss.find_elements_by_js(driver, "span[data-event-label='success-page']")[1]
            ss.click(driver, html_tab)

            copy_button = ss.find_elements_by_js(driver, "div[aria-label='Copy editor content']")
            ss.click(driver, copy_button)
            html = pyperclip.paste()
            profile_name = parse_profile_name(ss.profile_urls[0])
            with open(f"{PATH.PROFILE_DIR}{parse_profile_name(ss.profile_urls[0])}.html", 'a+') as file:
                file.write(html)
                ss.checkpoint = update_checkpoint(ss.checkpoint, profile_name)
                persist_checkpoint(ss.checkpoint)

            sleep(10)
            del ss.profile_urls[0]
    finally:
        driver.quit()


