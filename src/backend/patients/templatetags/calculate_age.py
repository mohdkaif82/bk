import datetime

import pandas as pd
from django import template
from num2words import num2words

register = template.Library()


@register.filter
def age(bday, d=None):
    bday = datetime.datetime.strptime(bday, "%Y-%m-%d").date()
    if d is None:
        d = datetime.date.today()
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))


@register.filter
def split(str, splitter):
    return str.split(splitter) if str else []


@register.filter
def mul(one, two):
    if one and two:
        return float(one) * float(two)
    else:
        return 0.0


@register.filter
def mul_float(one, two):
    if one and two:
        return float(float(one) * float(two))
    else:
        return 0.0


@register.filter
def to_date(date_str, two=None):
    return pd.to_datetime(date_str)


@register.filter
def div(one, two):
    return one / two if two != 0 else 0


@register.filter
def sub(one, two):
    if one and two:
        return float(one) - float(two)
    else:
        return 0.0


@register.filter
def roundoff(one, two):
    if one and two is not None:
        return round(one, two)
    else:
        return 0.0


@register.filter
def add(one, two):
    if one and two:
        return one + two
    elif one:
        return one
    elif two:
        return two
    else:
        return 0.0


@register.filter
def percent_discount(one, two):
    return one - (one * two / 100) if two != 0 else one


@register.filter
def num_to_word(num):
    num_list = str(float(num)).split(".") if num else [0, 0]
    half = " and half" if num_list[1] == "5" else ""
    return num2words(num_list[0]) + half if num_list[0] != "0" else "half"


@register.filter
def pay_count(payments, data_id):
    return len([item["pay_id"] for item in payments if item["pay_id"] < data_id])
