"""
This module is a wrapper for Selenium driver and provides functions to operate on L---e--- web pages during scraping
"""

import re
import sys
import logging
from time import sleep
import enum

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdrivermanager import ChromeDriverManager
# from webdriver_manager.chrome import ChromeDriverManager

from http_request_randomizer.requests.errors.ProxyListException import ProxyListException
from http_request_randomizer.requests.proxy.ProxyObject import Protocol
from tkinter import messagebox
from selenium.webdriver.common.keys import Keys

from config import SCRAPING_SUBDIRS as PATH
from config import SCRAPER_PARAMS as PARAM
from scraping.utils import *

logging.basicConfig(level=logging.INFO)


class JUMP_MODE(enum.Enum):
    INTERNAL = 'simple_i'
    EXTERNAL = 'simple_e'
    INTERNAL_EXTERNAL = 'long'


class JUMP_OPTION(enum.Enum):
    INTERNAL = 'internal'
    EXTERNAL = 'external'
    FEED = 'feed'


# The Selenium driver
_DRIVER = None

# List of external (not inside l---e---.com) URNs to navigate to after each profile scraped. For disguising purpose to act like a normal user browsing
_RANDOM_EXTERNAL_URNS = ["google.com", "facbook.com", "tum.de", "glosbe.com", "dict.cc", "vocabulary.com",
                         "amazon.com", "python.org"]

# List of internal (inside l---e---.com) URNs to navigate to after each profile scraped. For disguising purpose to act like a normal user browsing
_RANDOM_INTERNAL_URNS = ["mynetwork/", "notifications/", "jobs/", "psettings/",
                         "psettings/messages",
                         "psettings/account", "jobs/tracker/applied/", "jobs/tracker/saved/"]

# Link to the feed page of the scraping account
_FEED_URL = "https://www.l---e---.com/feed/"

# The current scraping account
_ACC = None


def _add_proxy_arg(options):
    """
    Adds a proxy from a proxy list into Chome driver options
    Args:
        options(Options): options for Chrome driver

    Returns:
        (tuple(Options))
    """
    import trials_errors.proxy_handler as ph
    continued = True
    retry = True
    try:
        while retry:
            try:
                proxy = ph.pick_proxy_hrr(Protocol.HTTP)
                options.add_argument(f'proxy-server={proxy.get_address()}')
                logging.info("Using proxy: " + options.arguments[1])
                retry = False

            except ProxyListException as ple:
                logging.debug(f"FAILED: Empty Proxy List - {ple}")
                retry = messagebox.askretrycancel(title="No Proxy Found", message="No proxy found. Retry?")
                if not retry:
                    continued = messagebox.askyesno(title="Proceed?", message="Proceed without proxy?"
                                                                              "\n- Click Yes to continue scraping without proxy"
                                                                              "\n- Click No to terminate the program")
    finally:
        return options, continued


