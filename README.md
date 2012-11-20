# An SCons Tool for AsciiDoc
Marc Joliet <marcec@gmx.de>

## Introduction

This is an SCons extension (more precisely, a tool) for compiling AsciiDoc
documents to various formats using the `asciidoc` and `a2x` programs.  It adds
two appropriate builders, `AsciiDoc` and `A2X`, to your env.  Their behaviour
can be modified using corresponding environment variables (see "Usage" below).

Please keep in mind that this SCons tool is still under (heavy) development,
lacks a test suite, and does not handle all cases (yet).

## Installation

The SCons AsciiDoc tool depends on the obvious:

- Python (2.5 or newer)
- SCons
- AsciiDoc (with all its dependencies, depending on what output you want)

If you use git, installation is easy: you can just add this repository as a git
submodule in the `site_scons/site_tools` directory, e.g., in `asciidoc`.

If you don't use git, copy the repository to your projects
`site_scons/site_tools` directory into a subdirectory with a sensible name,
e.g., in `asciidoc`.

## Usage

Use this as you would any other SCons extension: add it to the `tools` argument
of Environment(), for example:

    env = Environment(tools = ['default', 'asciidoc'])

To compile an AsciiDoc source file, use the builder AsciiDoc(), like so:

    docs = env.AsciiDoc(["readme.txt"])

To manipulate the behaviour of the builders, you can specify the following
environment variables:

- `ASCIIDOC`          -> the name of the `asciidoc` executable
- `ASCIIDOCFLAGS`     -> misc. flags passed to `asciidoc`
- `ASCIIDOCBACKEND`   -> the backend passed to the `-b` option
- `ASCIIDOCDOCTYPE`   -> the document type passed to the `-d` option
- `A2X`               -> the name of the `a2x` executable
- `A2XFLAGS`          -> misc. flags passed to `a2x`
- `A2XFORMAT`         -> the format passed to the `-f` option
- `A2XDOCTYPE`        -> the document type passed to the `-d` option

## Related Software

You could combine the AsciiDoc builder with the
[SCons DocBook tool](https://bitbucket.org/dirkbaechle/scons_docbook) by Dirk
Baechle as an alternative to using the A2X builder.  I've been meaning to try
this myself.

## License

See the file LICENSE.
