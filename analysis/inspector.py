import collections
import enum
import logging
from collections import defaultdict

import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from config import ANALYSIS_SUBDIRS as PATH
from config import INSPECTOR_PARAMS as PARAM

from analysis.utils import *
import analysis.company_matcher as matcher

logging.basicConfig(level=logging.INFO)
RESULTS = defaultdict(list)
FAULTIES = dict()
NONE_MATCHED = defaultdict(list)

col_acquiree_name = 'target_full'
col_acquirer_name = 'acquirer_full'
col_acquisition_date = 'Date'

TimeFrame = collections.namedtuple('TimeFrame', ['category', 'employer', 'start', 'end'])


class ResultRowAppender:
    """
    An object of this class represents a row in the final csv resulted from the :JobTransitionInspector.
    Each attribute of a :ResultRowAppender object will be a value corresponding to the respective key of the global dict :RESULTS
    """

    def __init__(self, aid, l---e---_id, acq_date, E, R):
        self.aid = aid
        self.l---e---_id = l---e---_id
        self.acq_date = acq_date
        self.E = E
        self.R = R

        self.cur_employer = None
        self.cur_job_start = None
        self.cur_job_end = None

        self.next_employer = None
        self.next_job_start = None
        self.days_to_next_job = None
        self.months_to_next_job = None

        self.second_next_employer = None
        self.second_next_job_start = None
        self.days_to_second_next_job = None
        self.months_to_second_next_job = None

        self.E_in_profile = None
        self.E_tframe = None

        self.R_in_profile = None
        self.R_tframe = None

        self.E_in_profile_prior_acq = None
        self.E_tframe_prior_acq = None

        self.R_in_profile_prior_acq = None
        self.R_tframe_prior_acq = None

    def add_current_employment(self, employer, start_date, end_date):
        self.cur_employer = employer
        self.cur_job_start = start_date
        self.cur_job_end = end_date

    def add_next_employment(self, employer, start_date, days_to_next_job, months_to_next_job):
        self.next_employer = employer
        self.next_job_start = start_date
        self.days_to_next_job = days_to_next_job
        self.months_to_next_job = months_to_next_job

    def add_second_next_employment(self, employer, start_date, days_to_second_next_job,
                                   months_to_second_next_job):
        self.second_next_employer = employer
        self.second_next_job_start = start_date
        self.days_to_second_next_job = days_to_second_next_job
        self.months_to_second_next_job = months_to_second_next_job

    def add_E_profile(self, E_in_profile, E_tframe):
        self.E_in_profile = E_in_profile
        self.E_tframe = E_tframe

    def add_R_profile(self, R_in_profile, R_tframe):
        self.R_in_profile = R_in_profile
        self.R_tframe = R_tframe

    def add_E_profile_prior_acq(self, E_in_profile_prior_acq, E_tframe_prior_acq):
        self.E_in_profile_prior_acq = E_in_profile_prior_acq
        self.E_tframe_prior_acq = E_tframe_prior_acq

    def add_R_profile_prior_acq(self, R_in_profile_prior_acq, R_tframe_prior_acq):
        self.R_in_profile_prior_acq = R_in_profile_prior_acq
        self.R_tframe_prior_acq = R_tframe_prior_acq

    def append(self):
        """
        Append a row of the final csv file into the global dict :RESULTS
        """
        RESULTS[col_AID].append(self.aid)
        RESULTS['l---e---_id'].append(self.l---e---_id)
        RESULTS['acq_date'].append(get_date_string(self.acq_date))

        RESULTS['cur_employer'].append(self.cur_employer)
        RESULTS['cur_job_start'].append(get_date_string(self.cur_job_start))
        RESULTS['cur_job_end'].append(get_date_string(self.cur_job_end))

        RESULTS['next_employer'].append(self.next_employer)
        RESULTS['next_job_start'].append(get_date_string(self.next_job_start))
        RESULTS[col_days_to_next_job].append(self.days_to_next_job)
        RESULTS[col_months_to_next_job].append(self.months_to_next_job)

        RESULTS['second_next_employer'].append(self.second_next_employer)
        RESULTS['second_next_job_start'].append(get_date_string(self.second_next_job_start))
        RESULTS[col_days_to_second_next_job].append(self.days_to_second_next_job)
        RESULTS[col_months_to_second_next_job].append(self.months_to_second_next_job)

        RESULTS['E'].append(self.E if self.E else '')
        RESULTS['E_in_profile'].append(self.E_in_profile if self.E_in_profile else '')
        RESULTS['E_timeframe'].append(self.E_tframe)
        # results['E_start'].append(get_date_string(E_start))
        # results['E_end'].append(get_date_string(E_end))

        RESULTS['R'].append(self.R if self.R else '')
        RESULTS['R_in_profile'].append(self.R_in_profile if self.R_in_profile else '')
        RESULTS['R_timeframe'].append(self.R_tframe)

        RESULTS['E_in_profile_prior_acq'].append(self.E_in_profile_prior_acq if self.E_in_profile_prior_acq else '')
        RESULTS['E_timeframe_prior_acq'].append(self.E_tframe_prior_acq)

        RESULTS['R_in_profile_prior_acq'].append(self.R_in_profile_prior_acq if self.R_in_profile_prior_acq else '')
        RESULTS['R_timeframe_prior_acq'].append(self.R_tframe_prior_acq)


