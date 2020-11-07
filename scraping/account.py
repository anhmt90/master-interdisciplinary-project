"""
    Class representing accounts to log in L---e--- for scraping profile
"""

import names
import logging as log

from scraping.utils import *
from os.path import join
from config import ACCOUNT_PARAMS as PARAM


def create_file(accounts, dir_):
    """
    Stores/Records/Persists/Creates a list of accounts into a new CSV file on local storage
    Args:
        accounts (list<Account>): List of account to store
        dir_ (str): Path to folder in which the CSV file containing new account data should be persisted

    """
    file_path = join(PARAM.ACC_SAVE_DIR, f'accounts_{get_now()}.csv')
    df = pd.DataFrame([{
        'email': acc.get_email(),
        'password': acc.get_password(),
        'blocked': acc.get_blocked()
    } for acc in accounts], columns=['email', 'password', 'blocked'])

    _persist(df, file_path)


def update_file(accounts, file_path):
    """
    Updates an existing CSV file of account data by a list of accounts
    Args:
        accounts (list<Account>): List of account used for updating the CSV file of account
        file_path (str): Path to the CSV file containing existing account data

    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f'FILE NOT FOUND: File {file_path} not found')
    df_current_accounts = pd.read_csv(file_path, delimiter=',', header=0)
    block_status = {acc.get_email(): acc.get_blocked for acc in accounts}
    block_status_keys = block_status.keys()
    for i, row in df_current_accounts.iterrows():
        # if block_status.get(row.email) is not None:
        if row.email in block_status_keys:
            row.blocked = block_status[row.email]

    _persist(df_current_accounts, file_path)


def _persist(df, file_path):
    """
    Stores a pandas.DataFrame into a CSV file on local storage
    Args:
        df (pandas.DataFrame): The pandas.DataFrame to store
        file_path (str): Path to the CSV file storing the account data
    """
    with open(file_path, 'w', newline='') as file:
        df.to_csv(file, header=file.tell() == 0, index=False)


def read_accounts(csv_file):
    """
    Reads account data strored in a CSV file and makes a list of scraping accounts from that
    Args:
        csv_file (str): Path to the CSV file storing the account data

    Returns:
        (list<Account>): list of Account's that will be used to log in L---e--- and scrape profiles
    """
    df = pd.read_csv(csv_file, delimiter=',', header=0)
    accounts = [Account.make_from(acc_data) for _, acc_data in df.iterrows() if not acc_data['blocked']]
    if not accounts:
        log.warning("FAILED: No active accounts found")
    return accounts


class Account:
    """
    Class that represents scraping accounts that are used to log in L---e--- and scrape profiles.
    Important information is `email` (used as username for logging in L---e---), `password` and `blocked` status indicating
    whether that Account has been blocked by L---e--- or not.
    """

    def __init__(self):
        self._email = ""
        self._password = ""
        self._first_name = ""
        self._last_name = ""
        self._yob = -1
        self._blocked = False
        self._scraped_count = 0
        self._logged_in = False

    @classmethod
    def make_from(cls, acc_data):
        """
        Generates an Account object from existing (persisted) data. This function is used to make Account objects from
        data stored in a CSV file.
        Args:
            acc_data (dict[str -> str/bool]): A dict containing the necessary data to create an Account object from

        Returns:
            (Account): The created Account object
        """
        assert acc_data['email'], "Account data has no email"
        assert acc_data['password'], "Account data has no password"
        if acc_data['blocked']:
            return

        acc = Account()
        acc._email = acc_data['email']
        acc._password = acc_data['password']
        acc._blocked = acc_data['blocked']

        name_parts = acc._email.partition('@')[0].split('.')
        acc._first_name = name_parts[0].capitalize()
        acc._last_name = name_parts[1].capitalize()
        if len(name_parts) == 3:
            acc._yob = int(name_parts[2])
        else:
            acc._gen_year_of_birth()

        return acc

    @classmethod
    def make_new(cls, domain, secured_pwd=False):
        """
        Generates a new Account object with a given email domain
        Args:
            domain (str): The email domain that the Account object being created should have in its email
            secured_pwd (bool): If True, a secured password for the Account object will be used following a predefined pattern.
                                If False, a simpler password pattern will be used for creating a new password

        Returns:
            (Account): The created Account object
        """
        acc = Account()
        acc._gen_full_name()
        acc._gen_year_of_birth()
        acc._gen_email(domain)
        acc._password = acc._gen_secured_password('CvCNNsNNsNNsvCvnn') if secured_pwd else acc._gen_password()
        print(f"SUCCESS: Created: {acc}")
        return acc

    def _gen_year_of_birth(self, start=1985, end=1999):
        """
        Generates for an Account a random year of birth in a given range of year
        Args:
            start (int): the lower bound of the range for year of birth
            end (int): the upper bound of the range for year of birth
        """
        self._yob = random.randint(start, end)

    def _gen_full_name(self, gender='female'):
        """
        Generates an full name (both first and last names) that looks realistic
        Args:
            gender (str): The name gender, either `male` or `female`
        """
        first_name, last_name = "", ""
        while True:
            self._first_name = names.get_first_name(gender)
            if len(first_name) <= 6:
                break
        while True:
            self._last_name = names.get_last_name()
            if len(last_name) <= 6:
                break

    def _gen_password(self):
        """
        Generates a simple password following the patter <first name><year of birth><last name>
        Returns:
            (str): The generated password  
        """
        return f'{self._first_name}{self._yob}{self._last_name}'

    @classmethod
    def _gen_secured_password(cls, pattern):
        """
        Generates a secured password following a pattern
        Args:
            pattern (str): The character pattern that the generated password should follow 

        Returns:
            (str): The secured password generated following the provided pattern
        """
        consonants = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X',
                      'Z']
        vowels = ['A', 'E', 'I', 'O', 'U', 'Y']
        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        symbols = ['(', ')', '?', '!', '#', '$', '%', '^', '&', '*']

        password = ""
        for char in pattern:
            if char == 'c':
                char = random.choice(consonants).lower()
            elif char == 'C':
                char = random.choice(consonants)
            elif char == 'v':
                char = random.choice(vowels).lower()
            elif char == 'V':
                char = random.choice(vowels)
            elif char == 'n' or char == 'N':
                char = random.choice(numbers)
            elif char == 's' or char == 'S':
                char = random.choice(symbols)

            password = f"{password}{char}"

        assert password
        return password

    def _gen_email(self, domain):
        username = f"{self._first_name.lower()}.{self._last_name.lower()}.{self._yob - 1900}"
        self._email = f"{username}@{domain}"

    def get_email(self):
        return self._email

    def get_password(self):
        return self._password

    def get_blocked(self):
        return self._blocked

    def get_first_name(self):
        return self._first_name

    def get_last_name(self):
        return self._last_name

    def get_scraped_count(self):
        return self._scraped_count

    def increase_scraped_count(self, by):
        self._scraped_count += by

    def get_logged_in(self):
        return self._logged_in

    def set_logged_in(self, logged_in):
        self._logged_in = logged_in

    def set_blocked(self, blocked):
        self._blocked = blocked

    def __str__(self):
        return f"{self._email, self._password, self._blocked, self._logged_in}"


def generate_account_file():
    _domains = ['protonmail.com', 'web.de', 'gmx.de', 'juno.com', 'posteo.de',
                'tutanota.de', 'kolabnow.com', 'mailfence.com', 'mailbox.org']

    _accounts = list()
    for i in range(PARAM.COUNT):
        _accounts.append(Account.make_new(_domains[i % len(_domains)]))

    if _accounts:
        create_file(_accounts, dir_=PARAM.ACC_SAVE_DIR)


if __name__ == '__main__':
    print("\n************************************** PARAMERTERS **************************************\n")
    print(f'COUNT: {PARAM.COUNT}\n')
    print(f'ACC_SAVE_DIR: {PARAM.ACC_SAVE_DIR}\n')
    print('*****************************************************************************************\n')

    generate_account_file()
