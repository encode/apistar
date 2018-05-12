import json

import click


def yaml_errors(value, errors):
    return render(value, errors)


def render(item, errors, indent=0):
    if isinstance(item, list):
        output = render_list(item, errors, indent)
    elif isinstance(item, dict):
        output = render_dict(item, errors, indent)
    else:
        output = json.dumps(item)

    if errors and isinstance(errors, str) and indent == 0:
        output = click.style(errors, fg='red')

    return output


def render_list(item, errors, indent=0):
    output = ''
    indent_str = ' ' * indent
    for idx, value in enumerate(item):
        current_error = errors.get(idx) if isinstance(errors, dict) else None
        if isinstance(value, (list, dict)):
            output += '%s- %s' % (indent_str, render(value, current_error, indent + 2).lstrip())
        else:
            output += '%s- %s\n' % (indent_str, render(value, current_error, indent + 2))

        if current_error and isinstance(current_error, str):
            output += click.style('%s  ^ %s\n' % (indent_str, current_error), fg='red')

    return output


def render_dict(item, errors, indent=0):
    output = ''
    indent_str = ' ' * indent
    for key, value in item.items():
        current_error = errors.get(key) if isinstance(errors, dict) else None
        if isinstance(value, (list, dict)):
            output += '%s%s:\n' % (indent_str, key)
        else:
            output += '%s%s: %s\n' % (indent_str, key, render(value, current_error, indent + 4))

        if current_error and isinstance(current_error, str):
            if current_error.code == 'no_additional_properties':
                output += click.style('%s^ %s\n' % (indent_str, current_error), fg='red')
            else:
                output += click.style('%s%s  ^ %s\n' % (indent_str, ' ' * len(key), current_error), fg='red')

        if isinstance(value, (list, dict)):
            output += render(value, current_error, indent + 4)

    return output
