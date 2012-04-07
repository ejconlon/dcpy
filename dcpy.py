#!/usr/bin/env python

make_lookup = lambda d: dict((i, d[i]) for i in xrange(len(d)))

OPCODES = "NON SET ADD SUB MUL DIV MOD SHL SHR AND BOR XOR IFE IFN IFG IFB".split(" ")

OPLOOKUP = make_lookup(OPCODES)

NONOPCODES = "RES JSR".split(" ")

NONOPLOOKUP = make_lookup(NONOPCODES)

CYCLES = {
    1: "SET AND BOR XOR".split(" "),
    2: "ADD SUB MUL SHR SHL IFE IFN IFG IFB".split(" "),
    3: "DIV MOD".split(" ")
}

REGISTERS = "A B C X Y Z I J".split(" ")

REGLOOKUP = make_lookup(REGISTERS)

decomp_cases = [
    [[0x7c01, 0x0030], "SET A, 0x30"],
    [[0x7de1, 0x1000, 0x0020], "SET [0x1000], 0x20"],
    [[0x7803, 0x1000], "SUB A, [0x1000]"],
    [[0xc00d], "IFN A, 0x10"],
    [[0x7dc1, 0x001a], "SET PC, 0x1a"],
    [[0xa861], "SET I, 0xa"],
    [[0x7c01, 0x2000], "SET A, 0x2000"]
]

def clean(parts):
    cleaned = []
    for part in parts:
        if type(part[1]) == str:
            cleaned.append(part[1])
        elif part[0] == "address":
            cleaned.append("[0x%x]" % part[1])
        else:
            cleaned.append("0x%x" % part[1])
    return cleaned

def djoin(parts):
    parts = list(parts)
    return " ".join([parts[0][1], ", ".join(clean(parts[1:]))])

class Parser(object):
    def __init__(self, inst):
        self.inst = inst
        self.word = 0

    def lookup_value(self, val):
        if val in REGLOOKUP:
            return ("regname", REGLOOKUP[val])
        elif val == 0x1c:
            return ("pcname", "PC")
        elif val == 0x1f:
            self.word += 1
            return ("literal", self.inst[self.word])
        elif val == 0x1e:
            self.word += 1
            return ("address", self.inst[self.word])
        elif 0x20 <= val <= 0x3f:
            return ("literal", val - 0x20);
        else:
            raise Exception("NI: 0x%x" % val)
    
    def parse(self):
        op = OPLOOKUP[0x000f & self.inst[0]]
        yield ("op", op)
        val = (0x03f0 & self.inst[0]) >> 4
        print "%x" % val
        yield self.lookup_value(val)
        val2 = (0xfc00 & self.inst[0]) >> 10
        print "%x" % val2
        yield self.lookup_value(val2)

def log(x):
    print x
    return x

def decomp_inst(inst):
    return djoin(log(i) for i in Parser(inst).parse())

def test_decomp():
    for case in decomp_cases:
        inst, res = case
        decomp = decomp_inst(inst)
        print case, decomp
        assert res == decomp

def main():
    test_decomp()

if __name__ == "__main__":
    main()
