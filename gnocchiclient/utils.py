# -*- encoding: utf-8 -*-
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import uuid

import pyparsing as pp
import six
from six.moves.urllib import parse as urllib_parse

uninary_operators = ("not", )
binary_operator = (u">=", u"<=", u"!=", u">", u"<", u"=", u"==", u"eq", u"ne",
                   u"lt", u"gt", u"ge", u"le", u"in", u"like", u"≠", u"≥",
                   u"≤", u"like" "in")
multiple_operators = (u"and", u"or", u"∧", u"∨")

operator = pp.Regex(u"|".join(binary_operator))
null = pp.Regex("None|none|null").setParseAction(pp.replaceWith(None))
boolean = "False|True|false|true"
boolean = pp.Regex(boolean).setParseAction(lambda t: t[0].lower() == "true")
hex_string = lambda n: pp.Word(pp.hexnums, exact=n)
uuid_string = pp.Combine(hex_string(8) +
                         (pp.Optional("-") + hex_string(4)) * 3 +
                         pp.Optional("-") + hex_string(12))
number = r"[+-]?\d+(:?\.\d*)?(:?[eE][+-]?\d+)?"
number = pp.Regex(number).setParseAction(lambda t: float(t[0]))
identifier = pp.Word(pp.alphas, pp.alphanums + "_")
quoted_string = pp.QuotedString('"') | pp.QuotedString("'")
comparison_term = pp.Forward()
in_list = pp.Group(pp.Suppress('[') +
                   pp.Optional(pp.delimitedList(comparison_term)) +
                   pp.Suppress(']'))("list")
comparison_term << (null | boolean | uuid_string | identifier | number |
                    quoted_string | in_list)
condition = pp.Group(comparison_term + operator + comparison_term)

expr = pp.operatorPrecedence(condition, [
    ("not", 1, pp.opAssoc.RIGHT, ),
    ("and", 2, pp.opAssoc.LEFT, ),
    ("∧", 2, pp.opAssoc.LEFT, ),
    ("or", 2, pp.opAssoc.LEFT, ),
    ("∨", 2, pp.opAssoc.LEFT, ),
])


def _parsed_query2dict(parsed_query):
    result = None
    while parsed_query:
        part = parsed_query.pop()
        if part in binary_operator:
            result = {part: {parsed_query.pop(): result}}

        elif part in multiple_operators:
            if result.get(part):
                result[part].append(
                    _parsed_query2dict(parsed_query.pop()))
            else:
                result = {part: [result]}

        elif part in uninary_operators:
            result = {part: result}
        elif isinstance(part, pp.ParseResults):
            kind = part.getName()
            if kind == "list":
                res = part.asList()
            else:
                res = _parsed_query2dict(part)
            if result is None:
                result = res
            elif isinstance(result, dict):
                list(result.values())[0].append(res)
        else:
            result = part
    return result


class MalformedQuery(Exception):
    def __init__(self, reason):
        super(MalformedQuery, self).__init__(
            "Malformed Query: %s" % reason)


def search_query_builder(query):
    try:
        parsed_query = expr.parseString(query, parseAll=True)[0]
    except pp.ParseException as e:
        raise MalformedQuery(six.text_type(e))
    return _parsed_query2dict(parsed_query)


def list2cols(cols, objs):
    return cols, [tuple([o[k] for k in cols])
                  for o in objs]


def format_string_list(objs, field):
    objs[field] = ", ".join(objs[field])


def format_dict_list(objs, field):
    objs[field] = "\n".join(
        "- " + ", ".join("%s: %s" % (k, v)
                         for k, v in elem.items())
        for elem in objs[field])


def format_move_dict_to_root(obj, field):
    for attr in obj[field]:
        obj["%s/%s" % (field, attr)] = obj[field][attr]
    del obj[field]


def format_archive_policy(ap):
    format_dict_list(ap, "definition")
    format_string_list(ap, "aggregation_methods")


def format_resource_for_metric(metric):
    # NOTE(sileht): Gnocchi < 2.0
    if 'resource' not in metric:
        return

    if not metric['resource']:
        metric['resource/id'] = None
        del metric['resource']
    else:
        format_move_dict_to_root(metric, "resource")


def dict_from_parsed_args(parsed_args, attrs):
    d = {}
    for attr in attrs:
        value = getattr(parsed_args, attr)
        if value is not None:
            d[attr] = value
    return d


def dict_to_querystring(objs):
    return "&".join(["%s=%s" % (k, urllib_parse.quote(six.text_type(v)))
                     for k, v in objs.items()
                     if v is not None])


# uuid5 namespace for id transformation.
# NOTE(chdent): This UUID must stay the same, forever, across all
# of gnocchi to preserve its value as a URN namespace.
RESOURCE_ID_NAMESPACE = uuid.UUID('0a7a15ff-aa13-4ac2-897c-9bdf30ce175b')


def encode_resource_id(value):
    try:
        try:
            return str(uuid.UUID(value))
        except ValueError:
            if len(value) <= 255:
                if six.PY2:
                    value = value.encode('utf-8')
                return str(uuid.uuid5(RESOURCE_ID_NAMESPACE, value))
            raise ValueError(
                'transformable resource id >255 max allowed characters')
    except Exception as e:
        raise ValueError(e)
