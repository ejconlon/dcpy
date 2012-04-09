#!/usr/bin/env python

from dcpy import *

parser_cases = [
    ["SET A, 0x30", [("opname", "SET"), ("regname", "A"), ("literal", 48)]],
    ["SUB X, [0x1000]", [("opname", "SUB"), ("regname", "X"), ("address", 0x1000)]],
    ["SET [0x2000+I], [A]", [("opname", "SET"), ("lit+reg", (0x2000, "I")), ("regval", "A")]],
    ["JSR 0x28", [("opname", "JSR"), ("literal", 0x28)]]
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
            if token in REVERSE_OPLOOKUP.keys():
                parts.append(("opname", token))
            elif token in REVERSE_REGLOOKUP.keys():
                parts.append(("regname", token))
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
