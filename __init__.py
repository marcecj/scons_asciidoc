import SCons.Builder
import SCons.Scanner
import os

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
    fname_dir = os.path.dirname(source[0].path)

    file_list = []
    if env['A2XFORMAT'] != 'docbook':
        file_list.append(fbasename + '.xml')

    # TODO: write a proper emitter for "chunked", "epub" and "htmlhelp" formats
    # TODO: the following formats do not produce final output, but do not raise
    # any errors: "dvi", "ps"
    # NOTE: the following formats do not add additional targets: pdf, ps, tex
    # (I haven't verified ps, though)
    if   env['A2XFORMAT'] == 'chunked':

        file_list.append('index.chunked')

    elif env['A2XFORMAT'] == 'dvi':

        # TODO: this format produces nothing on my system
        pass

    elif env['A2XFORMAT'] == 'epub':

        # TODO: xsltproc fails on my system
        file_list.append('index.epub.d')

    elif env['A2XFORMAT'] == 'htmlhelp':

        # TODO: fails on my system with a UnicodeDecodeError
        file_list.extend([fbasename + '.hhc', fbasename + '.hhp'])
        file_list.append('index.htmlhelp')

    elif env['A2XFORMAT'] == 'manpage':

        # TODO: find a way to test this
        pass

    elif env['A2XFORMAT'] == 'text':

        file_list.append(fname + '.html')

    elif env['A2XFORMAT'] == 'xhtml':

        file_list.append('docbook-xsl.css')

    file_list = [os.sep.join([fname_dir, f]) for f in file_list]

    target += file_list

    return (target, source)

def asciidoc_builder(env):
    """Returns an AsciiDoc builder"""

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

    # needed in case you want to do something with the target
    # TODO: figure out chunked, docbook, htmlhelp and manpage
    def gen_suffix(*kargs, **kwargs):
        if   env['A2XFORMAT'] == 'chunked':
            return '.chunked'
        elif env['A2XFORMAT'] == 'docbook':
            return '.xml' # TODO: is it really one file?
        elif env['A2XFORMAT'] == 'dvi':
            return '.dvi'
        elif env['A2XFORMAT'] == 'epub':
            return '.epub'
        elif env['A2XFORMAT'] == 'htmlhelp':
            return '.hhp'
        elif env['A2XFORMAT'] == 'manpage':
            return '.man'
        elif env['A2XFORMAT'] == 'pdf':
            return '.pdf'
        elif env['A2XFORMAT'] == 'ps':
            return '.ps'
        elif env['A2XFORMAT'] == 'tex':
            return '.tex'
        elif env['A2XFORMAT'] == 'text':
            return '.text'
        elif env['A2XFORMAT'] == 'xhtml':
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
