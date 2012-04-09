#!/usr/bin/env python

from dcpy import *

parser_cases = [
    ["SET A, 0x30", [("opname", "SET"), ("regname", "A"), ("literal", 48)]]
]

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
            else:
                if token.startswith("0x"):
                    val = int(token, 16)
                else:
                    val = int(token)
                parts.append(("literal", val))
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
