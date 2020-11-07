"""
CONTAIN FUNCTIONS THAT CAN BE REUSED BY MULTIPLE SCRIPTS
"""

import glob
import os
import re
from collections import defaultdict
from datetime import datetime
from os.path import join

import pandas as pd

str_sep = ' | '
tframe_sep = ' - '
special_hyphen = ' – '  # this is not an ordinary hyphen, it's from html files

col_URL = 'L---e---Link'
col_AID = 'author_id'
col_employee_name = 'Employee_Name'

col_company_name = 'Company_Name'
col_company_url = 'Company_URL'
col_role = 'Role'
col_timeframe = 'Timeframe'
col_location = 'Location'

col_cur_employer = 'cur_employer'
col_cur_job_start = 'cur_job_start'
col_cur_job_end = 'cur_job_end'

col_next_employer = 'next_employer'
col_next_job_start = 'next_job_start'
col_days_to_next_job = 'days_to_next_job'
col_months_to_next_job = 'months_to_next_job'

col_second_next_employer = 'second_next_employer'
col_second_next_job_start = 'second_next_job_start'
col_days_to_second_next_job = 'days_to_second_next_job'
col_months_to_second_next_job = 'months_to_second_next_job'

col_E = 'E'
col_E_in_profile = 'E_in_profile'
col_E_timeframe = 'E_timeframe'

col_R = 'R'
col_R_in_profile = 'R_in_profile'
col_R_timeframe = 'R_timeframe'

col_E_in_profile_prior_acq = 'E_in_profile_prior_acq'
col_E_timeframe_prior_acq = 'E_timeframe_prior_acq'

col_R_in_profile_prior_acq = 'R_in_profile_prior_acq'
col_R_timeframe_prior_acq = 'R_timeframe_prior_acq'


def parse_chained_str(chained_str):
    """
    Parse a string that is a concatenation of multiple strings separated by separation character into list of strings
    ======================================================================================
    Args:
        chained_str (str): string chained by str_sep

    Returns:
        list of strings split from the :chained_str
    """
    return chained_str.split(str_sep)


def get_now():
    """
    Get current datetime in specific format e.g. 2020_09_10_12_10. Used to name files in chronological order
    ======================================================================================
    Returns:
        datetime object of current time
    """
    return pd.to_datetime('today').strftime('%Y_%m_%d_%H_%M')


def _get_U2A_or_A2U_mappings(csv_dir, k, v):
    """
    Get mappings from L---e--- profile URLs to author ID or vice versa
    ======================================================================================
    Args:
        csv_dir (str): path to folder storing csv files listing all URLs and author IDs
        k (str): the column name that is the key of the mappings, either :col_AID or :col_URL
        v (str): the column name that is the value of the mappings, either :col_AID or :col_URL
    Returns:
        dict[k -> set(v)]
    """
    df = pd.DataFrame(columns=[col_AID, col_URL])
    for csv_file in glob.glob(join(csv_dir, '*_filtered*.csv')):
        _df = pd.read_csv(csv_file, delimiter=',', header=0, usecols=[col_AID, col_URL], dtype={col_AID: int})
        df = df.append(_df, ignore_index=True)

    mappings = defaultdict(set)
    for i, row in df.iterrows():
        mappings[row[k]].add(row[v])
    return mappings


def get_URL_AID_mappings(csv_dir):
    """
    Get mappings from L---e--- profile URLs to author ID
    ======================================================================================
    Args:
        csv_dir (str): path to folder storing csv files listing all URLs and author IDs

    Returns:
        dict[url -> aid]
    """
    return _get_U2A_or_A2U_mappings(csv_dir, k=col_URL, v=col_AID)


def get_AID_URL_mappings(csv_dir):
    """
    Get mappings from author ID to L---e--- profile URLs
    ======================================================================================
    Args:
        csv_dir (str): path to folder storing csv files listing all URLs and author IDs

    Returns:
        dict[aid -> url]
    """
    return _get_U2A_or_A2U_mappings(csv_dir, k=col_AID, v=col_URL)


def get_file_name(filepath):
    return os.path.basename(os.path.splitext(filepath)[0])


def remove_punctuation(name):
    return re.sub(r'[^\w\s]', '', name)


def _parse_month_year(date_str):
    """
    Parse a date string in '%b %Y' or '%Y' to respective datetime object
    ======================================================================================
    Args:
        date_str (str): the string of date to be parsed
    Returns:
        date (datetime)
    """
    date = None
    if date_str == 'Present':
        date = datetime.now()
    else:
        date = datetime.strptime(date_str, '%b %Y') if ' ' in date_str else datetime.strptime(date_str, '%Y')

    return set_day_to_1(date)


def parse_employment_timeframe(timeframe_str):
    """
    Parse employment timeframe string to a tuple of datetime objects representing start and end dates
    ======================================================================================
    Args:
        timeframe_str (str): timeframe string

    Returns:

    """
    # start_end = [remove_punctuation(time) for time in period_str.split(', ')]
    start_end = [remove_punctuation(time) for time in timeframe_str.split(tframe_sep)]

    if len(start_end) == 1 or not start_end[0] or not start_end[1]:
        raise InvalidTimeframeException('Period start or end is empty')
    elif len(start_end) == 1:
        start_end.append(start_end[0])

    start = _parse_month_year(start_end[0])
    end = _parse_month_year(start_end[1])
    return start, end


def set_day_to_1(date):
    """
    Set the day value of a datetime object to 1
    ======================================================================================
    Args:
        date (datetime): datetime object

    Returns:
        the datetime object with day set to 1
    """
    date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    assert date.day == 1
    return date


def parse_acquisition_date(acq_date):
    """
    Parse acquisition date from '%Y-%m-%d' format
    ======================================================================================
    Args:
        acq_date (str): acquisition date as string

    Returns:
        datetime object of acquisition date
    """
    _acq_date = datetime.strptime(acq_date, '%Y-%m-%d')
    return _acq_date


class InvalidTimeframeException(Exception):
    pass