def read_csv(file):
    return pd.read_csv(file, delimiter=',', header=0)


def get_date_string(date):
    if date is None:
        return ''

    if date.year == datetime.now().year:
        return 'Present'

    # return date.strftime("%d/%m/%Y")
    return date.strftime("%m/%Y")


def mark_none_match(row, df_profile):
    """
    Save an acquisition data row that does not have acquiree and acquirer   into the global dict :NONE_MATCHED, which
    Args:
        row ():
        df_profile ():
    """
    global NONE_MATCHED
    NONE_MATCHED[col_AID].append(row[col_AID])
    NONE_MATCHED[col_URL].append(df_profile.iloc[0][col_URL])
    NONE_MATCHED['E'].append(row[col_acquiree_name])
    NONE_MATCHED['R'].append(row[col_acquirer_name])
    NONE_MATCHED['employers'].append(f'{str_sep}'.join(set(df_profile[col_company_name].unique())).replace(',', ';'))


def _build_E_R_timeframe(category, employer_list, start, end):
    _sep = '' if len(employer_list) <= 1 else ' | '
    E_employers_str = _sep.join(e for e in employer_list)
    return TimeFrame(category, E_employers_str, start, end)


def _substract_months(datetime_, months):
    """
    Doing arithmetic subtraction on a datetime object. Subtract :months from :datetime_
    ====================
    Args:
        datetime_ (datetime): the datetime object whose month will be substracted
        months (int): number of months to subtract

    Returns:
        (datetime): the resulting datetime object with :months subtracted
    """
    return set_day_to_1(datetime_ - timedelta(days=(365 / 12) * months))


def _add_months(datetime_, months):
    """
    Doing arithmetic addition on a datetime object. Add :months to :datetime_
    ====================
    Args:
        datetime_ (datetime): the datetime object whose month will be added
        months (int): number of months to add

    Returns:
        (datetime): the resulting datetime object with :months added
    """
    return set_day_to_1(datetime_ + timedelta(days=(365 / 12) * months))


def _is_overlapping(last_tf_end, cur_tf_start, tolerance_months=0):
    """
    Check whether two timeframes overlap or not
    ====================
    Args:
        last_tf_end (datetime): the end time point of the most recent timeframe
        cur_tf_start (datetime):  the start time point of the current timeframe
        tolerance_months (int): number of overlapping months to consider two timeframes still do not overlap

    Returns:
        True if overlapping
    """
    return last_tf_end <= _substract_months(cur_tf_start, months=tolerance_months)


