"""
EXTRACT EMPLOYMENT INFORMATION FROM L---e--- HTML PAGES STORED LOCALLY
"""

import logging
from os.path import join, basename
from bs4 import BeautifulSoup

from analysis.utils import *
from analysis.employment_profile import EmploymentProfile, Employment, EmploymentRole
from config import ANALYSIS_SUBDIRS as PATH
from config import EXTRACTOR_PARAMS as PARAM

col_faulty_pages = 'Faulty_Pages'

table_URL_AID = get_URL_AID_mappings(PARAM.URLS_DIR)


def _parse_employment_timeframe(tframe_str):
    """
    Parse employment timeframe from a text string extracted from L---e--- profile page
    ======================================================================================
    :param tframe_str: the original string contain employment timeframe from L---e--- html page
    """
    if special_hyphen in tframe_str:
        tframe_str.replace(special_hyphen, tframe_sep)
    tframe_parts = tframe_str.partition(tframe_sep)
    # start = datetime.datetime.strptime(period_parts[0], '%b %Y')
    # end = period_parts[2] if period_parts[2] == 'Present' else datetime.datetime.strptime(period_parts[2], '%b %Y')

    start = tframe_parts[0]
    end = tframe_parts[2] if tframe_parts[2] == 'Present' else tframe_parts[2]
    end = start if not end else end
    return start, end


def _parse_web_text(text):
    """
    Parse text with many '\n' in L---e--- html pages to get the desired textual info
    ======================================================================================
    :param text: text from L---e--- a html page containing '\n' characters
    """
    return text.strip('\n').partition('\n')[2]


def _save_faulty_page_paths(paths_faulty_html):
    """
    Function to store paths to faulty html files to file_path
    ======================================================================================
    :param paths_faulty_html: set of paths to faulty html pages
    """
    rows = []
    for ep, err_cause in paths_faulty_html.items():
        url = f'https://www.l---e---.com/in/{get_file_name(ep)}'
        author_ids = table_URL_AID[url]
        for aid in author_ids:
            rows.append(pd.Series({col_AID: aid, col_faulty_pages: ep, 'Cause': err_cause}))
    df = pd.DataFrame().append(rows, ignore_index=True)
    df.sort_values(col_AID, inplace=True)
    df.to_csv(PARAM.FAULTY_PROFILES_CSV, index=False)
    logging.info(f'FILE_SAVED: Faulty profile paths stored ({PARAM.FAULTY_PROFILES_CSV})')


def _mark_faulty_pages(paths_faulty_htmls):
    """
    Bookmark paths to faulty html pages and store them in file_path csv file
    ======================================================================================
    :param paths_faulty_htmls: set of paths to faulty html pages
    """
    if os.path.isfile(PARAM.FAULTY_PROFILES_CSV):
        df_existent_faulty_pages = pd.read_csv(PARAM.FAULTY_PROFILES_CSV, delimiter=',', header=0, dtype={col_AID: int})
        for i, row in df_existent_faulty_pages.iterrows():
            paths_faulty_htmls[row[col_faulty_pages]] = paths_faulty_htmls.get(row[col_faulty_pages])

    _save_faulty_page_paths(paths_faulty_htmls)


def _unmark_faulty_pages(extracted):
    """
    Remove faulty pages found in previous runs from the list of faulty pages if they have been re-scraped correctly in the current run
    ======================================================================================
    :param extracted: set of paths to html files done with the extraction
    :param faulty_prev: set of paths to faulty html files from previous runs
    """
    df = pd.read_csv(PARAM.FAULTY_PROFILES_CSV, delimiter=',', header=0, dtype={col_AID: int})
    cur_faulty_htmls = {row[col_faulty_pages]: row['Cause'] for i, row in df.iterrows()}

    for page in set(extracted):
        if cur_faulty_htmls.get(page):
            del cur_faulty_htmls[page]

    _save_faulty_page_paths(cur_faulty_htmls)


def _persist_extracted_profile(rows, finished_profiles_df):
    """
    Stores the list of Pandas rows as df into folder save_dir
    ======================================================================================
    :param rows: list of data frame (df) rows to store as Pandas df
    :param finished_profiles_df: the df of profiles extracted from the most recent run. This will be merged and stored together with the profiles extracted in the current run
    """
    df = pd.DataFrame().append(rows, ignore_index=True)
    if len(finished_profiles_df.index) > 0:
        df = df.append(finished_profiles_df, ignore_index=True)

    df.sort_values(col_URL, inplace=True)
    file_ = join(PATH.EXTRACTED_DATA, f'{PARAM.TARGET_GROUP}__extracted_profiles_{get_now()}.csv')
    df.to_csv(file_, index=False)
    logging.info(f'SUCCESS: Profile data extracted to {file_}')


