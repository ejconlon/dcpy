#!/usr/bin/env python

from dcpy import *

parser_cases = [
    ["SET A, 0x30", [("opname", "SET"), ("regname", "A"), ("literal", 48), ("newline", "\n")]],
    ["SUB X, [0x1000]", [("opname", "SUB"), ("regname", "X"), ("address", 0x1000), ("newline", "\n")]],
    ["SET [0x2000+I], [A]", [("opname", "SET"), ("lit+reg", (0x2000, "I")), ("regval", "A"), ("newline", "\n")]],
    ["JSR 0x28", [("opname", "JSR"), ("literal", 0x28), ("newline", "\n")]],
    ["SET POP, POP", [("opname", "SET"), ("popname", "POP"), ("popname", "POP"), ("newline", "\n")]],
    ["SET PEEK, PEEK", [("opname", "SET"), ("peekname", "PEEK"), ("peekname", "PEEK"), ("newline", "\n")]],
    ["SET PUSH, PUSH", [("opname", "SET"), ("pushname", "PUSH"), ("pushname", "PUSH"), ("newline", "\n")]],
    ["SET SP, SP", [("opname", "SET"), ("spname", "SP"), ("spname", "SP"), ("newline", "\n")]],
    ["SET PC, PC", [("opname", "SET"), ("pcname", "PC"), ("pcname", "PC"), ("newline", "\n")]],
    ["SET O, O", [("opname", "SET"), ("oname", "O"), ("oname", "O"), ("newline", "\n")]],
    ["JSR A\nJSR A", [("opname", "JSR"), ("regname", "A"), ("newline", "\n"),
                      ("opname", "JSR"), ("regname", "A"), ("newline", "\n")]]
]

def to_int(token):
    if token.startswith("0x"):
        return int(token, 16)
    else:
        return int(token)

def parse(source):
    parts = []
    for line in source.split("\n"):
        for token in line.split(" "):
            if token[-1] == ',': token = token[:-1]
            print token
            if token in REVERSE_OPLOOKUP.keys() or token in REVERSE_NONOPLOOKUP.keys():
                parts.append(("opname", token))
            elif token in REVERSE_REGLOOKUP.keys():
                parts.append(("regname", token))
            elif token == "POP":
                parts.append(("popname", "POP"))
            elif token == "PEEK":
                parts.append(("peekname", "PEEK"))
            elif token == "PUSH":
                parts.append(("pushname", "PUSH"))
            elif token == "SP":
                parts.append(("spname", "SP"))
            elif token == "PC":
                parts.append(("pcname", "PC"))
            elif token == "O":
                parts.append(("oname", "O"))
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
                    parts.append(("lit+reg", (to_int(sub[1-regindex]), sub[regindex])))
                elif token in REVERSE_REGLOOKUP.keys():
                    parts.append(("regval", token))
                else:
                    parts.append(("address", to_int(token)))
            else:
                parts.append(("literal", to_int(token)))
        parts.append(("newline", "\n"))
    return parts

def test_parser():
    for case in parser_cases:
        source, expected = case
        actual = parse(source)
        print "--------"
        print "SOURCE", source
        print "EXPECTED", expected
        print "ACTUAL  ", actual
        assert expected == actual

if __name__ == "__main__":
    test_parser()