class JobTransitionInspector:
    """
    Main class for inspecting job transition status
    """

    def __init__(self, csv_file):
        self.acquisitions = read_csv(csv_file)
        data_type = {col_AID: int, col_company_name: str, col_company_url: str, col_location: str}
        self.profiles_df = pd.read_csv(glob.glob(join(PATH.EXTRACTED_DATA, f'{PARAM.TARGET_GROUP}__*.csv'))[-1],
                                       delimiter=',', header=0,
                                       dtype=data_type,
                                       keep_default_na=False)
        matcher.build_acquisition_company_ref_mappings(
            set(self.acquisitions[col_acquiree_name]).union(set(self.acquisitions[col_acquirer_name])))

    @staticmethod
    def _append_timeline(timeline, df, category):
        """
        PRIVATE, STATIC
        Convert pandas.DataFrame tows to TimeFrame namedtuples and append them to the :timeline list
        Args:
            timeline (list(TimeFrame)): the list to which TimeFrame namedtuples being put into
            df (pandas.DataFrame): the DataFrame contains rows of employment information
            category (str): the category information to build TimeFrame namedtuples. Either 'E', 'R' or 'O'
        Returns:
            None. The :timeline list will get appended
        """
        # num_err_periods = 0
        if df is not None:
            for i, row in df.iterrows():
                try:
                    start, end = parse_employment_timeframe(row[col_timeframe])
                    timeline.append(TimeFrame(category, row[col_company_name], start, end))
                except InvalidTimeframeException as ipe:
                    logging.warning(ipe)

    @classmethod
    def _sort_timeframes(cls, e_df=None, r_df=None, o_df=None):
        """
        Put all timeframes of every category into a list and sort them by their start date
        Args:
            e_df (pandas.DataFrame): The DataFrame containing (L---e---) employment rows at the acquiree
            r_df (pandas.DataFrame): The DataFrame containing (L---e---) employment rows at the acquirer
            o_df (pandas.DataFrame): The DataFrame containing (L---e---) employment rows at other companies

        Returns:
            (list(TimeFrame)): the list of TimeFrame namedtuples sorted by start date
        """
        timeline = list()
        cls._append_timeline(timeline, e_df, 'E')
        cls._append_timeline(timeline, r_df, 'R')
        cls._append_timeline(timeline, o_df, 'O')
        return sorted(timeline, key=lambda x: x.start)

    @staticmethod
    def _match_profile_with_E_R(profile_df, acquiree, acquirer):
        """
        Find the employers that matche :acquiree and :acquirer among all employers in a L---e--- profile
        ====================
        Args:
            profile_df (pandas.Dataframe): the dataframe containing all employments, and thus employers of a L---e--- profile
            acquiree (str): name of an acquiree from acquisition data
            acquirer (str): name of an acquirer from acquisition data

        Returns:
            tuple(pandas.Dataframe, pandas.Dataframe, pandas.Dataframe): df of employers matching acquiree, acquirer and not matching (others), respectively
        """
        profile_df.sort_values(by=col_company_name, ignore_index=True, inplace=True)
        rows_matching_E = list()
        rows_matching_R = list()
        rows_others = list()

        for j, profile_row in profile_df.iterrows():
            employer = profile_row[col_company_name]
            if employer != '':
                if matcher.match(employer=employer, other=acquiree):
                    rows_matching_E.append(profile_row)
                elif matcher.match(employer=employer, other=acquirer):
                    rows_matching_R.append(profile_row)
                else:
                    rows_others.append(profile_row)
            else:
                FAULTIES[profile_row[col_AID]] = f'An empty employer found in profile {profile_row[col_URL]}'

        df_E_matches = pd.DataFrame(rows_matching_E, columns=profile_df.columns)
        df_R_matches = pd.DataFrame(rows_matching_R, columns=profile_df.columns)
        df_others = pd.DataFrame(rows_others, columns=profile_df.columns)
        return df_E_matches, df_R_matches, df_others

    @staticmethod
    def get_future_job_status(future_tframe, acq_date):
        """
        Get the job transition information when a person switched from a current job to another in the future.
        The information includes: name of future employer, start date, number of days and months from the end of current
        job to the start of the future job
        Args:
            future_tframe (TimeFrame): the TimeFrame of the future job
            acq_date (datetime): the acquisiton date

        Returns:
            (dict): dictionary with four key-value pairs for employer name, start date, day delta, month delta
        """
        future_job = dict()
        if future_tframe:
            future_job['employer'] = future_tframe.employer if future_tframe.category == 'O' else future_tframe.category
            future_job['start'] = future_tframe.start
            future_job['day_delta'] = (future_job['start'] - acq_date).days
            delta = relativedelta(future_job['start'], acq_date)
            future_job['month_delta'] = delta.years * 12 + delta.months
        return future_job

    @staticmethod
    def _get_current_job_status(acq_tframes):
        """
        Get the employer name, start and end dates of the employment at the time the acquisition taking place
        ====================
        Args:
            acq_tframes (list(TimeFrame)): the timeframe at which the acquisition occurring

        Returns:
            (dict): dictionary with three key-value pairs for employer name, start date, end date
        """
        cur_job = dict()
        if acq_tframes:
            cur_job['employer'] = f'{str_sep}'.join(
                {tframe.employer if tframe.category == 'O' else tframe.category for tframe in
                 acq_tframes}).replace(',', '')
            cur_job['start'] = [tf.start for tf in acq_tframes][0]
            cur_job['end'] = sorted([tf.end for tf in acq_tframes])[-1]
        return cur_job

    @staticmethod
    def _update_accumulated_timeframe(category, accumulated_tf, timeline, t, E_R_tframes):
        """
        HELPER FUNCTION
        """
        if accumulated_tf['start'] is None:
            accumulated_tf['start'] = timeline[t].start
            accumulated_tf['end'] = timeline[t].end
        elif t >= 1:
            if timeline[t - 1].category == category:
                accumulated_tf['end'] = timeline[t].end
            elif timeline[t - 1].category != category and accumulated_tf['start'] is not None:
                E_R_tframes.append(_build_E_R_timeframe(category, accumulated_tf['employers'], accumulated_tf['start'],
                                                        accumulated_tf['end']))
                accumulated_tf['employers'], accumulated_tf['start'], accumulated_tf['end'] = {timeline[t].employer}, \
                                                                                              timeline[t].start, \
                                                                                              timeline[t].end
        accumulated_tf['employers'].add(timeline[t].employer)
        return accumulated_tf, E_R_tframes

    @staticmethod
    def _finalize_timeframe_series(category, accum_tf, E_R_tframes):
        """
        HELPER FUNCTION
        """
        if accum_tf['start'] is not None:
            E_R_tframes.append(
                _build_E_R_timeframe(category, accum_tf['employers'], accum_tf['start'], accum_tf['end']))
        accum_tf = {'start': None, 'end': None, 'employers': set()}
        return accum_tf, E_R_tframes

    @staticmethod
    def _merge_timeframes(tl):
        _tl = sorted([tf for tf in tl], key=lambda x: x.start)
        merged_tl = list()
        merges = {'E': list(), 'R': list(), 'O': list()}
        other_firm_names = set()
        for t, tframe in enumerate(_tl):
            cat = tframe.category
            if not merges[cat] or _is_overlapping(last_tf_end=merges[cat][-1][3], cur_tf_start=tframe.start,
                                                  tolerance_months=3):
                merges[cat].append([cat, {tframe.employer}, tframe.start, tframe.end])
            else:
                merges[cat][-1][3] = tframe.end
                if tframe.category == 'O':
                    merges[cat][-1][1].add(tframe.employer)

        for ER_merge_list in merges.values():
            for tf in ER_merge_list:
                merged_tl.append(TimeFrame(tf[0], ' | '.join(tf[1]), tf[2], tf[3]))

        merged_tl = sorted([tf for tf in merged_tl], key=lambda x: x.start)
        return merged_tl

    def exec(self):
        """
        The main function, which incorporate acquisition data with data from L---e--- profiles to inspect job transition status
        ====================
        Returns:
            None. The goal is to fill up the three global dictionaries :RESULTS, :NONE_MATCHED and :FAULTIES and store the three respective csv files locally
        """
        # presentation = {'sorted': dict(), 'merged': dict(), 'acq_date': list()}
        # presentative_is = {745, 1330, 1357, 2935, 3355, 3514}

        for i, row in self.acquisitions.iterrows():
            # if i < 3510:  # for DEBUG
            #     continue

            # if i not in presentative_is:
            #     continue

            aid = row[col_AID]
            l---e---_id = None
            acquiree = row[col_acquiree_name]
            acquirer = row[col_acquirer_name]

            logging.info(f'MATCHING:{i}.ACQUIREE={acquiree}, ACQUIRER={acquirer}')
            E_df, R_df, others_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

            profile_df = self.profiles_df[self.profiles_df[col_AID] == aid]
            if len(profile_df.index) > 0:
                l---e---_id = profile_df.iloc[0][col_URL].partition("/in/")[2]
                E_df, R_df, others_df = self._match_profile_with_E_R(profile_df, acquiree, acquirer)
            else:
                logging.warning(
                    f'PROFILE NOT FOUND:Employee (AID={aid}, Acquiree={acquiree}, Acquirer={acquirer}) '
                    f'are not included in the extracted profiles --> SKIP')
                FAULTIES[aid] = 'author_id not found'
                continue

            has_E_matched = len(E_df.index) > 0
            has_R_matched = len(R_df.index) > 0

            if not has_E_matched and not has_R_matched:
                mark_none_match(row, profile_df)
                continue

            acq_date = parse_acquisition_date(row[col_acquisition_date])
            timeline = self._sort_timeframes(e_df=E_df, r_df=R_df, o_df=others_df)
            # presentation['sorted'][aid] = timeline
            timeline = self._merge_timeframes(timeline)
            # presentation['merged'][aid] = timeline
            # presentation['acq_date'].append(acq_date)
            #######################################################################################################
            acq_tframes = list()
            next_tframe = None
            second_next_tframe = None
            for f, tframe in enumerate(timeline):
                if next_tframe is not None:
                    break

                is_acq_tframe = tframe.start <= acq_date <= tframe.end and not acq_tframes
                mergeable = acq_tframes and tframe.category == acq_tframes[-1].category and acq_date <= tframe.start
                if tframe.start < acq_date <= tframe.end:
                    acq_tframes.append(tframe)
                # elif acq_date <= tframe.start and acq_tframes and acq_tframes[-1].end <= tframe.start:
                elif acq_date <= tframe.start and acq_tframes:
                    if tframe.category == acq_tframes[-1].category:
                        acq_tframes.append(tframe)
                        continue

                    next_tframe = tframe

                    s = f + 1
                    while s < len(timeline):
                        if next_tframe.end < timeline[s].start:
                            second_next_tframe = timeline[s]
                            break
                        s += 1

            cur_job = self._get_current_job_status(acq_tframes)
            next_job = self.get_future_job_status(next_tframe, acq_date)
            second_next_job = self.get_future_job_status(second_next_tframe, acq_date)

            #######################################################################################################
            tl = sorted([p for p in timeline if p.employer in {'E', 'R'}], key=lambda x: x.start)
            timeline = sorted([p for p in timeline], key=lambda x: x.start)
            E_accum_tf = {'start': None, 'end': None, 'employers': set()}
            R_accum_tf = {'start': None, 'end': None, 'employers': set()}

            E_tframes_prior_acq, R_tframes_prior_acq = list(), list()
            E_tframes, R_tframes = list(), list()
            for t, tframe in enumerate(timeline):
                if tframe.end < acq_date:
                    if tframe.category == 'E':
                        E_accum_tf, E_tframes_prior_acq = self._update_accumulated_timeframe('E', E_accum_tf, timeline,
                                                                                             t, E_tframes_prior_acq)
                    elif tframe.category == 'R':
                        R_accum_tf, R_tframes_prior_acq = self._update_accumulated_timeframe('R', R_accum_tf, timeline,
                                                                                             t, R_tframes_prior_acq)

                    if t + 1 < len(timeline) and acq_date <= timeline[t + 1].end:
                        E_accum_tf, E_tframes_prior_acq = self._finalize_timeframe_series('E', E_accum_tf,
                                                                                          E_tframes_prior_acq)
                        R_accum_tf, R_tframes_prior_acq = self._finalize_timeframe_series('R', R_accum_tf,
                                                                                          R_tframes_prior_acq)

                elif acq_date <= tframe.end:
                    if tframe.category == 'E':
                        E_accum_tf, E_tframes = self._update_accumulated_timeframe('E', E_accum_tf, timeline, t,
                                                                                   E_tframes)
                    elif tframe.category == 'R':
                        R_accum_tf, R_tframes = self._update_accumulated_timeframe('R', R_accum_tf, timeline, t,
                                                                                   R_tframes)

            E_accum_tf, E_tframes = self._finalize_timeframe_series('E', E_accum_tf, E_tframes)
            R_accum_tf, R_tframes = self._finalize_timeframe_series('R', R_accum_tf, R_tframes)

            E_in_profile, E_tframes_str = get_timeframes_info_as_strings(E_tframes)
            R_in_profile, R_tframes_str = get_timeframes_info_as_strings(R_tframes)
            E_in_profile_prior_acq, E_tframes_prior_acq_str = get_timeframes_info_as_strings(E_tframes_prior_acq)
            R_in_profile_prior_acq, R_tframes_prior_acq_str = get_timeframes_info_as_strings(R_tframes_prior_acq)

            rrb = ResultRowAppender(aid, l---e---_id, acq_date, E=acquiree, R=acquirer)
            rrb.add_current_employment(employer=cur_job.get('employer'), start_date=cur_job.get('start'),
                                       end_date=cur_job.get('end'))
            rrb.add_next_employment(employer=next_job.get('employer'), start_date=next_job.get('start'),
                                    days_to_next_job=next_job.get('day_delta'),
                                    months_to_next_job=next_job.get('month_delta'))
            rrb.add_second_next_employment(employer=second_next_job.get('employer'),
                                           start_date=second_next_job.get('start'),
                                           days_to_second_next_job=second_next_job.get('day_delta'),
                                           months_to_second_next_job=second_next_job.get('month_delta'))
            rrb.add_E_profile(E_in_profile=E_in_profile, E_tframe=E_tframes_str)
            rrb.add_R_profile(R_in_profile=R_in_profile, R_tframe=R_tframes_str)

            rrb.add_E_profile_prior_acq(E_in_profile_prior_acq=E_in_profile_prior_acq,
                                        E_tframe_prior_acq=E_tframes_prior_acq_str)
            rrb.add_R_profile_prior_acq(R_in_profile_prior_acq=R_in_profile_prior_acq,
                                        R_tframe_prior_acq=R_tframes_prior_acq_str)
            rrb.append()

        pd.DataFrame.from_dict(RESULTS).to_csv(
            join(PARAM.FINAL_DATA_DIR, f'{PARAM.TARGET_GROUP}__employment_continuity_by_acquisition_{get_now()}.csv'),
            index=False)
        pd.DataFrame.from_dict(NONE_MATCHED).to_csv(
            join(PARAM.NONE_MATCHED_DIR, f'{PARAM.TARGET_GROUP}__none_matched_{get_now()}.csv'), index=False)
        pd.DataFrame([{
            col_AID: aid,
            'cause': cause
        } for aid, cause in FAULTIES.items()], columns=[col_AID, 'cause']).to_csv(
            join(PARAM.FAULTY_EMPLOYEES_DIR, f'{PARAM.TARGET_GROUP}__faulty_employees_{get_now()}.csv'), index=False)

        logging.info('SUCCESS: Analyzing Job Transition Patterns done!')

        # import pickle
        # pickle.dump(presentation, open("merges_2.pkl", "wb"))


