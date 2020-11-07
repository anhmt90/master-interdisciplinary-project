from time import sleep
from account import Account
import selenium_scraper as ss
from utils import *
from selenium.webdriver.common.keys import Keys


def fill_textbox(driver, my_input, textbox_css_selector):
    for char in my_input:
        driver.find_element_by_css_selector(textbox_css_selector).send_keys(char)
        sleep(get_rand_time(0.1, 0.3, integer=False))


def clear_accounts_file():
    with open(PATH.ACCOUNT_FILE_LOC, 'w+') as acc_file:
        old_accounts = acc_file.readlines()
        if old_accounts:
            with open(f'{PATH.SETTINGS_DIR}__blocked__.txt', 'a+') as blocked_file:
                blocked_file.writelines(old_accounts)
        acc_file.write('')


class L---e---AccountCreator:
    def __init__(self, filepath=None):
        """
        filepath: can be path to persist fake emails that are going to be created or path to an existing email account file
        """
        self.filepath = filepath
        self.driver = ss.build_driver(use_proxy=False, use_vpn_ext=False, use_profile=True)

    def __del__(self):
        if self.driver:
            self.driver.quit()

    def create_with_offline_email(self, num_acc, domain='protonmail.com'):
        clear_accounts_file()

        i = 0
        while i < num_acc:
            acc = Account.make_new(domain)
            if not acc.l---e---:
                if ss.is_logged_in(self.driver):
                    self.sign_out()

                self.sign_up(acc)
                self.driver.get("https://www.l---e---.com/notifications/")
                self.driver.get("https://www.l---e---.com/feed/")

                # login again to solve the login captcha
                if not ss.is_logged_in(self.driver):
                    ss.login_authwall(self.driver)
                else:
                    self.sign_out()
                    ss.login_authwall(self.driver)

                self.mute_messenger()
                self.sign_out()
                self.persist_account(acc)
                self.driver.quit()
                self.driver = ss.build_driver(use_proxy=False, use_vpn_ext=False, use_profile=True)
            i += 1
        # account.persist(accounts, self.filepath, mode='w')

    @staticmethod
    def persist_account(acc):
        with open(PATH.ACCOUNT_FILE_LOC, 'a+') as acc_file:
            acc_file.write(f'{acc.get_email()},{acc.password}')

    def sign_out(self):
        ss.click(self.driver, ss.find_elements_by_js(self.driver, "button[data-control-name='nav.settings']")[0])
        ss.click(self.driver, ss.find_elements_by_js(self.driver, "a[data-control-name='nav.settings_signout']")[0])

    def mute_messenger(self):
        ss.click(self.driver, ss.find_elements_by_js(self.driver, "li-icon[aria-label='Open messenger dropdown menu']")[0])
        ss.click(self.driver, ss.find_elements_by_js(self.driver, "div[data-control-name='overlay.connection_list_settings_from_dropdown']")[0])
        ss.click(self.driver, ss.find_elements_by_js(self.driver, "button[data-control-name='overlay.instant_messaging_setting_off']")[0])
        ss.click(self.driver, ss.find_elements_by_js(self.driver, "button[data-test-modal-close-btn]")[0])

    def sign_up(self, acc):
        self.driver.get("https://www.l---e---.com/")
        self.driver.find_element_by_css_selector("a.nav__button-tertiary").click()
        sleep(2)
        fill_textbox(self.driver, acc.get_email(), "input#email-address")
        self.driver.find_element_by_css_selector("input#email-address").send_keys(Keys.TAB)
        fill_textbox(self.driver, acc.password, "input#password")
        self.driver.find_element_by_css_selector("input#password").send_keys(Keys.ENTER)
        # self.driver.find_element_by_css_selector("button#join-form-submit").click()
        fill_textbox(self.driver, acc.first_name, "input#first-name")
        self.driver.find_element_by_css_selector("input#first-name").send_keys(Keys.TAB)
        fill_textbox(self.driver, acc.last_name, "input#last-name")
        self.driver.find_element_by_css_selector("input#last-name").send_keys(Keys.ENTER)
        # self.driver.find_element_by_css_selector("button#join-form-submit").click()
        input("Please solve the CAPTCHA challenge if any. When done, press Enter to continue...")


def rotate_proxy(self):
    self.driver.quit()
    self.driver = ss.build_driver(use_proxy=True)
    return self.driver


def create_with_online_email(self):
    pass


if __name__ == '__main__':
    lac = L---e---AccountCreator()
    lac.create_with_offline_email(2)
    # clear_accounts_file()


###################################### HANDLE PHONE VERIFICATION REQUIRED
# phone_verification_required = False
# while True:
#     sleep(1)
#     verification_iframes = ss.find_elements_by_js(driver, "iframe.challenge-dialog__iframe")
#     if not verification_iframes:
#         break
#
#     driver.switch_to.frame(verification_iframes[0])
#     phone_verification_required = len(ss.find_elements_by_js(driver, "#register-verification-phone-number")) != 0
#     if phone_verification_required:
#         account.persist(accounts, self.filepath, mode='w')
#         driver = self.rotate_proxy()
#         break
#
# driver.switch_to.default_content()
# if phone_verification_required:
#     continue
#
# while ss.find_elements_by_js(driver, "input#last-name"):
#     sleep(5)
# driver.get("https://www.l---e---.com/feed/")
# sleep(3)
# if driver.current_url in "https://www.l---e---.com/feed/":
#     acc.l---e--- = True
#     changed = True