def build_driver(use_proxy=False, use_vpn_ext=False, use_profile=False, use_fake_agent=False, headless=False,
                 download=False):
    """
    Creates Selenium Chrome driver and configures it with multiple options.
    These options are part of the trial and error process to bypass CAPTCHA and other restrictions from L---e--- against
    profile scraping. At the end of the day, these options are not so effective to get around anti-scraping mechanisms from L---e---.
    Args:
        use_proxy (bool): True if the driver should use proxy, False otherwise
        use_vpn_ext (bool): True if the driver should use VPN extension stored in tools/, False otherwise
        use_profile (bool): True if the driver should run with a real Chrome profile, False otherwise
        use_fake_agent (bool): True if the driver should run with a disguising user agent, False otherwise
        headless (bool): True if the driver should run in headless mode (not recommended), False otherwise
        download (bool): True if the function should auto-download the most up-to-date Chrome webdriver from the Internet.
                            Note that the real Chrome browser on the machine should be updated to same version of the driver
                            for it to run.

    Returns:
        (selenium.webdriver.Chrome): The Selenium Chrome webdriver configured with the respective options
    """

    global _DRIVER

    options = Options()

    if use_fake_agent:
        ua = UserAgent().chrome
        ua = re.sub("Chrome/[0-9]{2}", f"Chrome/{random.randint(70, 80)}", ua)
        # if int(user_agent_parser.Parse(ua)['user_agent']['major']) >= 50:
        options.add_argument(f'user-agent={ua}')
        logging.info("User-Agent changed to " + options.arguments[0])

    continued = True
    if use_proxy:
        options, continued = _add_proxy_arg(options)

    if not continued:
        sys.exit()

    if use_profile:
        # options.add_argument("--user-data-dir=C:\\Users\\anhmt\\AppData\\Local\\Google\\Chrome\\User Data")
        # options.add_argument('--profile-directory=C:\\Users\\anhmt\\AppData\\Local\\Google\\Chrome\\User Data\\Profile')
        options.add_argument(
            f"--user-data-dir=C:{sep}Users{sep}anhmt{sep}AppData{sep}Local{sep}Google{sep}Chrome{sep}User Data")

    options.add_argument("--incognito")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--ignore-certificate-errors")

    # options.add_argument(
    #     '--load-extension=/home/anhmt/.config/google-chrome/Default/Extensions/enaobbodnmbpecahhojidoiblhmnohef/2.2.2_0')
    if use_vpn_ext:
        options.add_extension(f"{PATH.TOOLS}Free VPN - the fastest VPN in the house.crx")
    # options.add_argument("--disable-extensions")
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    # _DRIVER = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    driver_file = ChromeDriverManager().download_and_install()[1] if download else PARAM.CHROME_DRIVER_FILE
    _DRIVER = webdriver.Chrome(driver_file, options=options)
    # _DRIVER = webdriver.Chrome("C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe", options=options)

    _DRIVER.implicitly_wait(5)
    _DRIVER.maximize_window()

    if use_vpn_ext:
        _DRIVER.get("chrome://extensions/?id=enaobbodnmbpecahhojidoiblhmnohef")
        _DRIVER.execute_script(
            "return document.querySelector('extensions-manager').shadowRoot.querySelector('#viewManager > extensions-detail-view.active').shadowRoot.querySelector('div#container.page-container > div.page-content > div#options-section extensions-toggle-row#allow-incognito').shadowRoot.querySelector('label#label input').click()")
        input("Please configure the proxy. When done, press Enter to continue...")

    return _DRIVER


def set_acc(acc):
    global _ACC
    if acc is not None and acc.get_blocked():
        raise_AccountBlockedException()
    _ACC = acc


def remove_acc():
    set_acc(None)


def get_acc():
    return _ACC


def is_logged_in():
    return _ACC.get_logged_in()


def set_logged_in(state):
    return _ACC.set_logged_in(state)


def cur_url():
    return _DRIVER.current_url


def feed_url():
    return _FEED_URL


def go(url):
    """
    Navigates to an URL
    Args:
        url: the URL to nagivate to
    """
    _DRIVER.get(url)


def go_feed():
    go(_FEED_URL)


def fill_input(text, css, hit_enter=False):
    """
    Fills up a text input on the current web page
    Args:
        text (str): The text for the driver to type in
        css (str): the CSS-selector of the input element on the DOM tree
        hit_enter (bool): True to automatically hit the Enter button after the input has been filled up
    """
    for char in text:
        _DRIVER.find_element_by_css_selector(css).send_keys(char)
        sleep(get_rand_time(0.1, 0.2, integer=False))
    if hit_enter:
        _DRIVER.find_element_by_css_selector(css).send_keys(Keys.ENTER)
        sleep(1)


def fill_username_pwd_form(css_username, css_password):
    """
    Fills up an HTML form with username and passwords fields
    Args:
        css_username: The CSS-selector of the textbox for username
        css_password: The CSS-selector of the textbox for password
    """
    fill_input(get_acc().get_email(), css_username)
    fill_input(get_acc().get_password(), css_password, hit_enter=True)


def login_authwall(dest_url=''):
    """
    [DEPRECATED] This function was part of the trial and error, so it can be removed in the future

    Logs in with :_ACC when standing at L---e---'s authwall (the page with URL l---e---.com/authwall). Normally, access attempts to
    protected L---e--- contents required login will be redirected to the authwall. During every login, users will have to solve
    CAPTCHA challenges, therfore, this function will return a boolean indicating whether the login attempt has been successfully done

    Args:
        dest_url (bool): the destination URL that one is trying to access to. After a successful login, one will be redirected back to this URL

    Returns:
        (bool): True if the login is successful, False otherwise
    """
    if dest_url != '':
        go(parse_redirect_url(dest_url))

    sign_links = _DRIVER.find_elements_by_css_selector('a.form-toggle')
    for link in sign_links:
        if link.text == "Sign in":  # we're at register form
            link.click()

        # driver.find_element_by_name("session_key").send_keys(CURRENT_ACC['username'])
    fill_username_pwd_form(css_username='input#login-email', css_password='input#login-password')
    return handle_challenge_and_inspect_login_state()


