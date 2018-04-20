from __future__ import unicode_literals
import re
from six import string_types
from jinja2 import evalcontextfilter, Markup, escape

from .formats import dateformat, datetimeformat, shortdateformat, datetodatetimeformat


def smartjoin(input):
    list_to_join = list(input)
    if len(list_to_join) > 1:
        return '{} and {}'.format(', '.join(list_to_join[:-1]), list_to_join[-1])
    elif len(list_to_join) == 1:
        return '{}'.format(list_to_join[0])
    else:
        return ''


def format_links(text):
    """
    Filter that searches a given string (or other string-like object) for any URIs
    and wraps them with either an anchor link or a span, depending on whether the link contains a valid protocol.
    Python3's re library returns matches with type string rather than the arg's type, which
    causes problems for Markup() objects containing tags to be escaped later. Therefore
    we need to cast the matches and formatted links back to the original type before returning the value.
    """
    url_match = re.compile(r"""(
                                (?:https?://|www\.)    # start with http:// or www.
                                (?:[^\s<>"'/?#]+)      # domain doesn't have these characters
                                (?:[^\s<>"']+)         # post-domain part of URL doesn't have these characters
                                [^\s<>,"'\.]           # no dot at end
                                )""", re.X)
    matched_urls = [type(text)(substr) for substr in url_match.findall(text)]
    if matched_urls:
        link = '<a href="{0}" class="break-link" rel="external">{0}</a>'
        plaintext_link = '<span class="break-link">{0}</span>'
        text_array = [type(text)(substr) for substr in url_match.split(text)]
        formatted_text_array = []
        for partial_text in text_array:
            if partial_text in matched_urls:
                if partial_text.startswith('www'):
                    url = plaintext_link.format(Markup.escape(partial_text))
                else:
                    url = link.format(Markup.escape(partial_text))
                formatted_text_array.append(url)
            else:
                partial_text = Markup.escape(partial_text)
                formatted_text_array.append(partial_text)
        formatted_text = Markup(''.join(formatted_text_array))
        return formatted_text
    else:
        return text


def nbsp(text):
    """Replace spaces with nbsp.

    If you want to use html with this filter you need to pass it in as marksafe
    ie.
    {{ "some text and <html>"|marksafe|nbsp }}"""
    text = escape(text)
    return text.replace(' ', Markup('&nbsp;'))


def capitalize_first(maybe_text):
    """If it's a string capitalise the first character, unless it looks like a URL

    :param maybe_text: Could be anything
    :return: If maybe_text is a string it will be returned with an initial capital letter, otherwise unchanged
    """
    if maybe_text and isinstance(maybe_text, string_types):
        if not maybe_text.startswith('http'):
            return maybe_text[0].capitalize() + maybe_text[1:]
    elif isinstance(maybe_text, (list, tuple)):
        return [capitalize_first(item) for item in maybe_text]

    return maybe_text

# find repeated sequences of '\r\n\', optionally separated by other non-newline whitespace space characters
_multiple_newlines_re = re.compile(r'(\r\n[ \t\f\v]*){2,}')
# find \r\n sequences
_single_newline_re = re.compile(r'(\r\n)')


@evalcontextfilter
def preserve_line_breaks(eval_ctx, value):

    # `escape()` returns Markdown objects in python2
    # We want to cast the output value back into unicode strings
    value = u'{}'.format(escape(value))

    # limit sequences of "\r\n\r\n ..."s to two
    value = _multiple_newlines_re.sub(u'\r\n\r\n', value)

    result = _single_newline_re.sub(u'<br>', value)

    if eval_ctx.autoescape:
        result = Markup(result)

    return result


CUSTOM_FILTERS = {
    'format_links': format_links,
    'nbsp': nbsp,
    'smartjoin': smartjoin,
    'dateformat': dateformat,
    'datetimeformat': datetimeformat,
    'shortdateformat': shortdateformat,
    'datetodatetimeformat': datetodatetimeformat
}
