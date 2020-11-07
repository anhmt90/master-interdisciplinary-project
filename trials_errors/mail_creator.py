from time import sleep

from selenium.webdriver.common.keys import Keys

import selenium_scraper as ss
from account import Account, PREFIX, ACC_FILE
from utils import *


def parse_domain_from_filename(filepath):
    filename = filepath if filepath.count(os.sep) == 0 else parse_filename(filepath)
    domain = filename.split('_')[1]
    return domain


def clear_input(webelement):
    webelement.send_keys(Keys.CONTROL + "a")
    webelement.send_keys(Keys.DELETE)


class MailCreator:
    def __init__(self, num_accounts, file_path):
        """
        write_mode: see write modes of builtin function open()
        """
        self.num_accounts = num_accounts
        self.file_path = str(file_path)
        self.driver = ss.build_driver() if PREFIX.OFFLINE not in file_path else None

    def __del__(self):
        if self.driver is not None:
            self.driver.quit()

    def create_yandex_mails(self):
        driver = self.driver
        domain = parse_domain_from_filename(self.file_path)
        for i in range(self.num_accounts):
            acc = Account.make_new(domain)

            driver.get("https://passport.yandex.com/registration/mail")
            sleep(1)
            driver.find_element_by_id("firstname").send_keys(acc.first_name)
            driver.find_element_by_id("lastname").send_keys(acc.last_name)

            while True:
                driver.find_element_by_id("login").send_keys(acc.username)
                sleep(1)
                if not ss.find_elements_by_js(driver, "strong.error-message"):
                    break
                clear_input(driver.find_element_by_id("login"))
                acc.pick_another_username()

            driver.find_element_by_id("password").send_keys(acc.password)
            driver.find_element_by_id("password_confirm").send_keys(acc.password)
            ss.click(driver, driver.find_element_by_css_selector(".toggle-link.link_has-no-phone"))
            sleep(1)
            driver.find_element_by_xpath("//option[contains(.,'computer game')]").click()
            driver.find_element_by_id("hint_answer").send_keys('left4dead2')

            # Wait for CAPTCHA to be solved by the user
            while "passport.yandex.com/profile" not in driver.current_url:
                sleep(5)

            acc.persist(self.file_path)

    def create_proton_mails(self):
        driver = self.driver
        domain = parse_domain_from_filename(self.file_path)
        for i in range(self.num_accounts):
            acc = Account.make_new(domain)
            driver.get("https://mail.protonmail.com/create/new?language=en")
            sleep(3)
            driver.find_element_by_css_selector("input#password").send_keys(acc.password)
            driver.find_element_by_css_selector("input#passwordc").send_keys(acc.password)
            while True:
                driver.switch_to.frame(driver.find_element_by_css_selector("iframe.top"))
                driver.find_element_by_css_selector("input#username").send_keys(acc.username)
                driver.switch_to.default_content()

                driver.switch_to.frame(driver.find_element_by_css_selector("iframe.bottom"))
                driver.find_element_by_css_selector(".btn").click()
                # driver.find_element_by_name("submitBtn").click()
                driver.switch_to.default_content()
                sleep(2)

                driver.switch_to.frame(driver.find_element_by_css_selector("iframe.top"))
                if not ss.find_elements_by_js(driver, "div.error"):
                    break
                driver.switch_to.default_content()
                acc.pick_another_username()

            while "inbox?welcome=true" not in driver.current_url:
                sleep(5)
            acc.persist(self.file_path)

            ss.find_elements_by_js(driver, "button#confirmModalBtn").click()
            sleep(3)
            # driver.find_element_by_css_selector("li.navigationUser>a").click()
            driver.find_element_by_css_selector("a[ui-sref='login']").click()

    def create_offline_mails(self):
        assert parse_filename(self.file_path).lower().startswith(
            PREFIX.OFFLINE), "File containing offline accounts must have its name start with 'offline_'"
        domain = parse_domain_from_filename(self.file_path)
        for i in range(self.num_accounts):
            acc = Account.make_new(domain)
            acc.persist(self.file_path)

    def run(self):
        if PREFIX.OFFLINE in parse_filename(self.file_path).lower():
            self.create_offline_mails()
        else:
            if 'yandex.com' in self.file_path:
                self.create_yandex_mails()
            elif 'protonmail.com' in self.file_path:
                self.create_proton_mails()


if __name__ == '__main__':
    mc = MailCreator(120, ACC_FILE.OFFLINE_PROTONMAIL_COM_1)
    mc.run()
