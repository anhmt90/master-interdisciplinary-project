import enum
import os
import glob
from os.path import isfile, isdir, join, dirname, realpath, splitext
from scraping import utils

CUR_DIR = dirname(realpath(__file__))
# CUR_GROUP = 'control'
CUR_GROUP = 'treatment'
_SCRAPER_DIR = join(CUR_DIR, 'scraping')
_ANALYSIS_DIR = join(CUR_DIR, 'analysis')


def make_dirs(dirs):
    for dir_ in dirs:
        utils.make_dir(dir_)


class SCRAPING_SUBDIRS:
    SETTINGS = join(_SCRAPER_DIR, 'settings')
    TOOLS = join(_SCRAPER_DIR, 'tools')
    URLS = join(_SCRAPER_DIR, 'urls')
    LOGS = join(_SCRAPER_DIR, 'logs')
    DEBUG_PROFILES = join(LOGS, 'debug_profiles')

    make_dirs([SETTINGS, TOOLS, URLS, LOGS, DEBUG_PROFILES])


class URL_FILTER_PARAMS:
    RUN_OPTION = 'filter'
    PROFILE_DIR = join(SCRAPING_SUBDIRS.URLS, 'original')
    SAVE_DIR = join(SCRAPING_SUBDIRS.URLS, 'filtered')
    INTER_DUPLICATE_DIR = join(SCRAPING_SUBDIRS.URLS, 'inter_duplicates')

    SCAN_DIR = join(PROFILE_DIR)


class ACCOUNT_SIGNUP_ASSISTANT_PARAMS:
    ACC_COUNT = 2
    ACC_SAVE_DIR = SCRAPING_SUBDIRS.SETTINGS
    USE_CHROME_PROFILE = False


class ACCOUNT_PARAMS:
    ACC_SAVE_DIR = SCRAPING_SUBDIRS.SETTINGS
    COUNT = 20


class SCRAPER_PARAMS:
    TARGET_GROUP = CUR_GROUP
    ACC_FILE = glob.glob(join(SCRAPING_SUBDIRS.SETTINGS, 'accounts_*.csv'))[-1]
    # URL_FILE = glob.glob(join(SCRAPING_DIRS.URLS, f'_{TARGET_GROUP}', '*filtered*.csv'))[-1]
    URL_FILE = glob.glob(join(SCRAPING_SUBDIRS.URLS, 'faulty_missing', '*missing*.csv'))[-1]
    CHECKPOINT_FILE = join(SCRAPING_SUBDIRS.SETTINGS, f'{utils.parse_filename(URL_FILE)}.ckp')
    SAVE_DIR = join(CUR_DIR, '..', 'raw_profiles', f'{TARGET_GROUP}_profiles')
    UNAVAILABLE_PROFILES_FILE = join(SCRAPING_SUBDIRS.URLS, 'unavailable_profiles.csv')
    CHROME_DRIVER_FILE = join(SCRAPING_SUBDIRS.TOOLS, 'chromedriver.exe')


class VALIDATOR_PARAMS:
    TARGET_GROUP = CUR_GROUP

    # path to the folder where the profiles are stored as HTML files
    TARGET_DIR = SCRAPER_PARAMS.SAVE_DIR

    # path to the folder where the csv file outlining faulty or missing profiles should be stored
    FAULTY_MISSING_DIR = join(SCRAPING_SUBDIRS.URLS, 'faulty_missing')

    # path to the folder where the csv files containing profile URLs are stored
    URLS_DIR = join(SCRAPING_SUBDIRS.URLS, f'_{TARGET_GROUP}')

    # path to the CSV file listing all URls to unavailable profiles
    UNAVAILABLE_PROFILES_FILE = SCRAPER_PARAMS.UNAVAILABLE_PROFILES_FILE


########################################################################################################################

class ANALYSIS_SUBDIRS:
    ACQ_DATA = join(_ANALYSIS_DIR, 'acq_data')
    EXTRACTED_DATA = join(_ANALYSIS_DIR, 'extracted_data')
    FINAL_DATA = join(_ANALYSIS_DIR, 'final_data')

    make_dirs([EXTRACTED_DATA, FINAL_DATA])


class EXTRACTOR_PARAMS:
    TARGET_GROUP = CUR_GROUP

    # Folder where the profile html files locate
    PROFILE_DIR = SCRAPER_PARAMS.SAVE_DIR
    URLS_DIR = join(SCRAPING_SUBDIRS.URLS, f'_{TARGET_GROUP}')

    FAUTY_PROFILES_DIR = join(ANALYSIS_SUBDIRS.EXTRACTED_DATA, 'faulty')
    # path to csv file that contains faulty html paths
    FAULTY_PROFILES_CSV = join(FAUTY_PROFILES_DIR, f'{TARGET_GROUP}__faulty_pages.csv')

    # If True: continue where left off from the most recent run by reading the extracted profiles from the latest csv file {profile_dir}/faulty_pages*.csv.
    # If False: running from scratch (without reading the last extracted profiles obtained from the recent run)
    CONTINUE_LAST_RUN = False

    # If True, only the set of faulty profile pages listed in the csv file located at :paths_faulty_prev will be extracted.
    # Since the extraction process takes quite long, this param is useful to inspect only a subset of faulty profiles
    RUN_PREV_FAULTY = False

    make_dirs([PROFILE_DIR, FAUTY_PROFILES_DIR])


class INSPECTOR_PARAMS:
    TARGET_GROUP = CUR_GROUP
    ACQ_FILE = join(ANALYSIS_SUBDIRS.ACQ_DATA, 'Employees and related Acquisition Information - v01.csv')

    FINAL_DATA_DIR = ANALYSIS_SUBDIRS.FINAL_DATA
    FAULTY_EMPLOYEES_DIR = join(ANALYSIS_SUBDIRS.FINAL_DATA, 'faulty')
    NONE_MATCHED_DIR = join(ANALYSIS_SUBDIRS.FINAL_DATA, 'none_matched')

    make_dirs([FINAL_DATA_DIR, FAULTY_EMPLOYEES_DIR, NONE_MATCHED_DIR])


class TIMEFRAMES_VISUALIZATION_PARAMS:
    PICKLES_DIR = join(_ANALYSIS_DIR, 'pickles')

    make_dirs([PICKLES_DIR])
