import SCons.Builder
import SCons.Scanner
import os

# TODO: write tests
# TODO: in order to get the dependencies for "chunked", "epub" and "htmlhelp"
# formats right, refactor so that a pseudo-builder wraps the actual builder and
# call Depends() on the appropriate directories

def _ad_scanner(node, env, path):
    """Scans AsciiDoc files for include::[] directives"""

    import re

    fname = str(node)

    # TODO: maybe raise an error here?
    if not os.path.isfile(fname):
        return []

    reg = re.compile('include::(.+)\[\]')
    res = reg.findall(node.get_contents())

    return res

__ad_src_scanner = SCons.Scanner.Scanner(_ad_scanner, recursive=True)

def _a2x_emitter(target, source, env):
    """Target emitter for the A2X builder."""

    # the a2x builder is single-source only, so we know there is only one source
    # file to check
    fname     = os.path.basename(source[0].path)
    fbasename = fname.rpartition('.')[0]
    fpath     = os.path.dirname(source[0].path)

    a2x_format = env['A2XFORMAT']

    # determine whether artifacts are to be kept or not
    a2x_flags = env['A2XFLAGS']
    a2x_flags = (a2x_flags if type(a2x_flags) is list else a2x_flags.split())
    keep_temp = '-k' in a2x_flags or '--keep-artifacts' in a2x_flags

    file_list = []
    if a2x_format != 'docbook' and keep_temp:
        file_list.append(fbasename + '.xml')

    # TODO: the following formats do not produce final output, but do not raise
    # any errors: "dvi", "ps"
    # NOTE: the following formats do not add additional targets: pdf, ps, tex
    # (I haven't verified ps, though)
    if   a2x_format == 'chunked':

        file_list.append(fbasename + '.chunked')

    elif a2x_format == 'dvi':

        pass

    elif a2x_format == 'epub' and keep_temp:

        # FIXME: xsltproc fails on my system
        file_list.append(fbasename + '.epub.d')

    elif a2x_format == 'htmlhelp' and keep_temp:

        # FIXME: fails on my system with a UnicodeDecodeError
        file_list.append(fbasename + '.hhc')
        file_list.append(fbasename + '.htmlhelp')

    elif a2x_format == 'manpage':

        # FIXME: xsltproc fails here
        pass

    elif a2x_format == 'text' and keep_temp:

        file_list.append(os.path.basename(target[0].path) + '.html')

    elif a2x_format == 'xhtml':

        file_list.append('docbook-xsl.css')

    file_list = [os.sep.join([fpath, f]) for f in file_list]

    target.extend(file_list)

    return (target, source)

def _gen_ad_suffix(env, sources):
    """Generate the AsciiDoc target suffix depending on the chosen backend."""

    html_like = ('xhtml11', 'html', 'html4', 'html5', 'slidy', 'wordpress')

    if   env['ASCIIDOCBACKEND'] == 'pdf':
        return '.pdf'
    elif env['ASCIIDOCBACKEND'] == 'latex':
        return '.tex'
    elif env['ASCIIDOCBACKEND'].startswith('docbook'):
        return '.xml'
    elif env['ASCIIDOCBACKEND'] in html_like:
        return '.html'

# needed in case you want to do something with the target
# TODO: figure out chunked, docbook, htmlhelp and manpage
def _gen_a2x_suffix(env, sources):
    """Generate the a2x target suffix depending on the chosen format."""

    a2x_format = env['A2XFORMAT']

    if   a2x_format == 'chunked':
        return '.chunked'
    elif a2x_format == 'docbook':
        return '.xml'
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

_ad_action = '${ASCIIDOC} \
        -b ${ASCIIDOCBACKEND} ${ASCIIDOCFLAGS} \
        -o ${TARGET} ${SOURCE}'

__asciidoc_bld = SCons.Builder.Builder(
    action = _ad_action,
    suffix = _gen_ad_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
)

__a2x_bld = SCons.Builder.Builder(
    action = '${A2X} -f ${A2XFORMAT} ${A2XFLAGS} ${SOURCE}',
    suffix = _gen_a2x_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
    emitter = _a2x_emitter,
)


def generate(env):

    env['BUILDERS']['AsciiDoc'] = __asciidoc_bld
    env['BUILDERS']['A2X']      = __a2x_bld

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
