"""The SCons AsciiDoc tool

This is an SCons tool for compiling AsciiDoc documents to various formats using
the `asciidoc` and `a2x` programs using two builders, `AsciiDoc` and `A2X`, to
the construction environment.
"""

# TODO: write tests
# TODO: try out docbook, htmlhelp and manpage formats
# FIXME: 'manpage' and 'epub' formats produce xsltproc failures
# TODO: complete implicit dependency handling
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
# Actual potential candidates for implicit dependencies:
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

#######################################################
# functions used to help generate the build signature #
#######################################################

def _gen_ad_conf_str(target, source, env, for_signature):
    return ' '.join('-f ' + c for c in env['AD_CONFFILES'])

def _gen_ad_attr_str(target, source, env, for_signature):
    return ' '.join('-a "'+a+'"' for a in env['AD_ATTRIBUTES'])

def _gen_a2x_conf_str(target, source, env, for_signature):
    if env['A2X_CONFFILE']:
        return "--conf-file=" + env['A2X_CONFFILE']
    return ''

def _gen_a2x_attr_str(target, source, env, for_signature):
    return ' '.join('-a "'+a+'"' for a in env['A2X_ATTRIBUTES'])

def _gen_a2x_res_str(target, source, env, for_signature):
    return ' '.join('-r "'+r+'"' for r in env['A2X_RESOURCES'])

def _gen_a2x_resman_str(target, source, env, for_signature):
    if env['A2X_RESOURCEMANIFEST']:
        return '-m ' + env['A2X_RESOURCEMANIFEST']
    else:
        return ''

##########################
# generate() and friends #
##########################

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

    import subprocess as subp
    import pseudo_builders

    # put the builders in the environment
    env['BUILDERS']['AsciiDoc'] = pseudo_builders.asciidoc_builder
    env['BUILDERS']['A2X']      = pseudo_builders.a2x_builder

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

    ad_asciidoc = _get_prog_path(env, 'AD_ASCIIDOC', 'asciidoc')
    a2x_a2x     = _get_prog_path(env, 'A2X_A2X', 'a2x')

    try:
        ad_proc = subp.Popen([ad_asciidoc, '--version'], stdout=subp.PIPE)
        ad_ver  = ad_proc.communicate()[0].split()[-1]
    except:
        ad_ver = ''

    # get the a2x version
    try:
        a2x_proc = subp.Popen([a2x_a2x, '--version'], stdout=subp.PIPE)
        a2x_ver = a2x_proc.communicate()[0].split()[-1]
    except:
        a2x_ver = ''

    # set asciidoc defaults; should match the asciidoc(1) defaults
    env['AD_ASCIIDOC']    = ad_asciidoc
    env['AD_VERSION']     = ad_ver
    env['AD_BACKEND']     = 'html'
    env['AD_DOCTYPE']     = 'article'
    env['AD_CONFFILES']   = []
    env['AD_ATTRIBUTES']  = []

    # set a2x defaults; should match the a2x(1) defaults
    env['A2X_A2X']        = a2x_a2x
    env['A2X_VERSION']    = a2x_ver
    env['A2X_FORMAT']     = 'pdf'
    env['A2X_DOCTYPE']    = 'article'
    env['A2X_CONFFILE']   = ''
    env['A2X_ATTRIBUTES'] = []
    env['A2X_RESOURCES']  = []
    env['A2X_RESOURCEMANIFEST'] = ''
    env['A2X_KEEPARTIFACTS']    = True

    # variables used to generate the build signature
    env['AD_GET_CONF']    = _gen_ad_conf_str
    env['AD_GET_ATTR']    = _gen_ad_attr_str
    env['A2X_GET_CONF']   = _gen_a2x_conf_str
    env['A2X_GET_ATTR']   = _gen_a2x_attr_str
    env['A2X_GET_RES']    = _gen_a2x_res_str
    env['A2X_GET_RESMAN'] = _gen_a2x_resman_str

def exists(env):
    # expect a2x to be there if asciidoc is
    return _get_prog_path(env, 'AD_ASCIIDOC', 'asciidoc')
