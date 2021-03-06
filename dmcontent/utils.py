import collections

from jinja2 import Markup, StrictUndefined, TemplateSyntaxError, UndefinedError
from jinja2.sandbox import SandboxedEnvironment
from markdown import markdown
from six import string_types

from .errors import ContentNotFoundError, ContentTemplateError
from .filters import CUSTOM_FILTERS


class TemplateField(object):
    def __init__(self, field_value, markdown=None):
        self.source = field_value

        if markdown is None:
            self.markdown = '\n' in field_value
        else:
            self.markdown = markdown

        try:
            self.template = self.make_template(field_value)
        except TemplateSyntaxError as e:
            raise ContentTemplateError(e.message)

    def make_template(self, field_value):
        env = DMSandboxedEnvironment(autoescape=True, undefined=StrictUndefined)
        template = markdown(field_value, []) if self.markdown else field_value

        return env.from_string(template)

    def render(self, context=None):
        try:
            return Markup(self.template.render(context or {}))
        except UndefinedError as e:
            raise ContentTemplateError(e.message)

    def __eq__(self, other):
        if not isinstance(other, TemplateField):
            return False
        return (self.source == other.source)

    def __repr__(self):
        return '<{}: "{}">'.format(
            self.__class__.__name__,
            self.source.encode('utf-8')
        )


class DMSandboxedEnvironment(SandboxedEnvironment):
    """DigitalMarketplace environment with filters."""

    def __init__(self, *args, **kwargs):
        super(DMSandboxedEnvironment, self).__init__(*args, **kwargs)
        self.filters.update(CUSTOM_FILTERS)


def template_all(item):
    if isinstance(item, string_types):
        return TemplateField(item)
    elif isinstance(item, collections.Sequence):
        return [template_all(i) for i in item]
    elif isinstance(item, collections.Mapping):
        result = {}
        for (key, val) in item.items():
            result[key] = template_all(val)
        return result
    else:
        return item


def drop_followups(question_or_section, data, nested=False):
    """Remove any follow up answer if the lead-in question value doesn't require a follow up.

    For nested questions (eg questions insidea a dynamic list array) we remove the question field
    completely, since the top-level data key will be replaced anyway.

    For multiquestions that are serialized to separate top-level keys we set the follow-up value
    to `None`, so that it's replaced if the question was previously answered with a follow-up.

    """

    data = data.copy()

    for question in question_or_section.questions:
        for followup_id, values in question.get('followup', {}).items():
            question_data = data.get(question.id)
            if not isinstance(question_data, list):
                question_data = [question_data]

            if not set(question_data) & set(values):
                for field in question_or_section.get_question(followup_id).form_fields:
                    if nested:
                        data.pop(field, None)
                    else:
                        data[field] = None

    return data


def get_option_value(option):
    """
    An option in a Checkboxes or CheckboxTree question is a dict, but we need to treat their
    contents in consistent ways, e.g. when getting the value to be persisted in the API.
    :param option: dict from a Question's list of options
    :return: string value to be persisted
    """
    return option.get('value') or option['label']


def try_load_manifest(content_loader, application, data, question_set, manifest):
    try:
        content_loader.load_manifest(data['slug'], question_set, manifest)

    except ContentNotFoundError:
        application.logger.info(
            "Could not load {}.{} manifest for {}".format(question_set, manifest, data['slug'])
        )
