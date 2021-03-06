# This file contains the pseudo-builders and related code.

import SCons.Errors
import SCons.Util
import os
from itertools import izip

import builders

##################################################################
# valid values for backend/format/doctype construction variables #
##################################################################

ad_valid_backends = frozenset((
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

a2x_valid_formats = frozenset((
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

valid_doctypes = frozenset((
    "article",
    "manpage",
    "book",
))

#########################################
# functions that add extra dependencies #
#########################################

def ad_add_extra_deps(env, target, source, backend, doctype, conffiles):
    """Add extra dependencies to an asciidoc target."""

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
    conf_files.extend(conffiles)

    for c in conf_files:
        if os.path.isfile(c):
            env.Depends(target, c)

def get_res_entry(line, dir):
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

def a2x_add_extra_deps(env, target, source, doctype, *args):
    """Add extra dependencies to an a2x target."""

    conffile, resources, resman, flags = args

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
    conf_files.append(conffile)

    for c in conf_files:
        if os.path.isfile(c):
            env.Depends(target, c)

    # check a resource manifest file for file/dir names

    # if a resource manifest is specified, search for directories and files in
    # each line, and add them to the dependency list
    if resman:
        with open(resman) as f:
            for line in f:
                resource = get_res_entry(line, d)
                if resource:
                    env.Depends(target, resource)

    # add resource files to the dependency list

    # for each resource specified, search for directories and files, and add
    # them to the dependency list
    for res in resources:
        resource = get_res_entry(res, d)
        if resource:
            env.Depends(target, resource)

    # look for files passed in A2X_FLAGS and add them to the dependency list
    for flag in env.Split(flags):

        # handle case "--option=[sub-option=]file"
        flag = flag.split('=')

        for f in flag:
            # strip space and quotes
            f = f.strip(" \"'")
            if os.path.exists(f):
                env.Depends(target, f)

##############################
# define the pseudo-builders #
##############################

def asciidoc_builder(env, target, source, *args, **kwargs):
    """An asciidoc pseudo-builder."""

    # get overridden construction variables outside of the builder
    ad_backend   = kwargs.get('AD_BACKEND', env['AD_BACKEND'])
    ad_doctype   = kwargs.get('AD_DOCTYPE', env['AD_DOCTYPE'])
    ad_conffiles = kwargs.get('AD_CONFFILES', env['AD_CONFFILES'])

    if ad_backend not in ad_valid_backends:
        raise ValueError("Invalid AsciiDoc backend '%s'." % ad_backend)

    if ad_doctype not in valid_doctypes:
        raise ValueError("Invalid AsciiDoc doctype '%s'." % ad_doctype)

    if ad_doctype == 'book' and 'docbook' not in ad_backend:
        raise SCons.Errors.UserError(
            "Doctype 'book' only supported by docbook backends."
        )

    r = builders.asciidoc_bld(env, target, source, *args, **kwargs)

    # add extra dependencies, like conf files
    for t, s in izip(r, source):
        ad_add_extra_deps(env, t, [s], ad_backend, ad_doctype, ad_conffiles)

    return r

def a2x_builder(env, target, source, *args, **kwargs):
    """An a2x pseudo-builder."""

    # get overridden construction variables outside of the builder
    a2x_doctype = kwargs.get('A2X_DOCTYPE', env['A2X_DOCTYPE'])
    a2x_format  = kwargs.get('A2X_FORMAT', env['A2X_FORMAT'])
    keep_temp   = kwargs.get('A2X_KEEPARTIFACTS', env['A2X_KEEPARTIFACTS'])

    # get overridden construction variables used by a2x_add_extra_deps
    dep_vars = ('A2X_CONFFILE',
                'A2X_RESOURCES',
                'A2X_RESOURCEMANIFEST',
                'A2X_FLAGS')
    dep_var_vals = [kwargs.get(d, env[d]) for d in dep_vars]

    if a2x_format not in a2x_valid_formats:
        raise ValueError("Invalid A2X format '%s'." % a2x_format)

    if a2x_doctype not in valid_doctypes:
        raise ValueError("Invalid A2X doctype '%s'." % a2x_doctype)

    if a2x_format == 'manpage' and a2x_doctype != 'manpage':
        raise SCons.Errors.UserError(
            "A2X format set to 'manpage', but Doctype set to '%s'." % a2x_doctype
        )

    r = builders.a2x_bld(env, target, source, *args, **kwargs)

    # make sure to clean up intermediary files when the target is cleaned
    # NOTE: the following formats do not produce artifacts: pdf, ps, tex
    for t, s in izip(r, source):

        # docbook is the only format with one target per source
        if a2x_format == 'docbook':
            break

        # add extra dependencies, like conf files
        a2x_add_extra_deps(env, t, [s], a2x_doctype, *dep_var_vals)

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
