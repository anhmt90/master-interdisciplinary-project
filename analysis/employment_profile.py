"""
CLASSES REPRESENTING STRUCTURE OF L---e--- PROFILES
"""


class EmploymentRole:
    """
    On L---e--- profile, an :EmploymentRole is the title of a job position including the time period/time frame,
    and location e.g. Software Architect July 2010 - April 2015, New York
    """
    def __init__(self, title, timeframe='', location=''):
        self.title = title
        self.timeframe = timeframe
        self.location = location

    def __str__(self):
        location_str = f'in {self.location}' if self.location else self.location
        return f'\t\t- {self.title}, {self.timeframe[0]} - {self.timeframe[1]} {location_str}'


class Employment:
    """
    A person can take many roles while working for a company. On L---e--- profile, an :Employment is a subsection that
    includes all employment roles/job positions of a single company. Each :Employment contains at least one :EmploymentRole.
    """
    def __init__(self, company_name='', company_url='', roles=None, duration=''):
        self.company_name = company_name
        self.company_url = company_url
        self.duration = duration
        self.roles = [] if roles is None else roles

    def __str__(self):
        roles_str = "\n" + '\n'.join([str(r) for r in self.roles])
        return f'\tCompany: {self.company_name}\n\tL---e---: {self.company_url}\n\tDuration:{self.duration}\n\tRoles:{roles_str}'


class EmploymentProfile:
    """
    On L---e--- profile, an :EmploymentProfile is a whole 'Experience' section of the profile page.
    Each :EmploymentProfile contains at least one :Employment.
    """
    def __init__(self, employee_name, l---e---='', employments=None):
        self.employee_name = employee_name
        self.l---e--- = l---e---
        self.employments = [] if employments is None else employments

    def __str__(self):
        employments_str = "\n" + "\n".join([f'{e}\n' for e in self.employments])
        return f'Name: {self.employee_name}\nL---e---: {self.l---e---}\nEmployments:{employments_str}'
