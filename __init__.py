import SCons.Builder
import SCons.Scanner
import os

# TODO: write tests

def asciidoc_scanner(node, env, path):
    """Scans AsciiDoc files for include::[] directives"""

    import re

    fname = str(node)

    # TODO: maybe raise an error here?
    if not os.path.isfile(fname):
        return []

    reg = re.compile('include::(.+)\[\]')
    res = reg.findall(node.get_contents())

    return res

def a2x_emitter(target, source, env):
    """Target emitter for the A2X builder."""

    # the a2x builder is single-source only, so we know there is only one source
    # file to check
    fname     = os.path.basename(source[0].path)
    fbasename = fname.rpartition('.')[0]
    fpath     = os.path.dirname(source[0].path)

    a2x_format = env['A2XFORMAT']

    file_list = []
    if a2x_format != 'docbook':
        file_list.append(fbasename + '.xml')

    # TODO: write a proper emitter for "chunked", "epub" and "htmlhelp" formats
    # TODO: the following formats do not produce final output, but do not raise
    # any errors: "dvi", "ps"
    # NOTE: the following formats do not add additional targets: pdf, ps, tex
    # (I haven't verified ps, though)
    if   a2x_format == 'chunked':

        file_list.append('index.chunked')

    elif a2x_format == 'dvi':

        # TODO: this format produces nothing on my system
        pass

    elif a2x_format == 'epub':

        # FIXME: xsltproc fails on my system
        file_list.append('index.epub.d')

    elif a2x_format == 'htmlhelp':

        # FIXME: fails on my system with a UnicodeDecodeError
        file_list.append(fbasename + '.hhc')
        file_list.append('index.htmlhelp')

    elif a2x_format == 'manpage':

        # FIXME: xsltproc fails here, too
        pass

    elif a2x_format == 'text':

        file_list.append(os.path.basename(target[0].path) + '.html')

    elif a2x_format == 'xhtml':

        file_list.append('docbook-xsl.css')

    file_list = [os.sep.join([fpath, f]) for f in file_list]

    target += file_list

    return (target, source)

def asciidoc_builder(env):
    """Returns an AsciiDoc builder"""

    # generate the target suffix depending on the chosen backend
    def gen_suffix(*kargs, **kwargs):
        html_like = ('xhtml11', 'html', 'html4', 'html5', 'slidy', 'wordpress')

        if   env['ASCIIDOCBACKEND'] == 'pdf':
            return '.pdf'
        elif env['ASCIIDOCBACKEND'] == 'latex':
            return '.tex'
        elif env['ASCIIDOCBACKEND'].startswith('docbook'):
            return '.xml'
        elif env['ASCIIDOCBACKEND'] in html_like:
            return '.html'

    ad_action = '${ASCIIDOC} \
            -b ${ASCIIDOCBACKEND} ${ASCIIDOCFLAGS} \
            -o ${TARGET} ${SOURCE}'

    ad_scanner = SCons.Scanner.Scanner(asciidoc_scanner, recursive=True)

    asciidoc = SCons.Builder.Builder(
        action = ad_action,
        suffix = gen_suffix,
        single_source = True,
        source_scanner = ad_scanner,
    )

    return asciidoc

def a2x_builder(env):
    """Returns an a2x builder"""

    # generate the target suffix depending on the chosen format; needed in case
    # you want to do something with the target
    # TODO: figure out chunked, docbook, htmlhelp and manpage
    def gen_suffix(*kargs, **kwargs):
        a2x_format = env['A2XFORMAT']
        if   a2x_format == 'chunked':
            return '.chunked'
        elif a2x_format == 'docbook':
            return '.xml' # TODO: is it really one file?
        elif a2x_format == 'dvi':
            return '.dvi'
        elif a2x_format == 'epub':
            return '.epub'
        elif a2x_format == 'htmlhelp':
            return '.hhp'
        elif a2x_format == 'manpage':
            return '.man'
        elif a2x_format == 'pdf':
            return '.pdf'
        elif a2x_format == 'ps':
            return '.ps'
        elif a2x_format == 'tex':
            return '.tex'
        elif a2x_format == 'text':
            return '.text'
        elif a2x_format == 'xhtml':
            return '.html'

    ad_scanner = SCons.Scanner.Scanner(asciidoc_scanner, recursive=True)

    a2x = SCons.Builder.Builder(
        action = '${A2X} -f ${A2XFORMAT} ${A2XFLAGS} ${SOURCE}',
        suffix = gen_suffix,
        single_source = True,
        source_scanner = ad_scanner,
        emitter = a2x_emitter,
    )

    return a2x

def generate(env):

    env['BUILDERS']['AsciiDoc'] = asciidoc_builder(env)
    env['BUILDERS']['A2X']      = a2x_builder(env)

    # set defaults; should match the asciidoc/a2x defaults
    env['ASCIIDOC']        = 'asciidoc'
    env['ASCIIDOCBACKEND'] = 'html'
    env['A2X']             = 'a2x'
    env['A2XFORMAT']       = 'pdf'

def exists(env):
    # expect a2x to be there if asciidoc is
    if not env.WhereIs("asciidoc"):
        return None
    return True