def get_timeframes_info_as_strings(tframes):
    """
    Converts a list of TimeFrames to two lists of strings, one is the concatenated employer names and the other is
    the concatenated start-end dates as strings
    Args:
        tframes (list<TimeFrame>): list of TimeFrame to be represented as strings

    Returns:
        (tuple<str,str>): the two list of strings for employer names and employment periods
    """
    employers_str = ' | '.join(ef.employer for ef in tframes)
    timeframes_str = ' | '.join(f'{get_date_string(ef.start)} - {get_date_string(ef.end)}' for ef in tframes)
    return employers_str, timeframes_str


def run():
    """
        Main function executing the module
    """
    print("\n************************************** PARAMERTERS **************************************\n")
    print(f'TARGET_GROUP: {PARAM.TARGET_GROUP}\n')
    print(f'ACQ_FILE: {PARAM.ACQ_FILE}\n')
    print(f'FINAL_DATA_DIR: {PARAM.FINAL_DATA_DIR}\n')
    print(f'FAULTY_EMPLOYEES_DIR: {PARAM.FAULTY_EMPLOYEES_DIR}\n')
    print(f'NONE_MATCHED_DIR: {PARAM.NONE_MATCHED_DIR}\n')
    print('*****************************************************************************************\n')

    jti = JobTransitionInspector(PARAM.ACQ_FILE)
    jti.exec()


if __name__ == '__main__':
    run()