def login_uas():
    """
    Logs in with :_ACC when standing at L---e---'s main login page (the page with URL l---e---.com/uas/login).
    The user will possibly need to solve a CAPTCHA as part of the login attempt
    Returns:
        (bool): True if the login is successful, False otherwise
    """
    if not is_same_url(cur_url(), "https://www.l---e---.com/uas/login"):
        _DRIVER.get("https://www.l---e---.com/uas/login")
    fill_username_pwd_form(css_username="input#username", css_password="input#password")
    return handle_challenge_and_inspect_login_state()


def wait_for_challenge_to_be_solved():
    """
    Suspends the program and wait for the CAPTCHA to be solved by the user. The user needs to hit Enter after solving
    the CAPTCHA so that the program can continue to run.
    """
    input("Please solve the challenge. When done, press Enter to continue...")


def handle_challenge_and_inspect_login_state():
    """
    Checks if a CAPTCHA challenge is encountered and suspends the programs to wait for the CAPTCHA to be solved. Afterwards,
    checks whether the CAPTCHA has been successfully solved or not by inspecting the login status.

    Returns:
        (bool): True if the login is successful, False otherwise
    """
    challenged = "checkpoint/" in cur_url() or "challenge/" in cur_url()
    if challenged:
        if find_elements_by_css("div.container-row + a.content__button--primary") != list():
            raise_AccountBlockedException()
        else:
            wait_for_challenge_to_be_solved()

    check_logged_in()
    if challenged and is_logged_in():
        logging.info("SUCCESS: Challenge solved!")
    elif challenged and not is_logged_in():
        logging.warning("FAILED: Failed to pass challenge!")

    if is_logged_in():
        logging.info("SUCCESS: Log-in successfully!")
    return is_logged_in()


def scroll_up(times=10):
    """
    Scrolls up a web page a certain number of times until the top of the page is reached
    Args:
        times: the number of times to scroll up until the top of the page is reached
    """
    height = _DRIVER.execute_script("return document.body.scrollHeight")
    for i in range(times):
        _DRIVER.execute_script(f"window.scrollBy(0,{-(height / times)})")
        sleep(1)
    _DRIVER.execute_script(f"window.scrollTo(0,0)")
    sleep(1 / 2)


def scroll_down():
    """
    Scrolls down a web page a certain number of times until the bottom of the page is reached. Note that, a web page
    can show more content and its height will be extended accordingly as one is scrolling down. This function will
    keep scrolling down until the `actual` bottom of the page is reached
    """
    last_height = _DRIVER.execute_script("return document.body.scrollHeight")
    while True:
        _DRIVER.execute_script(f"window.scrollBy(0,{last_height})")
        sleep(1)
        new_height = _DRIVER.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    _DRIVER.execute_script(f"window.scrollTo(0,{last_height})")
    sleep(1 / 2)


def scroll_to(element):
    """
    Scrolls to a web element on a page, so that the element is in the visible frame of the browser
    Args:
        element: The Selenium web element to scroll to
    """
    _DRIVER.execute_script("arguments[0].scrollIntoView();", element)


def click(element):
    """
    Does a left-click on a web element
    Args:
        element: The Selenium web element to left-click on
    """
    _DRIVER.execute_script("arguments[0].click();", element)
    sleep(1 / 2)


def scroll_to_click(element):
    """
    Wrapper function to execute functions scroll_to() and click() consecutively
    Args:
        element: The target Selenium web element to scroll to and click on
    """
    scroll_to(element)
    click(element)


def find_elements_by_css(css_selector):
    """
    Find all elements matching an CSS-selector
    Args:
        css_selector: The CSS-selector as a criterion to filter the web elements one wants to fetch

    Returns:
        (list[selenium.webdriver.remote.webelement.WebElement]): A list of Selenium web element matching the CSS-selector
    """
    return _DRIVER.execute_script(f"return document.querySelectorAll(\"{css_selector}\")")


