from apistar import codecs
import apistar
import click
import jinja2
import os
import shutil


def static_url(filename):
    return filename


@click.group()
def main():
    pass


@click.command()
@click.argument('schema', type=click.File('rb'))
def validate(schema):
    codec = codecs.OpenAPICodec()
    content = schema.read()
    document = codec.decode(content)
    click.echo(document)


@click.command()
@click.argument('schema', type=click.File('rb'))
def docs(schema):
    codec = codecs.OpenAPICodec()
    content = schema.read()
    document = codec.decode(content)

    loader = jinja2.PrefixLoader({
        'apistar': jinja2.PackageLoader('apistar', 'templates')
    })
    env = jinja2.Environment(autoescape=True, loader=loader)

    template = env.get_template('apistar/docs/index.html')
    code_style = None  # pygments_css('emacs')
    output_text = template.render(
        document=document,
        langs=['javascript', 'python'],
        code_style=code_style,
        static_url=static_url
    )

    directory = 'site'
    output_path = os.path.join(directory, 'index.html')
    if not os.path.exists(directory):
        os.makedirs(directory)
    output_file = open(output_path, 'w')
    output_file.write(output_text)
    output_file.close()

    static_dir = os.path.join(os.path.dirname(apistar.__file__), 'static')
    shutil.copytree(static_dir, os.path.join(directory, 'apistar'))

    click.echo('Documentation built at %s' % output_path)



main.add_command(docs)
main.add_command(validate)
