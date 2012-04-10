
# Some common lookup tables, etc

make_lookup = lambda d: dict((i, d[i]) for i in xrange(len(d)))
make_reverse_lookup = lambda d: dict((d[i], i) for i in xrange(len(d)))

OPCODES = "NON SET ADD SUB MUL DIV MOD SHL SHR AND BOR XOR IFE IFN IFG IFB".split(" ")

OPLOOKUP = make_lookup(OPCODES)
REVERSE_OPLOOKUP = make_reverse_lookup(OPCODES)

NONOPCODES = "RES JSR".split(" ")

NONOPLOOKUP = make_lookup(NONOPCODES)
REVERSE_NONOPLOOKUP = make_reverse_lookup(NONOPCODES)

REGISTERS = "A B C X Y Z I J".split(" ")

REGLOOKUP = make_lookup(REGISTERS)
REVERSE_REGLOOKUP = make_reverse_lookup(REGISTERS)
