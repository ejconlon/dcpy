#!/usr/bin/env python

# A simple disassembler for DCPU-16 programs.
# TODO - finish to spec

make_lookup = lambda d: dict((i, d[i]) for i in xrange(len(d)))

OPCODES = "NON SET ADD SUB MUL DIV MOD SHL SHR AND BOR XOR IFE IFN IFG IFB".split(" ")

OPLOOKUP = make_lookup(OPCODES)

NONOPCODES = "RES JSR".split(" ")

NONOPLOOKUP = make_lookup(NONOPCODES)

REGISTERS = "A B C X Y Z I J".split(" ")

REGLOOKUP = make_lookup(REGISTERS)

# A test table of [(instruction, expected output)]
decomp_cases = [
    [[0x7c01, 0x0030], "SET A, 0x30"],
    [[0x7de1, 0x1000, 0x0020], "SET [0x1000], 0x20"],
    [[0x7803, 0x1000], "SUB A, [0x1000]"],
    [[0xc00d], "IFN A, 0x10"],
    [[0x7dc1, 0x001a], "SET PC, 0x1a"],
    [[0xa861], "SET I, 0xa"],
    [[0x7c01, 0x2000], "SET A, 0x2000"],
    [[0x2161, 0x2000], "SET [0x2000+I], [A]"],
    [[0x8463], "SUB I, 0x1"],
    [[0x806d], "IFN I, 0x0"],
    [[0x7dc1, 0x000d], "SET PC, 0xd"],
    [[0x9031], "SET X, 0x4"],
    [[0x7c10, 0x0018], "JSR 0x18"],
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
    [[0x7c10, 0x0020], "JSR 0x20"]
]

# Pretty-format the list of instruction parts
def clean(parts):
    cleaned = []
    for part in parts:
        if part[0] in set(["regname", "popname", "pcname", "peekname", "pushname", "spname", "oname"]):
            cleaned.append(part[1])
        elif part[0] == "address":
            cleaned.append("[0x%x]" % part[1])
        elif part[0] == "lit+reg":
            cleaned.append("[0x%x+%s]" % part[1])
        elif part[0] == "regval":
            cleaned.append("[%s]" % part[1])
        elif part[0] == "newline":
            pass
        else:
            cleaned.append("0x%x" % part[1])
    return cleaned

# Join all of the instruction parts into a pretty string
def djoin(parts):
    parts = list(parts)
    return " ".join([parts[0][1], ", ".join(clean(parts[1:]))])

# A Parser parses one instruction (for now)
class Parser(object):
    def __init__(self, inst):
        self.inst = inst
        self.word = 0

    # lookup involves some state change (advancing word index).
    # returns pair of (token type, token value)
    def lookup_value(self, val):
        if 0x0 <= val <= 0x7:
            return ("regname", REGLOOKUP[val])
        elif 0x08 <= val <= 0x0f:
            return ("regval", REGLOOKUP[val - 0x08])
        elif 0x10 <= val <= 0x17:
            self.word += 1
            return ("lit+reg", (self.inst[self.word], REGLOOKUP[val - 0x10]))
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
            self.word += 1
            return ("address", self.inst[self.word])
        elif val == 0x1f:
            self.word += 1
            return ("literal", self.inst[self.word])
        elif 0x20 <= val <= 0x3f:
            return ("literal", val - 0x20);
        else:
            raise Exception("NI: 0x%x" % val)
    
    # yields all the typed tokens of a stream of instructions
    def parse(self):
        while self.word < len(self.inst):
            first_inst = self.inst[self.word]
            op = OPLOOKUP[0x000f & first_inst]
            skip = False
            if op == "NON":
                skip = True
                op = NONOPLOOKUP[(0x03f0 & first_inst) >> 4]
            yield ("op", op)
            if not skip:             
                val = (0x03f0 & first_inst) >> 4
                print "%x" % val
                yield self.lookup_value(val)
            val2 = (0xfc00 & first_inst) >> 10
            print "%x" % val2
            yield self.lookup_value(val2)
            yield ("newline", "\n")
            self.word += 1

# ignore me
def log(x):
    print x
    return x

# return a pretty string decomposition of the given program instruction
def decomp_inst(inst):
    return djoin(log(i) for i in Parser(inst).parse())

# run our test cases
def test_decomp():
    for case in decomp_cases:
        inst, res = case
        decomp = decomp_inst(inst)
        print case, decomp
        assert res == decomp

if __name__ == "__main__":
    test_decomp()
