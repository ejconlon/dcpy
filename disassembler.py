#!/usr/bin/env python

import struct
from common import *

# A simple disassembler for DCPU-16 programs.

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

def pretty_one(part):
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
    elif part[0] == "data":
        return ", ".join("0x%x" % x for x in part[1])
    else:
        return "0x%x" % part[1]

def pretty_join_typed_tokens(parts):
    """ Join a stream of typed tokens into a pretty string """
    expect_op = True
    s = ""
    for part in parts:
        if part[0] == "newline":
            expect_op = True
            s = s[:-2]
            s += "\n"
        elif part[0] == "data":
            expect_op = True
            s += "DAT "+pretty_one(part)+"\n"
        elif expect_op:
            s += pretty_one(part)+" "
            expect_op = False
        else:
            s += pretty_one(part)+", "
    return s[:-1]

def lookup_value(val, iterator, offset):
    """ lookup may involve consuming the next word from the byte stream
        returns pair of (token type, token value) """
    if 0x0 <= val <= 0x7:
        return ("regname", REGLOOKUP[val], offset)
    elif 0x08 <= val <= 0x0f:
        return ("regval", REGLOOKUP[val - 0x08], offset)
    elif 0x10 <= val <= 0x17:
        return ("lit+reg", (iterator.next(), REGLOOKUP[val - 0x10]), offset + 1)
    elif val == 0x18:
        return ("popname", "POP", offset)
    elif val == 0x19:
        return ("peekname", "PEEK", offset)
    elif val == 0x1a:
        return ("pushname", "PUSH", offset)
    elif val == 0x1b:
        return ("spname", "SP", offset)
    elif val == 0x1c:
        return ("pcname", "PC", offset)
    elif val == 0x1d:
        return ("oname", "O", offset)
    elif val == 0x1e:
        return ("address", iterator.next(), offset + 1)
    elif val == 0x1f:
        return ("literal", iterator.next(), offset + 1)
    elif 0x20 <= val <= 0x3f:
        return ("literal", val - 0x20, offset)
    else:
        raise Exception("NI: 0x%x" % val)

def decompile(iterator):
    """ decompile parses a DCPU-16 program byte array into a stream of
        (type, value) entities
        yields all the typed tokens of a stream of instructions """
    iterator = iter(iterator)
    offset = 0
    try:
        while True:
            first_inst = iterator.next()
            op = OPLOOKUP[0x000f & first_inst]
            skip = False
            if op == "NON":
                skip = True
                try:
                    op = NONOPLOOKUP[(0x03f0 & first_inst) >> 4]
                except KeyError:
                    offset += 1
                    yield ("data", [first_inst], offset)
                    continue
            yield ("op", op, offset)
            if not skip:             
                val = (0x03f0 & first_inst) >> 4
                #print "%x" % val
                tup = lookup_value(val, iterator, offset)
                offset = tup[2]
                yield tup
            val2 = (0xfc00 & first_inst) >> 10
            #print "%x" % val2
            tup = lookup_value(val2, iterator, offset)
            offset = tup[2]
            yield tup
            yield ("newline", "\n", offset)
            offset += 1
    except StopIteration:
        pass

def log(x):
    """ ignore me """
    #print x
    return x

def decompile_instructions(insts):
    """ return a pretty string decomposition of the given program byte array """
    return pretty_join_typed_tokens(log(i) for i in decompile(insts))

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

def read_words(f):
    word = f.read(2)
    while word != "":
        yield struct.unpack('>H', word)[0]
        word = f.read(2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            print decompile_instructions(read_words(f))
            sys.exit()
    test_decompilation()

