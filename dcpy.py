#!/usr/bin/env python

# A simple disassembler for DCPU-16 programs.

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

# A test table of [(instruction, expected output)]
decompilation_cases = [
    [[0x7c01, 0x0030], "SET A, 0x30"],
    [[0x7de1, 0x1000, 0x0020], "SET [0x1000], 0x20"],
    [[0x7803, 0x1000], "SUB A, [0x1000]"],
    [[0xc00d], "IFN A, 0x10"],
    [[0x7dc1, 0x002a], "SET PC, 0x2a"],
    [[0xa861], "SET I, 0xa"],
    [[0x7c01, 0x2000], "SET A, 0x2000"],
    [[0x2161, 0x2000], "SET [0x2000+I], [A]"],
    [[0x8463], "SUB I, 0x1"],
    [[0x806d], "IFN I, 0x0"],
    [[0x9031], "SET X, 0x4"],
    [[0x7c10, 0x0028], "JSR 0x28"],
    [[0x9037], "SHL X, 0x4"],
    [[0x61c1], "SET PC, POP"],
    [[0x0401], "SET A, B"],
    [[0x0c21], "SET C, X"],
    [[0x1441], "SET Y, Z"],
    [[0x1c61], "SET I, J"],
    [[0x0cb1], "SET [X], X"],
    [[0x0d31, 0x002a], "SET [0x2a+X], X"],
    [[0x6181], "SET POP, POP"],
    [[0x6591], "SET PEEK, PEEK"],
    [[0x69a1], "SET PUSH, PUSH"],
    [[0x6db1], "SET SP, SP"],
    [[0x71c1], "SET PC, PC"],
    [[0x75d1], "SET O, O"],
    [[0xfc01], "SET A, 0x1f"],
    [[0x7df1, 0xffff, 0x0020], "SET 0xffff, 0x20"],
    [[0x0010], "JSR A"],
    [[0x7c10, 0x0020], "JSR 0x20"],
    [[0x0010, 0x0010], "JSR A\nJSR A"]
]

def pretty(part):
    """ Pretty-format a typed token """
    if part[0] in set(["regname", "popname", "pcname", "peekname", "pushname", "spname", "oname", "op"]):
        return part[1]
    elif part[0] == "address":
        return "[0x%x]" % part[1]
    elif part[0] == "lit+reg":
        return "[0x%x+%s]" % part[1]
    elif part[0] == "regval":
        return "[%s]" % part[1]
    elif part[0] == "newline":
        return "\n"
    else:
        return "0x%x" % part[1]

def print_typed_tokens(parts):
    """ Join a stream of typed tokens into a pretty string """
    expect_op = True
    s = ""
    for part in parts:
        if part[0] == "newline":
            expect_op = True
            s = s[:-2]
            s += "\n"
        elif expect_op:
            s += pretty(part)+" "
            expect_op = False
        else:
            s += pretty(part)+", "
    return s[:-1]

def lookup_value(val, iterator):
    """ lookup may involve consuming the next word from the byte stream
        returns pair of (token type, token value) """
    if 0x0 <= val <= 0x7:
        return ("regname", REGLOOKUP[val])
    elif 0x08 <= val <= 0x0f:
        return ("regval", REGLOOKUP[val - 0x08])
    elif 0x10 <= val <= 0x17:
        return ("lit+reg", (iterator.next(), REGLOOKUP[val - 0x10]))
    elif val == 0x18:
        return ("popname", "POP")
    elif val == 0x19:
        return ("peekname", "PEEK")
    elif val == 0x1a:
        return ("pushname", "PUSH")
    elif val == 0x1b:
        return ("spname", "SP")
    elif val == 0x1c:
        return ("pcname", "PC")
    elif val == 0x1d:
        return ("oname", "O")
    elif val == 0x1e:
        return ("address", iterator.next())
    elif val == 0x1f:
        return ("literal", iterator.next())
    elif 0x20 <= val <= 0x3f:
        return ("literal", val - 0x20);
    else:
        raise Exception("NI: 0x%x" % val)

