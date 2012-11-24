# This file contains the builder objects used in the pseudo-builders, along with
# related code.

import SCons.Builder
import SCons.Scanner
import SCons.Script
import os
import re

#################################
# stuff common to both builders #
#################################

def ad_src_scanner_func(node, env, path):
    """Scans AsciiDoc files for implicit dependencies."""

    if not os.path.isfile(node.path):
        return []

    txt_reg = re.compile('include1{0,1}:{1,2}(.+?)\[')
    txt_files = txt_reg.findall(node.get_contents())

    img_reg = re.compile('image:{1,2}(.+?)\[')
    img_files = img_reg.findall(node.get_contents())

    return txt_files + img_files

def ad_scan_check(node, env):
    """Check whether a node should be scanned."""

    # only scan asciidoc source files (put another way, *do not* scan things
    # like image files)
    if node.path.endswith('.txt'):
        return True
    return False

ad_src_scanner = SCons.Scanner.Scanner(
    ad_src_scanner_func,
    scan_check = ad_scan_check,
    recursive = True
)

########################
# the AsciiDoc builder #
########################

ad_backend_suffix_map = {
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

def gen_ad_suffix(env, sources):
    """Generate the AsciiDoc target suffix depending on the chosen backend."""

    ad_backend = env['AD_BACKEND']

    return ad_backend_suffix_map[ad_backend]

ad_action = "${AD_ASCIIDOC} \
-b ${AD_BACKEND} \
-d ${AD_DOCTYPE} \
${AD_GET_CONF} \
${AD_GET_ATTR} \
${AD_FLAGS} \
-o ${TARGET} ${SOURCE}"

asciidoc_bld = SCons.Builder.Builder(
    action = ad_action,
    suffix = gen_ad_suffix,
    single_source = True,
    source_scanner = ad_src_scanner,
)

###################
# the A2X builder #
###################

# in the case of the manpage backend, the document should have the category as
# part of its name, e.g., "myprog.1.txt", in which case the target becomes
# "myprog.1".
a2x_backend_suffix_map = {
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

def gen_a2x_suffix(env, sources):
    """Generate the a2x target suffix depending on the chosen format."""

    a2x_format = env['A2X_FORMAT']

    return a2x_backend_suffix_map[a2x_format]

a2x_action = "${A2X_A2X} \
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

a2x_bld = SCons.Builder.Builder(
    action = a2x_action,
    suffix = gen_a2x_suffix,
    single_source = True,
    source_scanner = ad_src_scanner,
    target_factory = SCons.Script.Entry,
)