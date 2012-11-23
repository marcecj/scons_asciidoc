import SCons.Builder
import SCons.Errors
import SCons.Scanner
import SCons.Script
import SCons.Util
import os
import subprocess as subp
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

# in the case of the manpage backend, the document should have the category as
# part of its name, e.g., "myprog.1.txt", in which case the target becomes
# "myprog.1".
_a2x_backend_suffix_map = {
    "chunked":    ".chunked",
    "docbook":    ".xml",
    "dvi":        ".dvi",
    "epub":       ".epub",
    "htmlhelp":   ".hhp",
    "manpage":    "",
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
    """Scans AsciiDoc files for implicit dependencies."""

    import re

    if not os.path.isfile(node.path):
        return []

    txt_reg = re.compile('include1{0,1}:{1,2}(.+?)\[')
    txt_files = txt_reg.findall(node.get_contents())

    img_reg = re.compile('image:{1,2}(.+?)\[')
    img_files = img_reg.findall(node.get_contents())

    return txt_files + img_files

def _ad_scanner_check(node, env):
    """Check whether a node should be scanned."""

    # Only scan asciidoc source files (put another way, *do not* scan things
    # like image files)
    if node.path.endswith('.txt'):
        return True
    return False

__ad_src_scanner = SCons.Scanner.Scanner(
    _ad_scanner,
    scan_check = _ad_scanner_check,
    recursive=True
)

def _gen_ad_suffix(env, sources):
    """Generate the AsciiDoc target suffix depending on the chosen backend."""

    ad_backend = env['AD_BACKEND']

    return _ad_backend_suffix_map[ad_backend]

def _gen_a2x_suffix(env, sources):
    """Generate the a2x target suffix depending on the chosen format."""

    a2x_format = env['A2X_FORMAT']

    return _a2x_backend_suffix_map[a2x_format]

def _gen_ad_conf_str(target, source, env, for_signature):
    return ' '.join('-f ' + c for c in env['AD_CONFFILES'])

def _gen_a2x_conf_str(target, source, env, for_signature):
    if env['A2X_CONFFILE']:
        return "--conf-file=" + env['A2X_CONFFILE']
    return ''

def _gen_ad_attr_str(target, source, env, for_signature):
    return ' '.join('-a "'+a+'"' for a in env['AD_ATTRIBUTES'])

def _gen_a2x_attr_str(target, source, env, for_signature):
    return ' '.join('-a "'+a+'"' for a in env['A2X_ATTRIBUTES'])

def _gen_a2x_res_str(target, source, env, for_signature):
    return ' '.join('-r "'+r+'"' for r in env['A2X_RESOURCES'])

def _gen_a2x_resman_str(target, source, env, for_signature):
    if env['A2X_RESOURCEMANIFEST']:
        return '-m ' + env['A2X_RESOURCEMANIFEST']
    else:
        return ''

_ad_action = '${AD_ASCIIDOC} \
        -b ${AD_BACKEND} \
        -d ${AD_DOCTYPE} \
        ${AD_GET_CONF} \
        ${AD_GET_ATTR} \
        ${AD_FLAGS} \
        -o ${TARGET} ${SOURCE}'

__asciidoc_bld = SCons.Builder.Builder(
    action = _ad_action,
    suffix = _gen_ad_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
)

_a2x_action = "${A2X_A2X} \
        -f ${A2X_FORMAT} \
        -d ${A2X_DOCTYPE} \
        ${A2X_GET_CONF} \
        ${A2X_GET_ATTR} \
        ${A2X_GET_RES} \
        ${A2X_GET_RESMAN} \
        $( ${A2X_KEEPARTIFACTS and '-k' or ''} $)\
        ${A2X_FLAGS} \
        -D ${TARGET.dir} \
        ${SOURCE}"

__a2x_bld = SCons.Builder.Builder(
    action = _a2x_action,
    suffix = _gen_a2x_suffix,
    single_source = True,
    source_scanner = __ad_src_scanner,
    target_factory = SCons.Script.Entry,
)

# TODO: finish these functions
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
#
# Actual potential candidates to be emitted here:
# - image directories when the data-uri option is set:
#     - iconsdir
#     - imagesdir
# - files referenced in sys::[] macros; basically: expand the glob, split() it
# and check if any of the substrings are files (or directories)
# - find other implicit files used, i.e., from --theme and --filter (asciidoc)
# and from --icons-dir, --stylesheet, and --xsl-file (a2x); see the respective
# man pages
#
# (again, see http://www.methods.co.nz/asciidoc/userguide.html#X27 for more)
#
# Also, see if it is possible to deal with ifdef:[].
def _ad_add_extra_depends(env, target, source):
    """Add extra dependencies to an asciidoc target."""

    backend = env['AD_BACKEND']
    doctype = env['AD_DOCTYPE']

    src = str(source[0])
    s = SCons.Util.splitext(os.path.basename(src))[0]
    d = os.path.dirname(src)

    conf_files = (
        "asciidoc.conf",
        backend + ".conf",
        backend + "-"      + doctype + ".conf",
        s       + ".conf",
        s       + "-"      + backend + ".conf",
    )

    conf_files = [os.sep.join([d, c]) for c in conf_files]
    conf_files.extend(env['AD_CONFFILES'])

    for c in conf_files:
        if os.path.isfile(c):
            env.Depends(target, c)

def _get_res_entry(line, dir):
    """Return an A2X resource file/directory found in a resource spec.

    See the a2x man page for details on the format.
    """

    line = line.split('=')
    res = line[0]
    # resource files are also searched relatively to the source directory, so if
    # a resource spec is specified like that, we also need to check relatively
    # to the source directory
    alt_res = os.sep.join([dir, res])

    res_list = []
    if len(line) == 2:
        # either
        #   <resource_file>=<destination_file>
        # or
        #   .<ext>=<mimetype>
        if res.startswith('.'):
            pass
        elif os.path.isfile(res):
            res_list.append(res)
        elif os.path.isfile(alt_res):
            res_list.append(alt_res)
    elif len(line) == 1:
        # either a file or directory
        if os.path.exists(res):
            res_list.append(res)
        elif os.path.exists(alt_res):
            res_list.append(alt_res)

    return res_list

def _a2x_add_extra_depends(env, target, source):
    """Add extra dependencies to an a2x target."""

    doctype = env['A2X_DOCTYPE']
    resman  = env['A2X_RESOURCEMANIFEST']

    src = str(source[0])
    s = SCons.Util.splitext(os.path.basename(src))[0]
    d = os.path.dirname(src)

    # check for various conf files

    conf_files = (
        "asciidoc.conf",
        "docbook.conf",
        "docbook-" + doctype + ".conf",
        s + ".conf",
        s + "-docbook.conf",
    )

    conf_files = [os.sep.join([d, c]) for c in conf_files]
    conf_files.append(env['A2X_CONFFILE'])

    for c in conf_files:
        if os.path.isfile(c):
            env.Depends(target, c)

    # check a resource manifest file for file/dir names

    # if a resource manifest is specified, search for directories and files in
    # each line, and add them to the dependency list
    if resman:
        with open(resman) as f:
            for line in f:
                resource = _get_res_entry(line, d)
                if resource:
                    env.Depends(target, resource)

    # add resource files to the dependency list

    # for each resource specified, search for directories and files, and add
    # them to the dependency list
    for res in env['A2X_RESOURCES']:
        resource = _get_res_entry(res, d)
        if resource:
            env.Depends(target, resource)

def asciidoc_builder(env, target, source, *args, **kwargs):
    """An asciidoc pseudo-builder."""

    ad_backend = env['AD_BACKEND']
    ad_doctype = env['AD_DOCTYPE']

    if ad_backend not in _ad_valid_backends:
        raise ValueError("Invalid AsciiDoc backend '%s'." % ad_backend)

    if ad_doctype not in _valid_doctypes:
        raise ValueError("Invalid AsciiDoc doctype '%s'." % ad_doctype)

    if ad_doctype == 'book' and 'docbook' not in ad_backend:
        raise SCons.Errors.UserError(
            "Doctype 'book' only supported by docbook backends"
        )

    r = __asciidoc_bld(env, target, source, *args, **kwargs)

    # add extra dependencies, like conf files
    for t, s in izip(r, source):
        _ad_add_extra_depends(env, t, [s])

    return r

def a2x_builder(env, target, source, *args, **kwargs):
    """An a2x pseudo-builder."""

    # handle overriding construction variables by cloning the environment and
    # passing the unpacked keyword arguments; this is needed because this is a
    # pseudo-builder
    env = env.Clone(**kwargs)

    a2x_doctype = env['A2X_DOCTYPE']
    a2x_format  = env['A2X_FORMAT']
    a2x_flags   = env.Split(env['A2X_FLAGS'])
    keep_temp   = env['A2X_KEEPARTIFACTS']

    if a2x_format not in _a2x_valid_formats:
        raise ValueError("Invalid A2X format '%s'." % a2x_format)

    if a2x_doctype not in _valid_doctypes:
        raise ValueError("Invalid A2X doctype '%s'." % a2x_doctype)

    if a2x_format == 'manpage' and a2x_doctype != 'manpage':
        raise SCons.Errors.UserError(
            "A2X format set to 'manpage', but Doctype set to '%s'." % a2x_doctype
        )

    r = __a2x_bld(env, target, source, *args, **kwargs)

    # make sure to clean up intermediary files when the target is cleaned
    # TODO: the following formats do not add additional targets: pdf, ps, tex
    # (I haven't verified ps, though)
    # TODO: try out docbook, htmlhelp and manpage
    # FIXME: the following formats do not produce final output, but do not raise
    # any errors: "dvi", "ps"
    # FIXME: 'manpage' and 'epub' produce xsltproc failures
    for t, s in izip(r, source):

        # docbook is the only format with one target per source
        if a2x_format == 'docbook':
            break

        # add extra dependencies, like conf files
        _a2x_add_extra_depends(env, t, [s])

        fbasename = SCons.Util.splitext(t.path)[0]
        fpath     = os.path.dirname(str(t))

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

def _get_prog_path(env, key, name):
    """Try to find the executable 'name' and store its location in env[key]."""

    # check if the user already specified the location
    try:
        return env[key]
    except KeyError:
        pass

    # asciidoc and a2x may be installed with a '.py' suffix
    prog_path = env.WhereIs(name) or env.WhereIs(name+'.py')

    # Explicitly do not raise an error here. If asciidoc is not installed, then
    # the build system using this tool should be able to deal with it.
    return prog_path

def generate(env):

    # put the builders in the environment
    env['BUILDERS']['AsciiDoc'] = asciidoc_builder
    env['BUILDERS']['A2X']      = a2x_builder

    # get the asciidoc version
    #
    # NOTE: I originally wanted to do something like this:
    #
    #     class get_prog_version(object):
    #         def __init__(self, progvar):
    #             self.progvar = progvar
    #
    #         def __call__(self, target, source, env, for_signature):
    #             prog_exe = env[self.progvar]
    #             proc = subp.Popen([prog_exe, '--version'], stdout=subp.PIPE)
    #             out = proc.communicate()[0].split()[-1]
    #             return out
    #
    # An then do:
    #
    #     env['GET_PROG_VERSION'] = get_prog_version
    #     env['AD_VERSION']       = "${GET_PROG_VERSION('AD_ASCIIDOC')}"
    #     env['A2X_VERSION']      = "${GET_PROG_VERSION('A2X_A2X')}"
    #
    # In order to let AD_ASCIIDOC/A2X_A2X be defined by the calling SConstruct
    # file (to implement a sort of lazy evaluation of the version variables).
    # But it seems as if that is not supported by SCons.

    try:
        ad_proc = subp.Popen(['asciidoc', '--version'], stdout=subp.PIPE)
        ad_ver  = ad_proc.communicate()[0].split()[-1]
    except OSError:
        ad_ver = ''

    # get the a2x version
    try:
        a2x_proc = subp.Popen(['a2x', '--version'], stdout=subp.PIPE)
        a2x_ver = a2x_proc.communicate()[0].split()[-1]
    except OSError:
        a2x_ver = ''

    # set asciidoc defaults; should match the asciidoc(1) defaults
    env['AD_ASCIIDOC']  = _get_prog_path(env, 'AD_ASCIIDOC', 'asciidoc')
    env['AD_BACKEND']   = 'html'
    env['AD_DOCTYPE']   = 'article'
    env['AD_CONFFILES'] = []
    env['AD_GET_CONF']  = _gen_ad_conf_str
    env['AD_ATTRIBUTES'] = []
    env['AD_GET_ATTR']  = _gen_ad_attr_str
    env['AD_VERSION']   = ad_ver

    # set a2x defaults; should match the a2x(1) defaults
    env['A2X_A2X']      = _get_prog_path(env, 'A2X_A2X', 'a2x')
    env['A2X_FORMAT']   = 'pdf'
    env['A2X_DOCTYPE']  = 'article'
    env['A2X_CONFFILE'] = ''
    env['A2X_GET_CONF'] = _gen_a2x_conf_str
    env['A2X_ATTRIBUTES'] = []
    env['A2X_GET_ATTR'] = _gen_a2x_attr_str
    env['A2X_RESOURCES'] = []
    env['A2X_GET_RES']  = _gen_a2x_res_str
    env['A2X_RESOURCEMANIFEST'] = ''
    env['A2X_GET_RESMAN'] = _gen_a2x_resman_str
    env['A2X_KEEPARTIFACTS'] = False
    env['A2X_VERSION']  = a2x_ver

def exists(env):
    # expect a2x to be there if asciidoc is
    if not env.WhereIs("asciidoc"):
        return None
    return True