def expand_accomplishments_section(buttons):
    """
    Expands/Loads/Uncovers the "accomplishment" section on L---e--- profile page.
    Accomplishments section is handled separately since unlike other sections, it can only expand 1 subsection at
    the same time. We opt to expand subsection Organizations if it's available, otherwise, we expand subsection Projects
    instead (if it's available).
    Args:
        buttons (list[selenium.webdriver.remote.webelement.WebElement]): The button elements to be clicked on to expand the subsections
    """
    aria_labels = [button.get_attribute("aria-label") for button in buttons]

    click_idx = -1
    for i, al in enumerate(aria_labels):
        if "organizations" in al:
            click_idx = i
            break
        elif "projects" in al:
            click_idx = i

    if click_idx != -1:
        scroll_to_click(buttons[click_idx])
        current_section = buttons[click_idx].get_attribute("aria-label").split(" ")[1]
        # accomplishments_container = driver.find_element_by_css_selector(
        #     f"div[id='{current_section}-expandable-content']")
        while True:
            # expand_buttons = accomplishments_container.find_elements_by_css_selector("button[aria-expanded='false']")
            expand_buttons = find_elements_by_css(
                f"div[id='{current_section}-expandable-content'] button[aria-expanded='false']")
            if not expand_buttons:
                break
            scroll_to_click(expand_buttons[0])


def expand_all_sections():
    """
    Expands/Loads/Uncovers all sections of a profile page to make all the details visible for storing/collecting
    """
    accomplishments_section_buttons = []
    counter = 0
    while True:
        if counter % 3 == 0:
            accomplishments_section_buttons = find_elements_by_css(
                "div[class='profile-detail'] button[aria-expanded='false'][class*='pv-accomplishments-block__expand']")
        elements = find_elements_by_css(
            "div[class='profile-detail'] button[aria-expanded='false'][type='button'],a[id='line-clamp-show-more-button']")
        if (len(elements) == 0) or (set(elements) == set(accomplishments_section_buttons)):
            break
        for e in elements:
            if e in accomplishments_section_buttons:
                continue
            scroll_to(e)
            click(e)
        counter += 1

    expand_accomplishments_section(accomplishments_section_buttons)


def expose_profile_content():
    """
    Executes multiple scroll-ups and scroll-downs on a profile page to make all of its contents visible.
    In case the web page is still not completely loaded/exposed, the scraping will scroll up and down for another 2 times
    before throwing a warning that the page is not fully loaded.
    """
    for i in range(1, 4):
        scroll_down()
        scroll_up()
        expand_all_sections()
        sleep(1)

        is_page_complete = find_elements_by_css(css_selector='span.artdeco-loader__bars') == list()
        if is_page_complete:
            break
        elif i == 3:
            logging.warning(f'>>>>> INCOMPLETE PAGE: profile page not fully loaded after 3 attempts <<<<<')


def has_page_error():
    """
    Checks if the error page is shown instead of the actual profile page. This is a minor bug from L---e---'s front-end
    and rarely happens. If this is the case, the scraping will reload the page to fix this misbehavior.
    Returns:
        (bool): True if getting an error page, False othewise
    """
    elements = find_elements_by_css("p[class='error-description']")
    return len(elements) > 0


def get_page_source():
    """
    Gets the source code including the whole DOM tree of a web page encoded in UTF-8.
    The should code will then be stored as an HTML file.

    Returns:
        (str): The source code of a web page
    """
    return _DRIVER.page_source.encode("utf-8")


def check_logged_in(nav_feed=True):
    """
    Checks whether the scraping user is (still) logged in or not as a result of the fact that L---e--- kicks accounts
    with suspicious behaviors out every once in awhile. The login status of the current scraping account :_ACC will
    be set to the result of the check accordingly
    Args:
        nav_feed (bool): True if the scraping should navigate back to the feed/ page to perform the check

    Returns:
        (bool): True if the current user is (still) logged in, False otherwise
    """
    sleep(2)
    if nav_feed and not is_same_url(cur_url(), _FEED_URL):
        go_feed()
    prev_in = get_acc().get_logged_in()
    now_in = find_elements_by_css("header[id='extended-nav']") != []

    if not prev_in and now_in:
        logging.info(f"SUCCESS: Logged-in with {get_acc().get_email()}")
    elif not prev_in and not now_in:
        logging.warning("FAILED: Login attempt failed!")
    elif prev_in and not now_in:
        logging.warning(f"OOPS: User {get_acc().get_email()} got kicked out!")
    # elif prev_in and now_in:
    #     logging.info("INFO: still stay logged-in!")
    get_acc().set_logged_in(now_in)
    return now_in


