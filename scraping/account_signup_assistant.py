import enum
import random
from time import sleep
import logging

import l---e---_navigator as ln
import account
from account import Account
from config import ACCOUNT_SIGNUP_ASSISTANT_PARAMS as PARAM

# The default domains for the email used as username for the L---e--- account being signed up
DEFAULT_DOMAINS = ['protonmail.com', 'web.de', 'gmx.de', 'juno.com']


class _SIGNUP_EXIT_CODE(enum.Enum):
    """
    The Enum indicating the result of the signup process whether it was successful or a phone verification has shown up   
    """
    SUCCESS = 0
    PHONE_VERIFICATION = 1


def _try_to_get_kicked_out():
    """
    Performs a sequence of operations on the feed page after a successful sign-up to get kicked out by L---e---.
    This will help get an easier CAPTCHA for the first login. By doing an intentional logout instead, the CAPTCHA
    for the first login will be much hard to solve.
    The operations to repreatedly perform are using the search bar and scroll down the feed page to click on 
    `New Posts` buttons.
    """
    _search_random()
    _scroll_to_click_new_posts()


def _prep_scraping():
    """
        Performs a sequence of operations to prepare for the scraping later on after successfully sign up a L---e--- account.
        This includes turning of L---e---'s messenger, trying to get kicked out by L---e--- to get an easy CAPTCHA for the first
        login.
    """
    if ln.is_logged_in():
        _turn_off_message_overlay()

    while ln.check_logged_in(nav_feed=True):
        _try_to_get_kicked_out()

    if '/uas/login' in ln.cur_url():
        ln.login_uas()


def _fill_sign_up_form():
    """
        Types in textboxes of email, password, first name and last name 
    """
    ln.go('https://www.l---e---.com/signup/cold-join?trk=guest_homepage-basic_nav-header-join')
    ln.fill_username_pwd_form(css_username="input[type='email']", css_password="input[type='password']")
    sleep(2)
    ln.fill_input(text=ln.get_acc().get_first_name(), css="input#first-name")
    ln.fill_input(text=ln.get_acc().get_last_name(), css="input#last-name", hit_enter=True)
    sleep(2)


def _has_phone_verification_challenge():
    """
        Checks whether a phone verification shows up during the sign-up
    """
    return ln.find_elements_by_css("input#register-verification-phone-number") == list()


def _scroll_to_click_new_posts():
    """
        Scrolls to the `New Posts` button on the feed page and clicks on that
    """
    while True:
        if not ln.check_logged_in(nav_feed=True):
            break
        ln.scroll_down()
        elements = ln.find_elements_by_css("div.text-align-center button")
        if elements != list():
            ln.scroll_to_click(elements[0])
            break


def _turn_off_message_overlay():
    """
        Turns off the message notofication from the messenger when being on the feed page for the first time 
    """
    ln.click("button[data-control-name='overlay.dropdown_menu']")
    ln.click("div[data-control-name='overlay.connection_list_settings_from_dropdown']")
    ln.click("div[data-control-name='overlay.instant_messaging_setting_off']")
    ln.click("button[data-test-modal-close-btn]")
    ln.click("header[data-control-name='overlay.minimize_connection_list_bar']")


def _solve_audio_captcha():
    """
        Switches from image CAPTCHA to audio one and wait for it to be solved
    """
    if ln.find_elements_by_css('section.challenge-dialog') != list():
        if ln.find_elements_by_css("canvas#FunCAPTCHA") != list():
            ln.click("span.fc_meta_audio_btn")
            sleep(1)
            ln.click("button#audio_play")
            ln.wait_for_challenge_to_be_solved()


def _search_random():
    """
        Performs random search with L---e---'s search bar
    """
    ln.fill_input(text='covid 19', css='input.search-global-typeahead__input', hit_enter=True)
    ln.scroll_down()


class AccountSignUpAssistant:
    """
        Class that helps speed up the sign-up process for account L---e--- accounts
    """

    def __init__(self, count=4, email_domains=None, use_chrome_profile=False):
        self.count = count
        self.domains = email_domains if email_domains else DEFAULT_DOMAINS
        self.use_chrome_profile = use_chrome_profile
        self.accounts = list()

    def exec(self):
        rand = random.randint(0, len(self.domains))
        for i in range(self.count):
            acc = Account.make_new(self.domains[(i + rand) % len(self.domains)])
            exit_code = self._sign_up(acc)
            if exit_code == _SIGNUP_EXIT_CODE.PHONE_VERIFICATION:
                self.accounts.append(acc)
                logging.warning("STOP: Phone versification encountered. Sign-up process aborted!")
                # break
            ln.terminate()

        if self.accounts:
            account.create_file(self.accounts, PARAM.ACC_SAVE_DIR)

    def _sign_up(self, acc):
        """
        Signs up a L---e--- account
        Args:
            acc (account.Account): The account object containing data used for the sign up 

        Returns:
            (_SIGNUP_EXIT_CODE): Code indicating the resulting status of the sign-up process
        """
        ln.build_driver(use_profile=self.use_chrome_profile)
        ln.set_acc(acc)

        _fill_sign_up_form()
        if _has_phone_verification_challenge():
            sleep(1)
            return _SIGNUP_EXIT_CODE.PHONE_VERIFICATION

        _solve_audio_captcha()
        if 'onboarding/start/' in ln.cur_url():
            ln.go_feed()

        if ln.check_logged_in(nav_feed=True):
            if not acc.get_logged_in():
                acc.set_logged_in(True)

        self.accounts.append(acc)
        _prep_scraping()
        if ln.check_logged_in(nav_feed=True):
            ln.terminate()

        return _SIGNUP_EXIT_CODE.SUCCESS


def run():
    print("\n************************************** PARAMERTERS **************************************\n")
    print(f'ACC_COUNT: {PARAM.ACC_COUNT}\n')
    print(f'ACC_SAVE_DIR: {PARAM.ACC_SAVE_DIR}\n')
    print(f'USE_CHROME_PROFILE: {PARAM.USE_CHROME_PROFILE}\n')
    print('*****************************************************************************************\n')

    asua = AccountSignUpAssistant(count=PARAM.ACC_COUNT, use_chrome_profile=PARAM.USE_CHROME_PROFILE)
    asua.exec()


if __name__ == '__main__':
    run()
