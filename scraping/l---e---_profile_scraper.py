import enum
import logging
import time
from time import sleep
from os.path import join
from selenium.common.exceptions import StaleElementReferenceException, JavascriptException

from scraping.utils import *
from scraping import account
from scraping import l---e---_navigator as ln
from scraping.l---e---_navigator import JUMP_MODE

from config import SCRAPING_SUBDIRS as PATH
from config import SCRAPER_PARAMS as PARAM


class MODE(enum.Enum):
    """
    Runs the scraping in default mode or debugger mode
    """
    DEFAULT = 0
    DEBUG_1 = 1
    DEBUG_10 = 10


class L---e---ProfileScraper:
    """
    The main class that drives the whole scraping process
    """

    def __init__(self, urls_filepath, acc_filepath, save_dir_, overwrite_existing=False):
        """

        Args:
            urls_filepath (str): path to the file containing all L---e--- profile URLs to be scraped
            acc_filepath (str): path to the file containing data of user accounts used to log in L---e---
            save_dir_ (str): path to the directory/folder into which the html pages of L---e--- profiles will be stored
            overwrite_existing (): True to allow overwriting profile hmtl pages already scraped by scraping again that profile in case of duplicate URLs,
            False to skip and not scrape again.
        """
        self.exit_code = -1
        self.save_dir = save_dir_
        self.overwrite_existing = overwrite_existing

        # profiles and checkpoints
        self.checkpoint = _build_checkpoint(index=0, name='')
        self.urls_filepath = urls_filepath
        self.profile_urls = []

        # account
        self.acc_filepath = acc_filepath
        self.accounts = account.read_accounts(acc_filepath)

        # statistics
        self.count_total_scraped = 0

        # faulty profiles
        self.unavailable_profiles = set()

        self.run_mode = MODE.DEFAULT
        self._set_up()

    def _set_up(self):
        """
        Support function for the class constructor.
        Sets things up when an object :L---e---ProfileScraper is created and makes the scraping session ready to run. This
        includes creating necessary paths, reading checkpoint, loading profile URLs, starting Selenium driver and selecting
        scraping account
        """
        logging.basicConfig(level=logging.INFO)
        make_dir(PATH.LOGS)
        make_dir(self.save_dir)

        self._read_checkpoint()
        if self.run_mode == MODE.DEFAULT:
            if not self.profile_urls:
                self._load_profile_urls()
        else:
            self._get_debug_profile_urls()

        ln.build_driver()
        self._pick_account()

    def _pick_account(self):
        """
        Picks an scraping account not being blocked from file :self.acc_file
        Returns:
            (bool): True if an account is available, False otherwise
        """
        ln.remove_acc()
        for i, acc in enumerate(self.accounts):
            if not acc.get_blocked():
                ln.set_acc(acc)

        if not ln.get_acc():
            logging.warning('NO ACCOUNTS AVAILABLE: All accounts have been blocked!')
        return ln.get_acc() is not None

    def _get_debug_profile_urls(self):
        """
        FOR DEBUGGING ONLY
        For debugging purpose to avoid reading the whole the complete URL file with potential of modifying the current checkpoint.
        These selected profiles are good examples for debugging misbehaviors regarding to scraping profile pages
        """
        self.profile_urls = ["antonantonenko"]
        if MODE.DEBUG_10:
            self.profile_urls.extend(
                ["pbutlerm", "pjshand", "jwhitlock", "theganyo", "prolfe", "vicdacosta", "osanjuan", "ckdake",
                 "thebrianoneill"])
            assert len(self.profile_urls) == 10
        self.profile_urls = [f"https://www.l---e---.com/in/{name}" for name in self.profile_urls]

    def _load_profile_urls(self):
        """
        Loads the URLs of profiles to be scraped. This includes reading checkpoints to know at which profile to start with,
        reading the profile URls from that checkpoint and formatting them
        """
        logging.info(f"checkpoint read: ({self.checkpoint['index']},{self.checkpoint['profile_name']})")
        self._read_profile_urls()
        self._format_profile_urls()
        logging.info("Done loading up " + str(len(self.profile_urls)) + " profile URLs. "
                                                                        "First profile is " + self.profile_urls[0])

    def _read_profile_urls(self):
        """
        Reads URLs of profiles to be scraped from an csv file. The checkpoint will be investigate and only URLs of profiles
        not yet scraped will be read into :self.profile_urls
        """
        urls = pd.read_csv(f"{self.urls_filepath}", delimiter=',', header=0,
                           skiprows=range(1, self.checkpoint['index']),
                           usecols=['L---e---Link'], squeeze=True).tolist()
        # reader = pd.read_csv(csv_path, delimiter=',', header=0, usecols=['L---e---Link'])
        if self.checkpoint['profile_name']:
            assert self.checkpoint['profile_name'] in urls[0], "Invalid checkpoint indexing"
            del urls[0]
            assert self.checkpoint['profile_name'] not in urls[0], "First profile already scraped"
        self.profile_urls = urls

    def _format_profile_urls(self):
        """
        Formats and standardizes profile URLs such as striping locale strings, tailing backslash
        """
        for i, url in enumerate(self.profile_urls):
            profile_name = parse_profile_name(url)
            if "?" in profile_name:
                logging.warning(f"---> Profile {url} potentially has wrong url format")
                profile_name = strip_query(profile_name)
            if "/" in profile_name:
                profile_name = strip_locale(profile_name)
            elif not profile_name:
                logging.warning(f"---> Profile {url} has wrong url format. Empty profile name parsed")

            self.profile_urls[i] = f"https://www.l---e---.com/in/{profile_name}"

        logging.info(
            "Done formatting " + str(len(self.profile_urls)) + " profile URLs. First profile is " + self.profile_urls[
                0])

    def _persist_profile(self):
        """
        Persists the profile web page to local storage
        """
        profile_name = parse_profile_name(ln.cur_url())
        dir_ = self.save_dir if self.run_mode == MODE.DEFAULT else PATH.DEBUG_PROFILES
        file_name = join(dir_, f'{profile_name}.html')
        with open(file_name, 'wb') as file:
            file.write(ln.get_page_source())
            self._update_checkpoint(profile_name)
            logging.info(
                f"SUCCESS: profile page {self.checkpoint['profile_name']} persisted. {self.checkpoint['index']} profiles scraped.")

    def _update_checkpoint(self, new_profile_name=''):
        """
        Updates the current checkpoint by adding 1 to the index and changes the profile name accordingly
        Args:
            new_profile_name (str): the name of the profile most recently scraped
        """
        self.checkpoint['index'] = self.checkpoint['index'] + 1
        self.checkpoint['profile_name'] = new_profile_name

    def _read_checkpoint(self):
        """
        Reads the checkpoint stored in the local storage to start scraping from the profile name contained in it
        """
        profile_index = 0
        profile_name = ''
        with open(PARAM.CHECKPOINT_FILE, "a+", encoding='utf-8') as file:
            assert len(file.readlines()) <= 1, "ERROR: Multiple lines found in checkpoint file " + PARAM.CHECKPOINT_FILE
            file.seek(0, 0)
            line = file.readline()
            if line:
                stop_at = line.split(",")
                profile_index = int(stop_at[0])
                profile_name = stop_at[1]

        self.checkpoint = _build_checkpoint(index=profile_index, name=profile_name)

    def _persist_checkpoint(self):
        """
        Persists/Records the checkpoint into local storage so that when the scraping can start over from the profile just being scraped
        """
        with open(PARAM.CHECKPOINT_FILE, 'w', encoding='utf-8') as file:
            print("Checkpoint persisted at: (" + str(self.checkpoint['index']) + "," + str(
                self.checkpoint['profile_name']) + ")")
            file.write(str(self.checkpoint['index']) + "," + str(self.checkpoint['profile_name']))

    def _remove_cur_url(self):
        """
        Removes the current profile URL from the list of profiles to be scraped. This is always the first profile of the list
        """
        del self.profile_urls[0]

    def _handle_destination_unreachable(self, url):
        """
        Catches and handles possible cases during the scraping when an url is not reachable. The reasons could be the current scraping
        account gets blocked, a CAPTCHA shows up or the profile is not available.
        Args:
            url (str): the destination urls

        Returns:
            (bool): True if the cause has been fixed, False otherwise

        Raises:
            AccountBlockedException: If the current scraping account has been blocked by L---e---
            ProfileUnavailableException: If the target profile is not available
            UnknownPageException: If being redirected to an unknown page
        """
        logging.info("Could not reach destination URL. Retrying...")
        if "authwall" in ln.cur_url():
            return ln.is_logged_in()

        elif "signup/cold-join" in ln.cur_url():
            return ln.is_logged_in()

        elif "/checkpoint/challenge" in ln.cur_url():
            ln.handle_challenge_and_inspect_login_state()
            if ln.is_logged_in():
                return True
            ln.login_uas()
            return ln.check_logged_in()

        elif "checkpoint/lg/login-submit" in ln.cur_url():
            ln.raise_AccountBlockedException()

        elif '/in/unavailable/' in ln.cur_url():
            raise ProfileUnavailableException("Profile unavailable: " + url)

        elif not parse_profile_name(url):
            raise ProfileUnavailableException(
                f"Profile name empty due to wrong format (index {self.checkpoint['index'] + 1}). Previous profile: {self.checkpoint['profile_name']} ")

        else:
            raise UnknownPageException(
                f"--> ERROR: Unknown page reached. Current URL: {ln.cur_url()}. Expected URL: {url}")

    def _increase_logging_counter(self):
        """
        Increases the counter of total profiles that have been scraped in this scraping session and by the scraping account.
        This is just for logging and statistical purposes
        """
        self.count_total_scraped += 1
        ln.get_acc().increase_scraped_count(by=1)

    def _handle_profile_page(self):
        """
        Arranges the steps and the corresponding functions to handle a L---e--- profile page. This includes expanding all
        sections of the profile page, storing it, update checkpoint afterwards.
        """
        ln.expose_profile_content()
        self._persist_profile()
        self._increase_logging_counter()
        self._remove_cur_url()

        if self.checkpoint['index'] % 10 == 0:
            self._persist_checkpoint()

        sleep(get_rand_time())
        ln.jump_random(mode=JUMP_MODE.INTERNAL)

    def _skip_profile(self, profile_name):
        """
        Skips/Ignores a profile and does not scrape it by removing it from the list of profiles to be scraped and updating the
        checkpoint accordingly
        Args:
            profile_name (str): the profile name
        """
        del self.profile_urls[0]
        self._update_checkpoint(profile_name)

    def _skip_if_existing(self, url):
        """
        Checks whether the L---e--- profile at URL :url has been scraped and stored or not. If yes, the scraping won't go :url and
        skip this URL. This is useful because every fake L---e--- account can only visit 50 profiles before being blocked
        Args:
            url (str): the URL of an L---e--- profile

        Returns:
            (boolean): True if the profile at :url is already scraped, False otherwise
        """
        profile_name = parse_profile_name(url)
        is_existing = os.path.isfile(join(self.save_dir, f'{profile_name}.html'))
        if is_existing:
            logging.info(f'SKIP: Profile {url} already scraped')
            self._skip_profile(profile_name)
        return is_existing

    def _record_unavailable_profiles(self):
        """
        Stores URLs of unavailable L---e--- profiles into a csv file
        """
        if os.path.isfile(PARAM.UNAVAILABLE_PROFILES_FILE):
            self.unavailable_profiles.update(set(pd.read_csv(PARAM.UNAVAILABLE_PROFILES_FILE)[col_URL]))

        if self.unavailable_profiles:
            df = pd.DataFrame([{col_URL: url} for url in self.unavailable_profiles],
                              columns=['L---e---Link'])
            df.to_csv(PARAM.UNAVAILABLE_PROFILES_FILE, index=False)

    def exec(self):
        """
        The main function of class :L---e---ProfileScraper to drive the while scraping process
        Returns:
            (int): exiting codes for further handling the results of the scraping process
        """
        start_time = time.time()
        try:
            while len(self.profile_urls) >= 1:
                if not ln.get_acc():
                    ln.raise_AccountBlockedException()

                url = next(iter(self.profile_urls))
                if not self.overwrite_existing and self._skip_if_existing(url):
                    continue

                logging.info(f"START SCRAPING: {url}")
                try:
                    if not ln.check_logged_in():
                        ln.login_uas()
                        if not is_same_url(ln.cur_url(), ln.feed_url()):
                            self._handle_destination_unreachable(url)

                    if not is_same_url(ln.cur_url(), url) or '/check/bounced-email' in ln.cur_url():
                        ln.go(url)

                    retries = 1
                    while not is_same_url(ln.cur_url(), url):
                        success = self._handle_destination_unreachable(url)
                        if success:
                            break
                        elif not success and retries == 2:
                            return 1
                        retries += 1

                    if ln.has_page_error():
                        continue

                    if not ln.check_logged_in(nav_feed=False):
                        break
                    self._handle_profile_page()

                except AccountBlockedException:
                    ln.get_acc().set_blocked(True)
                    _log_account_session(start_time)
                    ln.restart()
                    success = self._pick_account()
                    if not success:
                        return 103
                    continue

                except ProfileUnavailableException as pue:
                    logging.error(pue)
                    self.unavailable_profiles.add(url)
                    self._update_checkpoint(parse_profile_name(url))
                    self._remove_cur_url()
                    continue

                except JavascriptException as jse:
                    logging.error(jse)
                    ln.go(self.profile_urls[0])
                    if is_same_url(ln.cur_url(), self.profile_urls[0]):
                        continue

                except (StaleElementReferenceException, UnknownPageException) as e:
                    logging.error(e)
                    continue

                except Exception as e:
                    # e = sys.exc_info()[0]
                    logging.error(e)
                    with open(PATH.LOGS + "_exception_page_source.html", 'wb') as file:
                        file.write(ln.get_page_source())
                    return 102
            return 0
        finally:
            if self.run_mode == MODE.DEFAULT:
                self._persist_checkpoint()
            account.update_file(self.accounts, file_path=self.acc_filepath)
            self._record_unavailable_profiles()
            if ln.get_acc() is not None:
                _log_account_session(start_time)
            ln.terminate()


