import SCons.Builder
import SCons.Errors
import SCons.Scanner
import SCons.Util
import os
from itertools import izip

# TODO: write tests

_ad_valid_backends = frozenset((
    "docbook45",
    "docbook",
    "xhtml11",
    "html",
    "html4",
    "html5",
    "slidy",
    "wordpress",
    "latex",
))

_ad_backend_suffix_map = {
    "docbook45":   ".xml",
    "docbook":     ".xml",
    "xhtml11":     ".html",
    "html":        ".html",
    "html4":       ".html",
    "html5":       ".html",
    "slidy":       ".html",
    "wordpress":   ".html",
    "latex":       ".tex",
}

_a2x_valid_formats = frozenset((
    "chunked",
    "docbook",
    "dvi",
    "epub",
    "htmlhelp",
    "manpage",
    "pdf",
    "ps",
    "tex",
    "text",
    "xhtml",
))

_a2x_backend_suffix_map = {
    "chunked":    ".chunked",
    "docbook":    ".xml",
    "dvi":        ".dvi",
    "epub":       ".epub",
    "htmlhelp":   ".hhp",
    "manpage":    ".man", # FIXME: this is wrong
    "pdf":        ".pdf",
    "ps":         ".ps",
    "tex":        ".tex",
    "text":       ".text",
    "xhtml":      ".html",
}

_valid_doctypes = frozenset((
    "article",
    "manpage",
    "book",
))

def _ad_scanner(node, env, path):
    """Scans AsciiDoc files for include::[] directives"""

    import re

    fname = str(node)

    if not os.path.isfile(fname):
        return []

    reg = re.compile('include::(.+)\[\]')
    res = reg.findall(node.get_contents())

    return res

__ad_src_scanner = SCons.Scanner.Scanner(_ad_scanner, recursive=True)

# TODO: finish this emitter
#
# NOTE: AsciiDoc does not seem to output extra targets.  In the case where JS
# and CSS is linked to the HTML file, it must be manually copied to the
# appropriate location.  In this case, the files would be part of the source
# code repository anyway, and the dependencies of the target file on them should
# not matter.  Furthermore, they are irrelevant to the produced HTML, and even
# when they are embedded, they reside in a central asciidoc configuration
# directory in $HOME, /etc/ or /usr/local/etc/ (see
# http://www.methods.co.nz/asciidoc/userguide.html#X27).  I believe that is
# *outside* the scope of this AsciiDoc tool.
def _ad_emitter(target, source, env):
    """Target emitter for the AsciiDoc builder."""

    # Actual potential candidates to be emitted here:
    # - image directories when the data-uri option is set:
    #     - iconsdir
    #     - imagesdir
    # - images included with the image:[] macro
    # - AsciiDoc configuration files in the source directory:
    #     - asciidoc.conf
    #     - <backend>.conf and <backend>-<doctype>.conf
    #     - <docfile>.conf and <docfile>-<backend>.conf
    #     -> add each conf file to the sources if it exists, or just make the
    #     target depend on it

    return (target, source)

def _gen_ad_suffix(env, sources):
    """Generate the AsciiDoc target suffix depending on the chosen backend."""

    ad_backend = env['ASCIIDOCBACKEND']

    return _ad_backend_suffix_map[ad_backend]

# needed in case you want to do something with the target
# TODO: try out docbook, htmlhelp and manpage
def _gen_a2x_suffix(env, sources):
    """Generate the a2x target suffix depending on the chosen format."""

    a2x_format = env['A2XFORMAT']

    return _a2x_backend_suffix_map[a2x_format]

_ad_action = '${ASCIIDOC} \
        -b ${ASCIIDOCBACKEND} \
        -d ${ASCIIDOCDOCTYPE} \
        ${ASCIIDOCFLAGS} \
        -o ${TARGET} ${SOURCE}'

__asciidoc_bld = SCons.Builder.Builder(
    action = _ad_action,
    suffix = _gen_ad_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
    emitter = _ad_emitter,
)

_a2x_action = '${A2X} \
        -f ${A2XFORMAT} \
        -d ${A2XDOCTYPE} \
        ${A2XFLAGS} \
        ${SOURCE}'

__a2x_bld = SCons.Builder.Builder(
    action = _a2x_action,
    suffix = _gen_a2x_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
    emitter = _ad_emitter,
)

def _partition_targets(target, source):
    """Partition target lists into one list per source."""

    t_basename = [SCons.Util.splitext(str(t))[0] for t in target]

    # find the indices corresponding to the next source
    idx = [t_basename.index(SCons.Util.splitext(str(s))[0]) for s in source]
    idx.append(len(target))

    # now split the target list
    new_list = [target[s:e] for s,e in izip(idx[:-1], idx[1:])]
    new_list = SCons.Util.NodeList(new_list)

    return new_list

