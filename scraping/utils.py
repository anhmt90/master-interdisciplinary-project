import glob
import os
from os.path import normpath, basename, dirname, splitext
import random
from collections import defaultdict
from datetime import datetime
import pytz
import pandas as pd
import numpy as np

col_URL = 'L---e---Link'
col_AID = 'author_id'

sep = os.sep


def get_now():
    return datetime.now(pytz.timezone('Europe/Berlin')).strftime('%Y_%m_%d_%H_%M_%S')


def get_embedded_link_script(url):
    # return "document.body.innerHTML='<a name=\"" + link_name + "\" href= \"" + url + "\">" + url + " </a>'"
    # document.body.innerHTML='<a href= \"" https://www.l---e---.com/in/anh-ma "\">" + url + " </a>'
    return "document.body.innerHTML='<a name=\"" + "embedded_link" + "\" href= \"" + url + "\">" + url + " </a>'"


def parse_redirect_url(dest_url, cookies=None):
    """
    Parse the tracking code from cookies.
    Args:
        dest_url (str): The target URL to go to
        cookies (list<str>): The list of cookies, each is a string

    Returns:
        (str): the redirected URLs
    """
    if cookies is None:
        cookies = []
    trk = "bf"
    trkInfo = "bf"
    for cookie in cookies:
        if (cookie.name == "trkCode") and cookie.value:
            trk = cookie.value

        elif (cookie.name == "trkInfo") and cookie.value:
            trkInfo = cookie.value

    username = dest_url.rsplit("/", 1)[1]
    redirect_url = "https://www.l---e---.com/authwall?trk=" + trk + "&trkInfo=" + trkInfo + \
                   "&originalReferer=&sessionRedirect=https%3A%2F%2Fwww.l---e---.com%2Fin%2F" + username
    return redirect_url


def make_dir(path):
    os.makedirs(path, exist_ok=True)


def get_rand_time(lbound=8.0, ubound=12.0, integer=True):
    if integer:
        return random.randint(lbound, ubound)
    step = 0.1
    return random.choice(np.arange(lbound, ubound + step, step))


def strip_query(profile_name_with_query):
    return profile_name_with_query.partition("?")[0]


def strip_locale(profile_name_with_locale):
    return profile_name_with_locale.partition('/')[0]


def parse_profile_name(url):
    profile_name = strip_ending_backslash(url).partition("/in/")[2]
    return profile_name


def strip_ending_backslash(url):
    if url[len(url) - 1] == "/":
        url = url[:len(url) - 1]
    return url


def is_same_url(current_url, url):
    return strip_ending_backslash(current_url) == url


# def parse_filename(filepath):
#     file_name_ext = filepath.rsplit(sep, 1)[1]
#     if file_name_ext.rfind('.') > -1:
#         return file_name_ext.rsplit('.', 1)[0]
#     return file_name_ext


def parse_filename(filepath):
    """
    Gets file name without extension from a relative or absolute file path
    Args:
        filepath (str): Path to a file

    Returns:
        (str): The resulting file name without extension from a relative or absolute file path
    """

    return splitext(basename(filepath))[0]


class ProfileUnavailableException(Exception):
    pass


class UnknownPageException(Exception):
    pass


class AccountBlockedException(Exception):
    pass
