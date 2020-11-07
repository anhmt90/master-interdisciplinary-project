import logging
from collections import namedtuple
from os.path import isfile, isdir, exists, join, basename, splitext
import shutil

# print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__, __name__, str(__package__)))
from scraping.utils import *
from config import URL_FILTER_PARAMS as PARAM

tup_name = 'Profile'


def _read_profile_urls(csv_file):
    """
    Read profile URLs from a CSV file into a pandas.DataFrame
    Args:
        csv_file (str): Path to the CSV containing profile URLs

    Returns:
        (pandas.DataFrame): The pandas.DataFrame containing profile URLs
    """
    df = pd.read_csv(csv_file, delimiter=',', header=0, usecols=[col_AID, col_URL], squeeze=True, dtype={col_AID: str})
    logging.info(f"DONE_FETCHING: {len(df)} entries fetched")
    return df


def _format_profile_urls(df, idc):
    """
    Formats and standardizes profile URLs such as striping locale strings, tailing backslash

    Args:
        df (pandas.DataFrame): The pandas.DataFrame containing profile URLs to be formatted in column 'L---e---Link'
        idc (IntraDuplicateCounter): An IntraDuplicateCounter object to store invalid URLs found

    Returns:
        (pandas.DataFrame): The resulting pandas.DataFrame containing the formatted profile URLs
    """
    for i, row in df.iterrows():
        url = row[col_URL]
        profile_name = parse_profile_name(url)
        if "?" in profile_name:
            idc.invalid_urls[url] = 1 if not idc.invalid_urls.get(url) else (idc.invalid_urls.get(url) + 1)
            profile_name = strip_query(profile_name)
        if "/" in profile_name:
            profile_name = strip_locale(profile_name)
        elif not profile_name:
            idc.invalid_urls[url] = 1 if not idc.invalid_urls.get(url) else (idc.invalid_urls.get(url) + 1)

        if profile_name:
            row[col_URL] = f"https://www.l---e---.com/in/{profile_name}"

    logging.info(f'DONE_FORMATTING: {len(df)} entries formatted')
    return df


class IntraDuplicateCounter:
    """
    A Class that helps represent information information such as number of rows, number of invalid URLs number of duplicate profile URLs within
    a CSV file (intra-duplcates)
    """

    def __init__(self, filepath):
        self.file_path = filepath
        self.file_name = parse_filename(filepath)
        self.num_rows = 0
        self.invalid_urls = defaultdict(int)
        self.df = _format_profile_urls(_read_profile_urls(filepath), self)
        self.intra_duplicates = count_intra_duplicate_urls(self.df)


def filter_intra_duplicate_urls(df, intra_duplicate_URLs):
    """
    Removes all duplicate profile URLs WITHIN a pandas.DataFrame from it

    Args:
        df (pandas.DataFrame): The pandas.DataFrame whose duplicate URLs should be removed/filtered
        intra_duplicate_URLs (dict[str -> int]): The dict mapping duplicate profile URLs to the number of its occurrences

    Returns:
        (pandas.DataFrame): The pandas.DataFrame without any duplicate URLs
    """
    _intra_duplicates = intra_duplicate_URLs.copy()
    for i, row in df.iterrows():
        url = row[col_URL]
        if _intra_duplicates.get(url) and _intra_duplicates.get(url) > 0:
            df.drop(i, inplace=True)
            _intra_duplicates[url] -= 1
    return df


def count_intra_duplicate_urls(df):
    """
    Counts how many duplicate URLs WITHIN a pandas.DataFrame

    Args:
        df (pandas.DataFrame): The pandas.DataFrame to count for duplicate URLs

    Returns:
        (dict[str -> int]): The dict mapping duplicate profile URLs to the number of its occurrences
    """
    duplicates = {}
    _df = df.sort_values(col_URL)
    for i in range(len(_df)):
        if i == 0:
            continue
        cur_row = _df.iloc[i]
        prev_row = _df.iloc[i - 1]
        if cur_row[col_URL] == prev_row[col_URL]:
            key = cur_row[col_URL]
            duplicates[key] = 1 if duplicates.get(key) is None else (duplicates.get(key) + 1)
    return duplicates


