# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from datetime import datetime
import pytz

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_SHORT_DATE_FORMAT = '%-d %B'
DISPLAY_DATE_FORMAT = '%A %-d %B %Y'
DISPLAY_TIME_FORMAT = '%H:%M:%S'
DISPLAY_DATETIME_FORMAT = '%A %-d %B %Y at %I:%M%p'


def timeformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_TIME_FORMAT)


def shortdateformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_SHORT_DATE_FORMAT, localize=False)


def dateformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_DATE_FORMAT, localize=False)


def datetimeformat(value, default_value=None, localize=True):
    # en_GB locale uses uppercase AM/PM which contravenes our style guide
    formatted_date = _format_date(value, default_value, DISPLAY_DATETIME_FORMAT, localize=localize)
    if formatted_date:
        return formatted_date.replace('AM', 'am').replace('PM', 'pm').replace(" 0", " ")
    return formatted_date


def utcdatetimeformat(value, default_value=None):
    """
    Use this filter to format deadline timestamps that are stored in the database as
    23:59:59 (UTC+00), when the localisation would otherwise display the date as 12.59am
     on the next day (due to daylight savings), potentially causing confusion for buyers/suppliers.
    """
    local_format = datetimeformat(value, default_value)
    if local_format:
        if "11:59pm" not in local_format:
            # Force UTC+00 if the date has rolled over to the next day and append timezone
            return "{} GMT".format(datetimeformat(value, default_value, localize=False))
        return "{} GMT".format(local_format)
    return None


def datetodatetimeformat(value):
    try:
        date = datetime.strptime(value, DATE_FORMAT)
        return dateformat(date)
    except ValueError:
        return value


EUROPE_LONDON = pytz.timezone("Europe/London")


def _format_date(value, default_value, fmt, localize=True):
    if not value:
        return default_value
    if not isinstance(value, datetime):
        value = datetime.strptime(value, DATETIME_FORMAT)
    if value.tzinfo is None:
        value = pytz.utc.localize(value)
    if localize:
        return value.astimezone(EUROPE_LONDON).strftime(fmt)
    else:
        return value.strftime(fmt)


def format_price(min_price, max_price, unit, interval, hours_for_price=None):
    """Format a price string"""
    if hours_for_price:
        return u'{} for £{}'.format(hours_for_price, min_price)

    if min_price is None:
        raise TypeError('min_price should be string or integer, not None')
    formatted_price = u'£{}'.format(min_price)
    if max_price:
        formatted_price += u' to £{}'.format(max_price)
    if unit:
        formatted_price += ' per ' + unit.lower()
    if interval:
        formatted_price += ' per ' + interval.lower()
    return formatted_price


def format_service_price(service):
    """Format a price string from a service dictionary

    :param service: a service dictionary, returned from data API

    :return: a formatted price string if the required
             fields are set in the service dictionary.
    """
    if not service.get('priceMin'):
        return ''
    return format_price(
        service.get('priceMin'),
        service.get('priceMax'),
        service.get('priceUnit'),
        service.get('priceInterval'))
