"""
In this file we are following the date conventions like as follows:
    for ex:  Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
             End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
End date need to follow the convention of 23:59:59 as hours, minutes and seconds convention to it.
"""
import calendar
from datetime import timedelta, datetime

from dateutil.parser import parse
from django.utils import timezone


def now_local(only_date=False):
    """
    In this method takes only date is true or false. If true means return the date with time (2016-03-15 13:09:08).
    If false means return the date (2016-03-15)
    :param only_date: true / false
    :return: date with time (2016-03-15 13:09:08) and date (2016-03-15)
    """
    if only_date:
        return (timezone.localtime(timezone.now())).date()
    else:
        return timezone.localtime(timezone.now())


def get_boundaries_for_tomorrow_and_day_after_tomorrow():
    """
    :return: tomorrow date (2016-03-16) and day_after_tomorrow (2016-03-17)
    """
    today = timezone.now_local(only_date=True)
    tomorrow = today + timedelta(days=1)
    day_after_tomorrow = tomorrow + timedelta(days=1)
    return tomorrow, day_after_tomorrow


def localtime(date_obj=datetime.now()):
    """
    :return: return local time ..ie indian standard time
    """
    return timezone.localtime(date_obj)


def get_today_start():
    """
    :return: Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
    """
    return now_local().replace(hour=0, minute=0, second=0, microsecond=0)


def get_today_end():
    """
    :return: End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
    """
    tomorrow = get_today_start() + timedelta(days=1)
    return tomorrow - timedelta(microseconds=1)


def get_day_start(date):
    """
    :return: Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
    """
    import datetime
    date_time = datetime.datetime.combine(date, datetime.time.min)
    return date_time.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(date):
    """
    :return: End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
    """
    import datetime
    date_time = datetime.datetime.combine(date, datetime.time.min)
    return date_time.replace(hour=23, minute=59, second=59, microsecond=0)


def get_yesterday_boundaries():
    """
    :return: Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00 And End Date (YYYY-MM-DD HH:MM:SS): 2016-03-15 23:59:59
    """
    yesterday_start = get_today_start() - timedelta(days=1)
    yesterday_end = get_today_start() - timedelta(microseconds=1)
    return yesterday_start, yesterday_end


def get_current_month_start():
    """
    It will not take any params. It will returns month start date.
    :return: Month Start Date (YYYY-MM-DD HH:MM:SS): 2016-03-1 00:00:00
    """
    return get_today_start().replace(day=1)


def get_prev_month_boundaries():
    """
    Will return the previous month start date (2016-02-1 00:00:00) and previous month end date (2016-02-29 23:59:59).
    :return: (prev_month_start_date, prev_month_end_date)
    """
    prev_month_end_date = get_current_month_start() - timedelta(microseconds=1)
    if prev_month_end_date:
        prev_month_start_date = prev_month_end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return prev_month_start_date, prev_month_end_date


def get_prev_month_till_today():
    """
    Will return the previous month start date (2016-02-1 00:00:00) and the continuing date of current month as previous month end date
    2016-02-15 23:59:59).
    :return: previous month start date and today date of previous month end date
    """

    prev_month_start_date, prev_month_end_date = get_prev_month_boundaries()
    try:
        #  + datetime.timedelta(days=3) need to remove in next month....
        # import datetime
        prev_month_end_till_date = prev_month_end_date.replace(
            day=get_today_start().day)  # + datetime.timedelta(days=3)
    except ValueError:
        prev_month_end_till_date = prev_month_end_date
    return prev_month_start_date, prev_month_end_till_date


def get_next_60_days_date():
    """
    will return next 60 days date starting form today date
    :return next dates due date from today onwards
    """
    return now_local(only_date=True) + timedelta(days=59)


def get_dates(start_date, end_date=None):
    """
    Will take the start and end date and caluculate the dates and return the dates
    :param start_date, end_date
    :return dict(start_date, end_date)
    """
    try:
        startdate = start_date.date()
        enddate = end_date.date() if end_date else end_date
        date_dict = {
            # Date display
            "start_date": startdate,
            "end_date": enddate,
        }
    except AttributeError:
        date_dict = {
            "start_date": start_date,
            "end_date": end_date
        }
    return date_dict


def get_contest_date(start_date=None, end_date=None):
    from datetime import datetime
    from pytz import timezone
    date_str = "2017-10-01 00:00:01"
    datetime_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    datetime_obj_utc = datetime_obj.replace(tzinfo=timezone('Asia/Kolkata'))
    return datetime_obj_utc


def get_date_format_for_reports_string(date_str):
    """
    It will retunr the Propoer Format Of dates from String
    """
    from datetime import datetime
    from pytz import timezone
    datetime_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    datetime_obj_utc = datetime_obj.replace(tzinfo=timezone('Asia/Kolkata'))
    return datetime_obj_utc


def get_next_prev_year_month_start_end_date():
    """
    will return Prev Year Same Month Start and End date
    :return prev year same month start date , end date
    """
    from calendar import monthrange
    from dateutil.relativedelta import relativedelta
    # monthrange(2011, 2) #  (1, 31)  # (weeks, days)
    prev_year_month_start_date = get_current_month_start() - timedelta(microseconds=-1)
    pre_policy_start_date = prev_year_month_start_date - relativedelta(years=1)
    first_day = pre_policy_start_date.replace(hour=0, minute=0, second=0, microsecond=1)
    get_month_days = monthrange(prev_year_month_start_date.year, prev_year_month_start_date.month)
    days_in_month = get_month_days[1]
    last_day = pre_policy_start_date.replace(day=days_in_month, hour=23, minute=59, second=59, microsecond=1)
    return first_day, last_day


def to_str(dt):
    if not dt:
        return dt
    return dt.isoformat()


def from_str(dt_str):
    if not dt_str:
        return dt_str
    return parse(dt_str)


def get_the_last_date_of_month(date):
    """
    It will take date as a input and return the last day of a month in date format
    Basically Month End
    """
    last_day = calendar.monthrange(date.year, date.month)[1]
    return date.replace(day=last_day)


def subtract_years(date=None, years=1):
    """Return a date that's `years` years ago the date (or datetime)
    object `d`. Return the same calendar date (month and day) in the
    destination year, if it exists, otherwise use the current date to calculate a date an year ago.
    """
    import datetime
    if isinstance(date, datetime.date):
        return date.replace(year=date.year - years)
    else:
        current_datetime = now_local()
        return current_datetime.replace(year=current_datetime.year - years)


def get_current_month_no_of_days():
    import datetime
    now = datetime.datetime.now()
    return calendar.monthrange(now.year, now.month)[1]