def asciidoc_builder(env, target, source, *args, **kwargs):

    ad_backend = env['ASCIIDOCBACKEND']
    ad_doctype = env['ASCIIDOCDOCTYPE']

    if ad_backend not in _ad_valid_backends:
        raise ValueError("Invalid AsciiDoc backend '%s'." % ad_backend)

    if ad_doctype not in _valid_doctypes:
        raise ValueError("Invalid AsciiDoc doctype '%s'." % ad_doctype)

    if ad_doctype == 'book' and 'docbook' not in ad_backend:
        raise SCons.Errors.UserError(
            "Doctype 'book' only supported by docbook backends"
        )

    r = __asciidoc_bld(env, target, source, *args, **kwargs)

    return r

def a2x_builder(env, target, source, *args, **kwargs):

    a2x_doctype = env['A2XDOCTYPE']
    a2x_format  = env['A2XFORMAT']
    a2x_flags   = env.Split(env['A2XFLAGS'])

    if a2x_format not in _a2x_valid_formats:
        raise ValueError("Invalid A2X format '%s'." % a2x_format)

    if a2x_doctype not in _valid_doctypes:
        raise ValueError("Invalid A2X doctype '%s'." % a2x_doctype)

    if a2x_format == 'manpage' and a2x_doctype != 'manpage':
        raise SCons.Errors.UserError(
            "A2X format set to 'manpage', but Doctype set to '%s'." % a2x_doctype
        )

    r = __a2x_bld(env, target, source, *args, **kwargs)

    # create a list of target lists, one per source
    partitioned_r = _partition_targets(r, source)

    # determine whether artifacts are to be kept or not
    keep_temp = '-k' in a2x_flags or '--keep-artifacts' in a2x_flags

    # make sure to clean up intermediary files when the target is cleaned
    # NOTE: the following formats do not add additional targets: pdf, ps, tex
    # (I haven't verified ps, though)
    # FIXME: the following formats do not produce final output, but do not raise
    # any errors: "dvi", "ps"
    # FIXME: 'manpage' and 'epub' produce xsltproc failures
    for t, s in izip(partitioned_r, source):

        # docbook is the only format with one target per source
        if a2x_format == 'docbook':
            break

        t = t[0]

        fbasename = SCons.Util.splitext(t.path)[0]
        fpath     = os.path.dirname(str(s))

        if keep_temp:
            xml_temp = fbasename + '.xml'

        # Add t to the cleanup file list for when it's a directory
        cleanup_files = ([t, xml_temp] if keep_temp else [t])

        if a2x_format == 'chunked':

            html_files = env.Glob(os.sep.join([t.path, '*']))

            cleanup_files.extend(html_files)

        elif a2x_format == 'epub' and keep_temp:

            epub_dir = fbasename + '.epub.d'
            epub_files = env.Glob(os.sep.join([epub_dir, '*']))

            cleanup_files.append(epub_dir)
            cleanup_files.extend(epub_files)

        elif a2x_format == 'htmlhelp' and keep_temp:

            html_dir = fbasename + '.htmlhelp'
            html_files = env.Glob(os.sep.join([html_dir, '*']))

            cleanup_files.append(fbasename + '.hhc')
            cleanup_files.append(html_dir)
            cleanup_files.extend(html_files)

        elif a2x_format == 'text' and keep_temp:

            html_file = t.path + '.html'

            cleanup_files.append(html_file)

        elif a2x_format == 'xhtml':

            css_file = os.sep.join([fpath, 'docbook-xsl.css'])
            cleanup_files.append(css_file)
            r.append(css_file)

        env.Clean(t, cleanup_files)

    return r

def generate(env):

    env['BUILDERS']['AsciiDoc'] = asciidoc_builder
    env['BUILDERS']['A2X']      = a2x_builder

    # set defaults; should match the asciidoc/a2x defaults
    # TODO: add ASCIIDOCVERSION and A2XVERSION variables.
    env['ASCIIDOC']        = 'asciidoc'
    env['ASCIIDOCBACKEND'] = 'html'
    env['ASCIIDOCDOCTYPE'] = 'article'
    env['A2X']             = 'a2x'
    env['A2XFORMAT']       = 'pdf'
    env['A2XDOCTYPE']      = 'article'

def exists(env):
    # expect a2x to be there if asciidoc is
    if not env.WhereIs("asciidoc"):
        return None
    return True
