import SCons.Builder
import SCons.Scanner
import SCons.Util
import os

# TODO: write tests

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
    #     -> add "ASCIIDOCDOCTYPE" env var and add the appropriate conf file to the
    #     sources if it exists

    return (target, source)

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
    # NOTE: the following formats are handled in the pseudo-builder: chunked,
    # epub, and the directory output of htmlhelp
    if a2x_format == 'dvi':

        pass

    elif a2x_format == 'htmlhelp' and keep_temp:

        # FIXME: fails on my system with a UnicodeDecodeError
        file_list.append(fbasename + '.hhc')

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
# TODO: try out docbook, htmlhelp and manpage
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

# TODO: add the -d option
_ad_action = '${ASCIIDOC} \
        -b ${ASCIIDOCBACKEND} ${ASCIIDOCFLAGS} \
        -o ${TARGET} ${SOURCE}'

__asciidoc_bld = SCons.Builder.Builder(
    action = _ad_action,
    suffix = _gen_ad_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
    emitter = _ad_emitter,
)

__a2x_bld = SCons.Builder.Builder(
    # TODO: add the -d option
    action = '${A2X} -f ${A2XFORMAT} ${A2XFLAGS} ${SOURCE}',
    suffix = _gen_a2x_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
    emitter = [_a2x_emitter, _ad_emitter],
)

def _partition_targets(target, source):
    """Partition target lists into one list per source."""

    t_basename = [str(t).rpartition('.')[0] for t in target]

    # find the indices corresponding to the next source
    idx = [t_basename.index(str(s).rpartition('.')[0]) for s in source]
    idx.append(len(target))

    # now split the target list
    new_list = [target[s:e] for s,e in zip(idx[:-1], idx[1:])]
    new_list = SCons.Util.NodeList(new_list)

    return new_list

def asciidoc_builder(env, target, source, *args, **kwargs):

    r = __asciidoc_bld(env, target, source, **kwargs)

    return r

def a2x_builder(env, target, source, *args, **kwargs):

    a2x_format = env['A2XFORMAT']
    a2x_flags  = env['A2XFLAGS']

    r = __a2x_bld(env, target, source, **kwargs)

    # create a list of target lists, one per source
    partitioned_r = _partition_targets(r, source)

    # determine whether artifacts are to be kept or not
    a2x_flags = (a2x_flags if type(a2x_flags) is list else a2x_flags.split())
    keep_temp = '-k' in a2x_flags or '--keep-artifacts' in a2x_flags

    # make sure to clean up intermediary files when the target is cleaned
    for entry in partitioned_r:

        # docbook is the only format with one target per source
        if a2x_format == 'docbook':
            break

        # the first entry is always the actual target; we know the emitter
        # appends the xml intermediary, so it is always the second entry
        t        = entry[0]
        if keep_temp:
            xml_temp = entry[1]

        fbasename = t.path.rpartition('.')[0]

        # Add t to the cleanup file list for when it's a directory
        cleanup_files = [t]

        if a2x_format == 'chunked':

            html_files = env.Glob(os.sep.join([t.path, '*']))

            cleanup_files.extend(html_files)

            env.Clean(t, cleanup_files)

            # make sure the xml intermediary does not depend on the html files
            if keep_temp:
                env.Ignore(xml_temp, html_files)

            # these files are the actual builder output, so add them to results
            r.extend(html_files)

        elif a2x_format == 'epub' and keep_temp:

            # FIXME: xsltproc fails here
            epub_dir = fbasename + '.epub.d'
            epub_files = env.Glob(os.sep.join([epub_dir, '*']))

            cleanup_files.append(epub_dir)
            cleanup_files.extend(epub_files)

            env.Clean(t, cleanup_files)

            # make sure the xml intermediary does not depend on the intermediate
            # epub files
            env.Ignore(xml_temp, epub_files)

        elif a2x_format == 'htmlhelp' and keep_temp:

            html_dir = fbasename + '.htmlhelp'
            html_files = env.Glob(os.sep.join([html_dir, '*']))

            cleanup_files.append(html_dir)
            cleanup_files.extend(html_files)

            env.Clean(t, cleanup_files)

            # make sure the xml intermediary does not depend on the html files
            env.Ignore(xml_temp, html_files)

    return r

def generate(env):

    env['BUILDERS']['AsciiDoc'] = asciidoc_builder
    env['BUILDERS']['A2X']      = a2x_builder

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
