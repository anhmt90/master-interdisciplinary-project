import logging
import sys
from bs4 import BeautifulSoup
from os.path import isfile, isdir, join

from analysis.utils import *
from scraping.utils import *

from config import VALIDATOR_PARAMS as PARAM


# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.append('..')


def filter_faulty_profile_pages(from_prev_run=False):
    """
    Extracts and stores the list of all public profile pages that are scraped without logging in L---e---, which may not
    contain full profile data as well as profiles pages that are not fully loaded due to network latency. These profiles will
    be bookmarked in a csv file for scraping again later on.
    Args:
        from_prev_run (bool): if True, the filter will only look for profiles filtered in the last run. This list of profiles
    is stored in the latest csv file in save_dir. If this list is empty, or no 'scrape_again*.csv' found, the filter
    will consider all profiles in profile_dir.
    """

    logging.info("RUNNING: Run the validator for filtering faulty profile pages")
    if not isdir(PARAM.TARGET_DIR):
        logging.error('PROFILE DIR NOT FOUND')

    else:
        html_files = []
        if from_prev_run:
            scrape_again_files = glob.glob(join(PARAM.FAULTY_MISSING_DIR, f'{PARAM.TARGET_GROUP}*scrape_again*.csv'))
            if not scrape_again_files:
                logging.info("FILES_NOT_FOUND: No `scrape_again` files found!")
                exit()
            scrape_again_file = scrape_again_files[-1]
            if scrape_again_file:
                prev_filtered_urls = set(pd.read_csv(scrape_again_file)[col_URL])
                html_files.extend(
                    [join(PARAM.TARGET_DIR, f'{url.split("/in/")[1]}.html') for url in prev_filtered_urls])

        if not html_files:
            html_files = glob.glob(join(PARAM.TARGET_DIR, '*.html'))
            logging.info(f'FOUND: {len(html_files)} html files')

        faulty_pages = {}
        for i, page in enumerate(html_files):
            if not os.path.isfile(page):
                logging.warning(f'Profile {page}')
                continue

            with open(page, encoding='UTF-8') as file:
                logging.info(f'{i}.INSPECT:{os.path.join(basename(dirname(page)), basename(page))}')
                bsoup = BeautifulSoup(file.read(), "html.parser")
                if not bsoup.find('main', {'class': 'core-rail'}):
                    faulty_pages[f'https://www.l---e---.com/in/{parse_filename(page)}'] = 'page not loaded'
                    continue

                if bsoup.find('span', {'class': 'artdeco-loader__bars'}) or bsoup.find('span',
                                                                                       {
                                                                                           'class': 'artdeco-spinner--bars'}):
                    faulty_pages[f'https://www.l---e---.com/in/{parse_filename(page)}'] = 'incomplete'
                    continue

                nav_header = bsoup.find('header', {'id': 'extended-nav'})
                if not nav_header:
                    faulty_pages[f'https://www.l---e---.com/in/{parse_filename(page)}'] = 'not logged in'

        if faulty_pages:
            make_dir(PARAM.FAULTY_MISSING_DIR)
            df = pd.DataFrame([{col_URL: url, 'Cause': cause} for url, cause in faulty_pages.items()],
                              columns=[col_URL, 'Cause'])
            _file = join(PARAM.FAULTY_MISSING_DIR, f'{basename(PARAM.TARGET_DIR)}__scrape_again__{get_now()}.csv')
            df.to_csv(_file, index=False)
            logging.info(f'SAVED: File {_file} saved')
        else:
            logging.info('No erroneous profile pages found')


def verify_missing_profiles():
    """
    Checks the profiles scraped against the list of profile URLs to see which profiles have not been scraped.
    The list of missing profiles if any will be stored as csv file after the verification.
    """

    logging.info("RUNNING: Run the validator for verifying missing profile pages")
    missing_profiles = set()
    all_urls = get_URL_AID_mappings(PARAM.URLS_DIR).keys()
    for i, url in enumerate(all_urls):
        if (i > 0 and i % 500 == 0) or i == len(all_urls) - 1:
            print(f'VERIFYING_MISSING_PROFILES: Done verifying {i} profiles')
        if '/in/' in url:
            profile_name = url.partition('/in/')[2]
            profile_path = join(PARAM.TARGET_DIR, f'{profile_name}.html')
            if not os.path.isfile(profile_path):
                missing_profiles.add(url)

            if len(profile_name) == 2:
                logging.debug(f'Possibly invalid profile: {profile_name}')

    unavailable_profiles = set()
    if isfile(PARAM.UNAVAILABLE_PROFILES_FILE):
        unavailable_profiles = set(pd.read_csv(PARAM.UNAVAILABLE_PROFILES_FILE)[col_URL])

    missing_profiles.difference_update(unavailable_profiles)
    logging.info(f'COUNT:{len(missing_profiles)} missing profiles found!')
    if missing_profiles:
        make_dir(PARAM.FAULTY_MISSING_DIR)
        df = pd.DataFrame([{col_URL: url} for url in missing_profiles], columns=[col_URL])
        df.to_csv(join(PARAM.FAULTY_MISSING_DIR, f'{basename(PARAM.TARGET_DIR)}__missing_profiles__{get_now()}.csv'),
                  index=False)
        for url in missing_profiles:
            logging.info(f'MISSING:{url}')


def run():
    """
        Main function executing the module
    """
    print("\n************************************** PARAMERTERS **************************************\n")
    print(f'PROFILE_DIR: {PARAM.TARGET_DIR}\n')
    print(f'FAULTY_MISSING_DIR: {PARAM.FAULTY_MISSING_DIR}\n')
    print(f'URL_DIR: {PARAM.URLS_DIR}\n')
    print('*****************************************************************************************\n')

    logging.basicConfig(level=logging.INFO)

    filter_faulty_profile_pages(from_prev_run=False)
    verify_missing_profiles()


if __name__ == '__main__':
    run()