def extract():
    """
    Main function that run the extraction of profiles from html pages to usable data in csv format
    Faulty profile pages will be bookmarked in a CSV file
    """

    finished_profile_urls = set()
    finished_profiles_df = pd.DataFrame()
    if PARAM.CONTINUE_LAST_RUN:
        profile_info_files = glob.glob(join(PATH.EXTRACTED_DATA, f'{PARAM.TARGET_GROUP}__extracted_profiles_*.csv'))
        last_extraction_file = '' if len(profile_info_files) == 0 else profile_info_files[-1]
        if os.path.isfile(last_extraction_file):
            finished_profiles_df = pd.read_csv(last_extraction_file, delimiter=',', header=0, dtype={col_AID: int})

        for i, row in finished_profiles_df.iterrows():
            finished_profile_urls.add(row[col_URL])

    profiles = []
    extracted_htmls = set()
    faulty_pages = {}
    try:
        target_htmls = list()
        if PARAM.RUN_PREV_FAULTY:
            target_htmls = set(pd.read_csv()[col_faulty_pages])
        else:
            target_htmls = glob.glob(join(PARAM.PROFILE_DIR, '*.html'))

        for i, html in enumerate(target_htmls):
            # if i >= 40:
            #     break
            file_name = get_file_name(html)
            if PARAM.CONTINUE_LAST_RUN and f'https://www.l---e---.com/in/{file_name}' in finished_profile_urls:
                continue
            try:
                with open(html, encoding='UTF-8') as file:
                    logging.info(f'EXTRACT:{i}.{join(basename(PARAM.PROFILE_DIR), file_name)}')
                    bsoup = BeautifulSoup(file.read(), "html.parser")
                    main_section = bsoup.find('main', {'class': 'core-rail'})
                    employee_name = main_section.find('div', {
                        'class': 'display-flex'}).find_next_sibling().ul.li.getText(strip=True)
                    employment_profile = EmploymentProfile(employee_name=employee_name,
                                                           l---e---=f'https://www.l---e---.com/in/{file_name}')

                    exp_section = bsoup.find('section', {'id': 'experience-section'})
                    if not exp_section:
                        raise AttributeError('No employment found')

                    for li in exp_section.ul.findChildren('li', recursive=False):  # each 'li' is an occupation
                        employment = Employment()
                        company_profile_link = li.find('a', {'data-control-name': 'background_details_company'})[
                            'href']
                        employment.company_url = f'https://www.l---e---.com{company_profile_link}' if '/company/' in company_profile_link else ''
                        company_summary_info = li.find('div', {'class': 'pv-entity__company-summary-info'})
                        if company_summary_info is None:
                            employment.company_name = li.a.find('p', {'class': 'visually-hidden'}).find_next_sibling(
                                'p').getText(strip=True).replace('Full-time', '')
                            title = li.a.h3.getText()
                            timeframe = ''
                            if li.a.h4:
                                timeframe = li.a.h4.span.find_next_sibling().getText().replace(special_hyphen,
                                                                                               tframe_sep)

                            employment.roles.append(EmploymentRole(title=title, timeframe=timeframe))

                        else:
                            employment.company_name = _parse_web_text(li.a.h3.getText())
                            employment.duration = _parse_web_text(li.a.h4.getText())
                            for role_li in li.ul.findChildren('li', recursive=False):
                                title = _parse_web_text(role_li.h3.getText())
                                timeframe_div = role_li.h3.find_next_sibling()
                                for _ in range(3):
                                    if 'Dates Employed' in timeframe_div.getText():
                                        break
                                    timeframe_div = timeframe_div.find_next_sibling()

                                timeframe = timeframe_div.find('span', {'class': ''}).getText().replace(special_hyphen,
                                                                                                        tframe_sep)

                                location_h4 = timeframe_div.find_next_sibling('h4')
                                location = '' if location_h4 is None else _parse_web_text(location_h4.getText())

                                employment.roles.append(
                                    EmploymentRole(title=title, timeframe=timeframe, location=location))

                        employment_profile.employments.append(employment)

                    profiles.append(employment_profile)
                    if PARAM.RUN_PREV_FAULTY:
                        extracted_htmls.add(html)

            except AttributeError as ae:
                logging.error(f'PROBLEM:Page {html} cannot be extracted - {ae}')
                faulty_pages[html] = ae
                continue
    finally:
        rows = []
        for profile in profiles:
            for employment in profile.employments:
                for role in employment.roles:
                    for aid in table_URL_AID[profile.l---e---]:
                        row = {
                            col_AID: aid,
                            col_employee_name: profile.employee_name,
                            col_URL: profile.l---e---,
                            col_company_name: employment.company_name,
                            col_company_url: employment.company_url,
                            col_role: role.title,
                            col_timeframe: role.timeframe,
                            col_location: role.location
                        }
                        rows.append(pd.Series(row))
        if rows:
            _persist_extracted_profile(rows, finished_profiles_df)
            if PARAM.RUN_PREV_FAULTY:
                _unmark_faulty_pages(extracted_htmls)
        else:
            logging.info('EMPTY:No profiles extracted')

        if faulty_pages:
            _mark_faulty_pages(faulty_pages)
        else:
            logging.info('CLEAR:No faulty profiles found')


def run():
    """
        Main function executing the module
    """
    print("\n************************************** PARAMERTERS **************************************\n")
    print(f'TARGET_GROUP: {PARAM.TARGET_GROUP}\n')
    print(f'PROFILE_DIR: {PARAM.PROFILE_DIR}\n')
    print(f'URLS_DIR: {PARAM.URLS_DIR}\n')
    print(f'FAULTY_PROFILES_CSV: {PARAM.FAULTY_PROFILES_CSV}\n')
    print(f'CONTINUE_LAST_RUN: {PARAM.CONTINUE_LAST_RUN}\n')
    print(f'RUN_PREV_FAULTY: {PARAM.RUN_PREV_FAULTY}\n')
    print('*****************************************************************************************\n')

    logging.basicConfig(level=logging.INFO)
    extract()


if __name__ == '__main__':
    run()
