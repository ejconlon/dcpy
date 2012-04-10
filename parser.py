#!/usr/bin/env python

from dcpy import *

parser_cases = [
    ["SET A, 0x30", [("op", "SET"), ("regname", "A"), ("literal", 48), ("newline", "\n")]],
    ["SUB X, [0x1000]", [("op", "SUB"), ("regname", "X"), ("address", 0x1000), ("newline", "\n")]],
    ["SET [0x2000+I], [A]", [("op", "SET"), ("lit+reg", (0x2000, "I")), ("regval", "A"), ("newline", "\n")]],
    ["JSR 0x28", [("op", "JSR"), ("literal", 0x28), ("newline", "\n")]],
    ["SET POP, POP", [("op", "SET"), ("popname", "POP"), ("popname", "POP"), ("newline", "\n")]],
    ["SET PEEK, PEEK", [("op", "SET"), ("peekname", "PEEK"), ("peekname", "PEEK"), ("newline", "\n")]],
    ["SET PUSH, PUSH", [("op", "SET"), ("pushname", "PUSH"), ("pushname", "PUSH"), ("newline", "\n")]],
    ["SET SP, SP", [("op", "SET"), ("spname", "SP"), ("spname", "SP"), ("newline", "\n")]],
    ["SET PC, PC", [("op", "SET"), ("pcname", "PC"), ("pcname", "PC"), ("newline", "\n")]],
    ["SET O, O", [("op", "SET"), ("oname", "O"), ("oname", "O"), ("newline", "\n")]],
    ["JSR A\nJSR A", [("op", "JSR"), ("regname", "A"), ("newline", "\n"),
                      ("op", "JSR"), ("regname", "A"), ("newline", "\n")]],
    [":stop JSR stop", [("label", "stop"), ("op", "JSR"), ("label", "stop"), ("newline", "\n")]],
    ["; comment SET X, asdf", [("comment", "; comment SET X, asdf"), ("newline", "\n")]]
]

def to_int(token):
    if token.startswith("0x"):
        return int(token, 16)
    else:
        return int(token)

def parse(source):
    for line in source:
        for token in line.strip().split(" "):
            if len(token) == 0:
                continue
            if token[-1] == ',': token = token[:-1]
            #print "TOKEN", token
            if token[0] == ':':
                yield ("label", token[1:])
            elif token[0] == ';':
                yield ("comment", line[line.index(';'):])
                break
            elif token in REVERSE_OPLOOKUP.keys() or token in REVERSE_NONOPLOOKUP.keys():
                yield ("op", token)
            elif token in REVERSE_REGLOOKUP.keys():
                yield ("regname", token)
            elif token == "POP":
                yield ("popname", "POP")
            elif token == "PEEK":
                yield ("peekname", "PEEK")
            elif token == "PUSH":
                yield ("pushname", "PUSH")
            elif token == "SP":
                yield ("spname", "SP")
            elif token == "PC":
                yield ("pcname", "PC")
            elif token == "O":
                yield ("oname", "O")
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
                    yield ("lit+reg", (to_int(sub[1-regindex]), sub[regindex]))
                elif token in REVERSE_REGLOOKUP.keys():
                    yield ("regval", token)
                else:
                    yield ("address", to_int(token))
            elif token[0].isalpha():
                yield ("label", token)
            else:
                yield ("literal", to_int(token))
        yield ("newline", "\n")

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