def jump_internal(dest, sleep_time=0):
    """
    For the purpose of disguising as a normal user. Jumps/Navigates/Browses to an internal (inside l---e---.com) destination
    Args:
        dest (str): the URN referencing to an internal page
        sleep_time (int): the time to stay at the destination page after jumping to it
    """
    go(f"https://www.l---e---.com/{dest}")
    scroll_down()
    sleep(get_rand_time() if sleep_time == 0 else sleep_time)


def jump_feed():
    """
    For the purpose of disguising as a normal user. Jumps/Navigates/Browses to the feed page
    """
    jump_internal("feed/", sleep_time=get_rand_time(3, 5))
    sleep(get_rand_time(5, 8))


def jump_external(dest, sleep_time=0):
    """
    For the purpose of disguising as a normal user. Jumps/Navigates/Browses to an external (outside l---e---.com) destination
    Args:
        dest (str): the URN referencing to an external page
        sleep_time (int): the time to stay at the destination page after jumping to it
    """
    assert "l---e---.com" not in dest
    go(f"https://www.{dest}")
    sleep(get_rand_time() if sleep_time == 0 else sleep_time)


def jump_random(mode):
    """
    For the purpose of disguising as a normal user. Jumps/Navigates/Browses randomly to a page that is not a L---e---
    profile page.
    Args:
        mode (JUMP_MODE): the jumping mode, which can be only jumping internally, only jumping externally or a combination of both
    """
    jump_limit = random.randint(1, 2)

    possible_jump_options = [JUMP_OPTION.FEED]

    if mode == JUMP_MODE.INTERNAL_EXTERNAL:
        possible_jump_options.append(JUMP_OPTION.EXTERNAL)
        possible_jump_options.append(JUMP_OPTION.INTERNAL)
    elif mode == JUMP_MODE.INTERNAL:
        possible_jump_options.append(JUMP_OPTION.INTERNAL)
    elif mode == JUMP_MODE.EXTERNAL:
        possible_jump_options.append(JUMP_OPTION.EXTERNAL)

    jump_options = []
    while len(jump_options) < jump_limit:
        # nav_type = random.choice(['internal', 'external', 'feed'])
        jump_opt = random.choice(possible_jump_options)
        if jump_options.count(jump_opt) < 1:
            jump_options.append(jump_opt)

    # rearrange: make sure same jump_type not next to each other
    options_len = len(jump_options)
    for i in range(options_len - 1):
        if jump_options[i] == jump_options[i + 1]:
            jump_options[(i + 1)] = jump_options[(i + 2) % options_len]
            jump_options[(i + 2) % options_len] = jump_options[i + 1]
            break

    sleep_time = 0
    visited_dests = []
    for jump_opt in jump_options:
        if jump_limit == 1 or jump_limit == 2:
            sleep_time = get_rand_time(10, 12)
        elif jump_limit == 3:
            sleep_time = get_rand_time(6, 12)
        elif jump_limit == 4:
            sleep_time = get_rand_time(4, 9)

        dest = ""
        if jump_opt == JUMP_OPTION.INTERNAL:
            while True:
                dest = random.choice(_RANDOM_INTERNAL_URNS)
                if dest not in visited_dests:
                    break
            jump_internal(dest, sleep_time)

        elif jump_opt == JUMP_OPTION.EXTERNAL:
            while True:
                dest = random.choice(_RANDOM_EXTERNAL_URNS)
                if dest not in visited_dests:
                    break
            jump_external(dest, sleep_time)

        elif jump_opt == JUMP_OPTION.FEED:
            jump_internal('feed/', sleep_time)

        visited_dests.append(dest)


def raise_AccountBlockedException(message=''):
    """
    Raises the AccountBlockedException with a customizable message
    Args:
        message (str): the message of the exception to print on the screen
    """
    if not message:
        message = f"ACCOUNT BLOCKED: Account {get_acc().get_email()} has been restricted by L---e---"
    set_logged_in(False)
    logging.warning(message)
    raise AccountBlockedException(message)


def terminate():
    """
    Terminates the driver. This includes shutting down the Selenium driver and removing the scraping account from this module
    """
    if _DRIVER is not None:
        _DRIVER.quit()
    remove_acc()


def restart():
    """
    Restarts the module. This includes terminating the module object and setting up a new Selenium driver
    """
    terminate()
    build_driver()
