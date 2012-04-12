#!/usr/bin/env python

from dcpy import *

parser_cases = [
    ["SET A, 0x30", [("op", "SET", 0), ("regname", "A", 0), ("literal", 48, 1), ("newline", "\n", 1)]],
    ["SUB X, [0x1000]", [("op", "SUB", 0), ("regname", "X", 0), ("address", 0x1000, 1), ("newline", "\n", 1)]],
    ["SET [0x2000+I], [A]", [("op", "SET", 0), ("lit+reg", (0x2000, "I"), 1), ("regval", "A", 1), ("newline", "\n", 1)]],
    ["JSR 0x28", [("op", "JSR", 0), ("literal", 0x28, 1), ("newline", "\n", 1)]],
    ["JSR 0x04", [("op", "JSR", 0), ("literal", 0x04, 0), ("newline", "\n", 0)]],
    ["SET POP, POP", [("op", "SET", 0), ("popname", "POP", 0), ("popname", "POP", 0), ("newline", "\n", 0)]],
    ["SET PEEK, PEEK", [("op", "SET", 0), ("peekname", "PEEK", 0), ("peekname", "PEEK", 0), ("newline", "\n", 0)]],
    ["SET PUSH, PUSH", [("op", "SET", 0), ("pushname", "PUSH", 0), ("pushname", "PUSH", 0), ("newline", "\n", 0)]],
    ["SET SP, SP", [("op", "SET", 0), ("spname", "SP", 0), ("spname", "SP", 0), ("newline", "\n", 0)]],
    ["SET PC, PC", [("op", "SET", 0), ("pcname", "PC", 0), ("pcname", "PC", 0), ("newline", "\n", 0)]],
    ["SET O, O", [("op", "SET", 0), ("oname", "O", 0), ("oname", "O", 0), ("newline", "\n", 0)]],
    ["JSR A\nJSR A", [("op", "JSR", 0), ("regname", "A", 0), ("newline", "\n", 0),
                      ("op", "JSR", 1), ("regname", "A", 1), ("newline", "\n", 1)]],
    [":stop JSR stop", [("label", "stop", 0), ("op", "JSR", 0), ("label", "stop", 0), ("newline", "\n", 0)]],
    ["; comment SET X, asdf\n; another", [("comment", "; comment SET X, asdf", 0), ("newline", "\n", 0),
                                          ("comment", "; another", 0), ("newline", "\n", 0)]]
    #["DAT \"hello, world!\", 0", [("data", [ord(c) for c in "hello, world!"] + [0])]]
]

def to_int(token):
    if token.startswith("0x"):
        return int(token, 16)
    else:
        return int(token)

def parse(source):
    offset = 0
    for line in source:
        saw_op = False
        for token in line.strip().split(" "):
            if len(token) == 0:
                continue
            if token[-1] == ',': token = token[:-1]
            #print "TOKEN", token
            if token[0] == ':':
                yield ("label", token[1:], offset)
            elif token[0] == ';':
                yield ("comment", line[line.index(';'):], offset)
                break
            elif token in REVERSE_OPLOOKUP.keys() or token in REVERSE_NONOPLOOKUP.keys():
                saw_op = True
                yield ("op", token, offset)
            elif token in REVERSE_REGLOOKUP.keys():
                yield ("regname", token, offset)
            elif token == "POP":
                yield ("popname", "POP", offset)
            elif token == "PEEK":
                yield ("peekname", "PEEK", offset)
            elif token == "PUSH":
                yield ("pushname", "PUSH", offset)
            elif token == "SP":
                yield ("spname", "SP", offset)
            elif token == "PC":
                yield ("pcname", "PC", offset)
            elif token == "O":
                yield ("oname", "O", offset)
            elif token.startswith("[") and token.endswith("]"):
                token = token[1:-1]
                if "+" in token:
                    sub = [x.strip() for x in token.split('+')]
                    assert len(sub) == 2
                    regindex = 0
                    for x in sub:
                        if len(x) == 1 and x.isalpha():
                            break
                        regindex += 1
                    assert regindex < 2
                    offset += 1
                    yield ("lit+reg", (to_int(sub[1-regindex]), sub[regindex]), offset)
                elif token in REVERSE_REGLOOKUP.keys():
                    yield ("regval", token, offset)
                else:
                    offset += 1
                    yield ("address", to_int(token), offset)
            elif token[0].isalpha():
                yield ("label", token, offset)
            else:
                val = to_int(token)
                if val > 0x1f:
                    offset += 1
                yield ("literal", val, offset)
        yield ("newline", "\n", offset)
        if saw_op: offset += 1

def test_parser():
    for case in parser_cases:
        source, expected = case
        actual = list(parse(source.split("\n")))
        print "--------"
        print "SOURCE", source
        print "EXPECTED", expected
        print "ACTUAL  ", actual
        assert expected == actual

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            print list(parse(f.readlines()))
            sys.exit()
    test_parser()
