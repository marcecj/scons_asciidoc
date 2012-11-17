import SCons.Builder
import SCons.Scanner

def asciidoc_scanner(node, env, path):
    """Scans AsciiDoc files for include::[] directives"""

    import os
    import re

    fname = str(node)

    # TODO: maybe raise an error here?
    if not os.path.isfile(fname):
        return []

    reg = re.compile('include::(.+)\[\]')
    res = reg.findall(node.get_contents())

    return res

# TODO: finish the emitter; it is mostly (only?) needed for temporary files left
# over when a2x fails (e.g., when the xmllint fails) so that SCons can clean
# them up
def asciidoc_emitter(target, source, env):

    pass

def asciidoc_builder(env):
    """Returns an AsciiDoc builder"""

    # TODO: experiment with docbook, as I have no experience with it
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
        # emitter = asciidoc_emitter,
    )

    return asciidoc

def a2x_builder(env):
    """Returns an a2x builder"""

    # needed in case you want to do something with the target
    # TODO: figure out chunked, docbook, htmlhelp and manpage
    def gen_suffix(*kargs, **kwargs):
        if   env['A2XFORMAT'] == 'chunked':
            return ''
        elif env['A2XFORMAT'] == 'docbook':
            return '.xml' # TODO: is it really one file?
        elif env['A2XFORMAT'] == 'dvi':
            return '.dvi'
        elif env['A2XFORMAT'] == 'epub':
            return '.epub'
        elif env['A2XFORMAT'] == 'htmlhelp':
            return ''
        elif env['A2XFORMAT'] == 'manpage':
            return ''
        elif env['A2XFORMAT'] == 'pdf':
            return '.pdf'
        elif env['A2XFORMAT'] == 'ps':
            return '.ps'
        elif env['A2XFORMAT'] == 'tex':
            return '.tex'
        elif env['A2XFORMAT'] == 'text':
            return '.txt'
        elif env['A2XFORMAT'] == 'xhtml':
            return '.html'

    ad_scanner = SCons.Scanner.Scanner(asciidoc_scanner, recursive=True)

    a2x = SCons.Builder.Builder(
        action = '${A2X} -f ${A2XFORMAT} ${A2XFLAGS} ${SOURCE}',
        suffix = gen_suffix,
        single_source = True,
        source_scanner = ad_scanner,
        # emitter = asciidoc_emitter,
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