def _log_account_session(start_time):
    """
    Stores the logs of the scraping session
    Args:
        start_time (float): the start time of the scraping session
    """
    if ln.get_acc() and ln.get_acc().get_scraped_count() > 0:
        acc_session_log = f"STOP::{datetime.now()}::{ln.get_acc().get_scraped_count()} profiles scraped by {ln.get_acc().get_email()} in {round((time.time() - start_time) / 60, 2)} mins\n"
        logging.info(acc_session_log)
        with open(f'{PATH.LOGS}scraping-sessions.log', 'a+') as file:
            file.write(acc_session_log)


def _build_checkpoint(index, name):
    """
    Builds a checkpoint, which is a dict with 2 key-value pairs
    Args:
        index (int): the ordinal index number in the URL file of the profile most recently scraped
        name (str): the name of the profile

    Returns:
        (dict): includes the index and the profile name the profile most recently scraped
    """
    return {
        'index': index,
        'profile_name': name
    }


def run():
    print("\n************************************** PARAMERTERS **************************************\n")
    print(f'URL_FILE: {PARAM.URL_FILE}\n')
    print(f'SAVE_DIR: {PARAM.SAVE_DIR}\n')
    print(f'CHECKPOINT_FILE: {PARAM.CHECKPOINT_FILE}\n')
    print(f'ACC_FILE: {PARAM.ACC_FILE}\n')
    print('*****************************************************************************************\n')

    lps = L---e---ProfileScraper(PARAM.URL_FILE, PARAM.ACC_FILE, PARAM.SAVE_DIR, overwrite_existing=True)
    lps.exec()


if __name__ == '__main__':
    run()