def intersect_tuples(target_tuples, template_tuples):
    """
    Performs an intersection operation of two sets of (author_id, URls)-tuples based on the URLs. The function returns
    a new set of tuples that have their URLs appear in both input sets.

    Args:
        target_tuples (set[tuple]): The first set of (author_id, URls)-tuples
        template_tuples (set[tuple]): The second set of (author_id, URls)-tuples

    Returns:
        (set[tuple]): The set of (author_id, URls)-tuples as a result of the intersection of the two input sets
    """
    target_dict = {url: aid for aid, url in target_tuples}
    template_dict = {url: aid for aid, url in template_tuples}
    Profile = namedtuple(tup_name, [col_AID, col_URL])
    return set([Profile(target_dict[dup_url], dup_url) for dup_url in target_dict.keys() & template_dict.keys()])


def _generate_URL_files(target_csv, unique_tups, duplicate_tups):
    """
    Generates a CSV file containing unique L---e--- profile URls and a CSV file containing duplicate ones

    Args:
        target_csv (str): path to the CSV file containing URLs that needs to be verified for duplicates
        unique_tups (set[tuple]): set of tuples of unique L---e--- profile URLs
        duplicate_tups (set[tuple]): set of tuples of duplicate L---e--- profile URLs

    Returns:
        (bool): If True, the two files of unique and duplicate URLs have been successfully created, False otherwise
    """
    df_uniques = pd.DataFrame([{col_AID: eval(f'tup.{col_AID}'),
                                col_URL: eval(f'tup.{col_URL}'),
                                } for tup in unique_tups],
                              columns=[col_AID, col_URL])

    df_duplicates = pd.DataFrame([{col_AID: eval(f'tup.{col_AID}'),
                                   col_URL: eval(f'tup.{col_URL}'),
                                   } for tup in duplicate_tups],
                                 columns=[col_AID, col_URL])

    file_name = parse_filename(target_csv)
    is_created = False
    i = 0
    while not is_created:
        new_file = join(PARAM.SAVE_DIR, f"{file_name}_filtered_{get_now()}.csv")
        if exists(new_file):
            i += 1
        else:
            with open(new_file, 'a+', newline='') as file:
                df_uniques.to_csv(file, header=file.tell() == 0, index=False)

            make_dir(PARAM.INTER_DUPLICATE_DIR)  # inter-duplicates mean duplicate URLs across many CSV files
            new_file_duplicates = join(PARAM.INTER_DUPLICATE_DIR, f'{file_name}_duplicates_{get_now()}.csv')

            if not df_duplicates.empty:
                with open(new_file_duplicates, 'a+', newline='') as file:
                    df_duplicates.to_csv(file, header=file.tell() == 0, index=False)

            is_created = True
            logging.info(f"DONE_FILTERING: {len(df_uniques)} unique profile URLs stored in {new_file}.")
            if len(df_duplicates) > 0:
                logging.info(
                    f"DUPLICATES_FOUND: {len(df_duplicates)} inter-duplicate profile URLs stored in {new_file_duplicates}")
            else:
                logging.info(f"CLEAR: No inter-dupplicates found!")

    return is_created


def _verify_filtering_results(target_df, others_df, unique_tups, duplicate_tups):
    """
    Checks whether the process of filtering the duplicate URLs has been done correctly. The check performs the filtering
    again with lists of URLs instead of tuples and compares whether the respective sets of URLs are equal to one another.
    The function returns nothing since the check is based on 'assert' statements.

    Args:
        target_df (pandas.DataFrame):
        others_df (pandas.DataFrame):
        unique_tups (set[tuple]): set of tuples of L---e--- profile URLs that need to be checked for duplications
        duplicate_tups (set[tuple]):
    """
    target_urls = set(target_df[col_URL].tolist())
    assert len(target_df) == len(target_urls)

    others = set(others_df[col_URL].tolist())

    duplicates = target_urls.intersection(others)
    unique_urls = target_urls.difference(duplicates)

    assert set([eval(f'tup.{col_URL}') for tup in unique_tups]) == unique_urls
    assert set([eval(f'tup.{col_URL}') for tup in duplicate_tups]) == duplicates


