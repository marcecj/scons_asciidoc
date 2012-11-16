def generate(env):

    asciidoc = env.Builder(action = ['asciidoc ${ASCIIDOCFLAGS} -o ${TARGET} ${SOURCE}'],
                           suffix = '.html',
                           single_source = True)

    a2x = env.Builder(action = ['a2x $A2XFLAGS ${SOURCE}'],
                      suffix = 'pdf',
                      single_source = True)

    env['BUILDERS']['AsciiDoc'] = asciidoc
    env['BUILDERS']['A2X']      = a2x

def exists(env):
    if not env.WhereIs("asciidoc"):
        return False
    return True
