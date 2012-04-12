#!/usr/bin/env python

import struct
from common import *

def calculate_label_offsets(ir):
    offsets = {}
    skews = []
    saw_newline = True
    for item in ir:
        if item[0] == "label":
            if saw_newline:
                offsets[item[1]] = item[2]
            else:
                skews.append(item[2])
        if item[0] == "newline":
            saw_newline = True
        else:
            saw_newline = False
    for key in offsets.iterkeys():
        skew = 0
        val = offsets[key]
        for pos in skews:
            if pos < val:
                skew += 1
            else:
                break
        offsets[key] += skew
    #for pair in offsets.iteritems():
    #    print pair[0], "0x%x" % pair[1]
    return offsets

def compile_ir(ir):
    """ compiles IR (list of typed tokens) to a yielded stream of bytes """
    label_offsets = calculate_label_offsets(ir)
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
                    elif t[0] == 'label':
                        b |= 0x1f << pos
                        next_words.append(label_offsets[t[1]])
                    else:
                        raise Exception("Invalid token: "+str(t))
                    pos += 6
                yield b
                for w in next_words:
                    yield w
                b = 0x0000
                pos = 0
                next_words = []
            elif t[0] not in set(["newline", "comment", "label"]):
                raise Exception("Unexpected token: "+str(t))
    except StopIteration:
        pass

def assemble(source):
    ir = list(parse(source))
    return compile_ir(ir)

from disassembler import decompilation_cases
from parser import parse

def test_compilation():
    """ run our test cases """
    for case in decompilation_cases:
        expected, source = case
        print "--------"
        print "SOURCE", source
        print "EXPECTED", ["0x%x" % x for x in expected]
        actual = list(assemble(source.split("\n")))
        print "ACTUAL  ", ["0x%x" % x for x in actual]
        assert expected == actual

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            program = list(assemble(f.readlines()))
            print ["0x%x" % x for x in program]
            if len(sys.argv) > 2:
                with open(sys.argv[2], 'wb') as g:
                    for word in program:
                        packed = struct.pack('>H', word)
                        g.write(packed)
            sys.exit()
    test_compilation()