def decompile(iterator):
    """ decompile parses a DCPU-16 program byte array into a stream of
        (type, value) entities
        yields all the typed tokens of a stream of instructions """
    iterator = iter(iterator)
    try:
        while True:
            first_inst = iterator.next()
            op = OPLOOKUP[0x000f & first_inst]
            skip = False
            if op == "NON":
                skip = True
                op = NONOPLOOKUP[(0x03f0 & first_inst) >> 4]
            yield ("op", op)
            if not skip:             
                val = (0x03f0 & first_inst) >> 4
                #print "%x" % val
                yield lookup_value(val, iterator)
            val2 = (0xfc00 & first_inst) >> 10
            #print "%x" % val2
            yield lookup_value(val2, iterator)
            yield ("newline", "\n")
    except StopIteration:
        pass

def log(x):
    """ ignore me """
    #print x
    return x

def decompile_instructions(insts):
    """ return a pretty string decomposition of the given program byte array """
    return print_typed_tokens(log(i) for i in decompile(insts))

def test_decompilation():
    """ run our test cases """
    for case in decompilation_cases:
        instructions, expected = case
        actual = decompile_instructions(instructions)
        print "--------"
        print "PROGRAM ", instructions
        print "EXPECTED", expected
        print "ACTUAL  ", actual
        assert expected == actual

def compile(ir):
    ir = iter(ir)
    b = 0x0000;
    pos = 0
    next_words = []
    try:
        while True:
            t = ir.next()
            print t
            if t[0] == 'op':
                assert pos == 0
                num_args = 2
                if t[1] != "JSR":
                    b |= 0x00f & REVERSE_OPLOOKUP[t[1]]
                    pos += 4
                else:
                    b |= (0x03f & REVERSE_NONOPLOOKUP[t[1]]) << 4
                    pos += 10
                    num_args = 1
                for i in xrange(num_args):
                    t = ir.next()
                    print t
                    if t[0] == 'regname':
                        b |= (0x003f & REVERSE_REGLOOKUP[t[1]]) << pos
                    elif t[0] == 'regval':
                        b |= (0x003f & (REVERSE_REGLOOKUP[t[1]] + 0x8)) << pos                      
                    elif t[0] == 'lit+reg':
                        b |= (0x003f & (REVERSE_REGLOOKUP[t[1][1]] + 0x10)) << pos
                        next_words.append(t[1][0])
                    elif t[0] == 'popname':
                        b |= 0x18 << pos
                    elif t[0] == 'peekname':
                        b |= 0x19 << pos
                    elif t[0] == 'pushname':
                        b |= 0x1a << pos
                    elif t[0] == 'spname':
                        b |= 0x1b << pos
                    elif t[0] == 'pcname':
                        b |= 0x1c << pos
                    elif t[0] == 'oname':
                        b |= 0x1d << pos
                    elif t[0] == 'address':
                        b |= 0x1e << pos
                        next_words.append(t[1])
                    elif t[0] == 'literal':
                        if t[1] <= 0x1f:
                            b |= (0x003f & (t[1] + 0x20)) << pos
                        else:
                            b |= 0x1f << pos
                            next_words.append(t[1])
                    else:
                        raise Exception("NI: "+str(t))
                    pos += 6
                yield b
                for w in next_words:
                    yield w
                b = 0x0000
                pos = 0
                next_words = []
            elif t[0] != 'newline':
                raise Exception("NI: "+str(t))
    except StopIteration:
        pass

def compile_to_list(ir):
    return list(compile(ir))

def test_compilation():
    """ run our test cases """
    for case in decompilation_cases:
        expected, source = case
        ir = decompile(expected)
        actual = compile_to_list(ir)
        print "--------"
        print "SOURCE", source
        print "EXPECTED", ["0x%x" % x for x in expected]
        print "ACTUAL  ", ["0x%x" % x for x in actual]
        assert expected == actual

if __name__ == "__main__":
    test_decompilation()
    test_compilation()
