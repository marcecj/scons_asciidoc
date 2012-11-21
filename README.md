# An SCons Tool for AsciiDoc
Marc Joliet <marcec@gmx.de>

## Introduction

This is an SCons tool for compiling AsciiDoc documents to various formats using
the `asciidoc` and `a2x` programs.  It adds two appropriate builders, `AsciiDoc`
and `A2X`, to your env.  Their behaviour can be modified using various
construction variables (see "Usage" below).

Please keep in mind that this SCons tool is still under (heavy) development,
lacks a test suite, and does not handle all cases (yet).

## Installation

The SCons AsciiDoc tool depends on the obvious:

- Python (2.4 or newer)
- SCons
- AsciiDoc (with all its dependencies, depending on what output you want)

If you use git, installation is easy: you can just add this repository as a git
submodule in the `site_scons/site_tools` directory in `asciidoc`.

If you don't use git, you can copy the repository into your projects
`site_scons/site_tools` directory into a subdirectory named `asciidoc`.
Alternatively, you could clone the repository into
`$HOME/.scons/site_scons/site_tools`, again, into a subdirectory named
`asciidoc`.

## Usage

Use this as you would any other SCons tool: add it to the `tools` argument of
Environment(), for example:

    env = Environment(tools = ['default', 'asciidoc'])

To compile an AsciiDoc source file, you can use either the `AsciiDoc()` or the
`A2X()` builder:

    docs = env.AsciiDoc(['readme.txt'])
    pdf  = env.A2X(['readme.txt'])

Note that due to the nature of the `a2x` program (you cannot specify the output
file name), specifying the target of the `A2X` builder only changes the
output directory (the `a2x` `-D` option).  Regardless, the combination of this
builder and variant directories should work.

To manipulate the behaviour of the builders, you can specify the following
construction variables (variables for internal use are not listed here):

- `AD_ASCIIDOC`  -> the name of the `asciidoc` executable
- `AD_FLAGS`     -> miscellaneous flags passed to `asciidoc`
- `AD_BACKEND`   -> the backend passed via the `-b` option
- `AD_DOCTYPE`   -> the document type passed via the `-d` option
- `AD_CONFFILES` -> a list of configuration files passed via the `-f` option
- `A2X_A2X`      -> the name of the `a2x` executable
- `A2X_FLAGS`    -> miscellaneous flags passed to `a2x`
- `A2X_FORMAT`   -> the format passed via the `-f` option
- `A2X_DOCTYPE`  -> the document type passed via the `-d` option
- `A2X_CONFFILE` -> a configuration file passed via the `--conf-file` option

Finally, there is also a variable `A2X_KEEPARTIFACTS`, which defines whether
build artifacts should be deleted by `a2x` or not.  This variable sets the `a2x`
`-k` option when true (the default).  This should normally not need to be
modified, but *can* be, "just in case."

To override these variables for individual source files, SCons lets you pass
construction variables as keyword arguments to builders.  For example, to build
one document as a website and another as a manpage, you can do the following:

    web = env.AsciiDoc(['website.txt'], AD_BACKEND='html5')
    # man.path is 'prog.1'
    man = env.A2X(['prog.1.txt'],
                  AD_BACKEND='manpage', AD_DOCTYPE='manpage')

As can be seen here, in the case of the manpage backend, the document should
have the category as part of its name, as the target file name is identical to
the source file name without the suffix (a consequence of the `a2x` limitation
mentioned above).

Furthermore, the tool adds the construction variables `AD_VERSION` and
`A2X_VERSION`.  For this to work in the case of non-standard executable
locations, you can set the `AD_ASCIIDOC` and `A2X_A2X` construction variables at
environment initialisation time, e.g.:

    env = Environment(AD_ASCIIDOC='/path/to/asciidoc'
                      tools = ['default', 'asciidoc'])

This is especially handy in combination with the SCons `ARGUMENTS` dictionary.
A generic way to handle this might be to do something like following:

    extra_kwargs = {}
    for k, v in ARGUMENTS.iteritems():
        if k == 'AD_ASCIIDOC' and v:
            extra_kwargs[k] = v
        elif k == 'A2X_A2X' and v:
            extra_kwargs[k] = v

    env = Environment(tools = ['default', 'asciidoc'], **extra_kwargs)

## Related Software

You could combine the `AsciiDoc()` builder with the
[SCons DocBook tool](https://bitbucket.org/dirkbaechle/scons_docbook) by Dirk
Bächle as an alternative to using the `A2X` builder.

## License

See the file LICENSE.