def _filter_duplicate_urls_OvM(target_csv):
    """
    Filters out duplicate profile urls in a target CSV file by comparing its URLs against all other URls
    in other CSV files located in the same folder (One vs. Many comparisons).
    The goal is to have no duplicate URls in the target CSV file compared to all other csv files located in a target folder.

    Args:
        target_csv (str): path to the target CSV file containing URLs that needs to be verified for duplicates

    Returns:
        (bool): If True, a new CSV file without duplicate URLs has been created successfully, False otherwise
    """

    idc = IntraDuplicateCounter(target_csv)

    target_df = idc.df.copy()

    target_df = filter_intra_duplicate_urls(target_df, idc.intra_duplicates)

    others_df = pd.DataFrame(columns=[col_AID, col_URL])
    cur_file_name = parse_filename(target_csv)
    if isdir(PARAM.PROFILE_DIR):
        for file in glob.glob(join(PARAM.SAVE_DIR, "*filtered*.csv")):
            if cur_file_name not in parse_filename(file):
                others_df = others_df.append(_read_profile_urls(file), ignore_index=True)
                logging.info(f'TEMPLATE_READ: {file}')

    assert count_intra_duplicate_urls(others_df) == {}

    target_tups = set(target_df.itertuples(index=False, name=tup_name))
    other_tups = set(others_df.itertuples(index=False, name=tup_name))
    duplicate_tups = intersect_tuples(target_tups, other_tups)

    unique_tups = target_tups.difference(duplicate_tups)
    _verify_filtering_results(target_df, others_df, unique_tups, duplicate_tups)

    return _generate_URL_files(target_csv, unique_tups, duplicate_tups)


def _backup_existing_CSV_files(from_, to_):
    csv_files = glob.glob(join(from_, '*.csv'))
    for csv in csv_files:
        shutil.move(csv, to_)


def filter_duplicate_urls():
    """
    Filters out duplicate profile URLs contained in CSV files located in a folder to one another. CSV files that
    have `_filtered` suffix will be skipped for the comparison. Files that have been processed will
    be tagged with suffix `_filtered` in file name and will be copied to :PARAM.PROFILE_DIR/filtered/, while their duplicate URLs
    will be copied to :PARAM.PROFILE_DIR/duplicates/.
    The goal is to have no duplicate URls among all csv files located in a target folder.
    Note that the folder :PARAM.SAVE_DIR should not contain any CSV files for the filter to work correctly. The filter
    will therefore move all CSV files to the subfolder :PARAM.SAVE_DIR/prev before proceeding
    """

    if not isdir(PARAM.PROFILE_DIR):
        logging.error(f'ERROR: {PARAM.PROFILE_DIR} is not a valid directory')
        exit()

    backup_dir = join(PARAM.SAVE_DIR, 'prev')
    make_dir(backup_dir)
    _backup_existing_CSV_files(from_=PARAM.SAVE_DIR, to_=backup_dir)

    csv_files = glob.glob(join(PARAM.PROFILE_DIR, '*.csv'))
    for file in csv_files:
        if 'filtered' in file:
            continue
        print()
        logging.info(f'FILTER: {file}')
        success = _filter_duplicate_urls_OvM(file)
        if not success:
            logging.warning(f'ERROR: An error occured while filtering duplicates from file {file}')


########################################################################################################################
def make_mappings_from_AID_URL_df(df, k=0, v=1):
    """
    Builds author_id <-> URL author_id mappings from a pandas.DataFrame with two respective columns

    Args:
        df (pandas.DataFrame): The pandas.DataFrame containing only columns of 'author_id' and 'L---e---Link'
        k (int): Takes only value 0 or 1. If k=0, the first column of :df will be the keys of the resulting mappings, otherwise, the second column is
        v (int): Takes only value 0 or 1. If v=1, the second column of :df will be the values of the resulting mappings, otherwise, the first column is

    Returns:
        (dict[str -> str]): the dict that maps author_id -> profile URLs or vice versa
    """
    tups = list(df.itertuples(index=False))
    res = defaultdict(set)
    for i in range(len(tups)):
        res[tups[i][k]].add(tups[i][v])
    return {_k: _v for _k, _v in res.items() if len(_v) > 1}


def sort_csv(file_path, col_name):
    """
    Sorts a csv file by a specified column

    Args:
        file_path (str): path to the csv file
        col_name (str): Name of the column, by which the csv should be sorted
    """
    if isfile(file_path):
        df = pd.read_csv(file_path, delimiter=',', header=0, dtype={col_AID: int})
        df.sort_values(col_name, inplace=True)
        df.to_csv(file_path, index=False, mode='w')


def _scan_invalid_mapping_between_AIDs_URLs(target_dir, sadu=True):
    """
    Scans invalid mappings between author_id's and profile URLs of all csv files inside a folder.
    Invalid cases could be the case that an author_id is mapped to multiple profile URLs or vice versa.
    Such duplicates will be stored in a folder called 'tricky_duplicates' inside the folder ./urls/

    Args:
        target_dir (str): path to folder, in which all csv files containing profile URLs are located
        sadu (bool): If true, run for the case "Same Author_id with Different URLs", else run for
                        "Same URLs with Different Author_id's" (SUDA)
    """
    case_adapter = {
        'file_name': 'same_authorid_diff_urls' if sadu else 'same_url_diff_authorids',
        'column_labels': [col_AID, col_URL] if sadu else [col_URL, col_AID],
        'sort_col': col_AID if sadu else col_URL
    }

    tricky_duplicates_dir = f'{target_dir}tricky_duplicates'
    file_ = f'{tricky_duplicates_dir}/{case_adapter["file_name"]}_{get_now()}.csv'
    for csv_file in glob.glob(f"{target_dir}*.csv"):
        idc = IntraDuplicateCounter(csv_file)
        col_idx_AID = idc.df.columns.get_loc(col_AID)
        col_idx_URL = idc.df.columns.get_loc(col_URL)
        # idc.df = remove_duplicate_urls(idc.df, idc.intra_duplicates)
        duplicate_table = make_mappings_from_AID_URL_df(idc.df, k=col_idx_AID, v=col_idx_URL) \
            if sadu else make_mappings_from_AID_URL_df(idc.df, k=col_idx_URL, v=col_idx_AID)

        if not duplicate_table:
            continue

        make_dir(tricky_duplicates_dir)

        rows = []
        for k, v in duplicate_table.items():
            for elem in v:
                rows.append(pd.Series([k, elem], index=case_adapter['column_labels']))

        duplicates = pd.DataFrame(rows, columns=case_adapter['column_labels'])

        with open(file_, 'a+', newline='') as _file:
            duplicates.to_csv(_file, header=(_file.tell() == 0), index=False)

    sort_csv(file_, case_adapter['sort_col'])


def scan_same_authorID_with_different_urls(target_dir):
    """
    Scans for cases where an author_id gets assigned to different profile URLs.

    Args:
        target_dir (str): path to folder, in which all csv files containing profile URLs are located
    """
    _scan_invalid_mapping_between_AIDs_URLs(target_dir, sadu=True)


def scan_same_url_with_different_authorIDs(target_dir):
    """
    Scans for cases where an URL gets assigned to different author_id's.

    Args:
        target_dir: path to folder, in which all csv files containing profile URLs are located
    """
    _scan_invalid_mapping_between_AIDs_URLs(target_dir, sadu=False)


def run():
    """
        Main function executing the module
    """
    logging.basicConfig(level=logging.INFO)

    if PARAM.RUN_OPTION == 'filter':
        filter_duplicate_urls()
    else:
        scan_same_authorID_with_different_urls(target_dir=PARAM.SCAN_DIR)
        scan_same_url_with_different_authorIDs(target_dir=PARAM.SCAN_DIR)


if __name__ == '__main__':
    run()
