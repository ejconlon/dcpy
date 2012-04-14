#!/usr/bin/env python

translate_cases = [
(["ADD", "1",  "2"],
"""\
SET PC, :start
:op_ADD SET Z, POP
SET Y, POP
SET X, POP
ADD X, Y
SET PUSH, X
SET PC, Z
:start SET PUSH, 2
SET PUSH, 1
JSR :op_ADD
SET X, POP
:return SET PC, :return\
""".split("\n"))
]

REG = "XYIJABCZ"

def translate(statement):
    npushes = len(statement)-1
    if npushes > len(REG)-1 or npushes == 0:
        raise Exception("Bad number of arguments: "+npushes)
    op = statement[0]
    label = ":op_"+statement[0]

    yield "SET PC, :start"

    # define our operations

    yield label+" SET "+REG[-1]+", POP"
    for i in xrange(npushes):
        yield "SET "+REG[npushes-i-1]+", POP"
    yield op+" "+", ".join(REG[:npushes])
    yield "SET PUSH, "+REG[0]
    yield "SET PC, "+REG[-1]
    
    prefix = ":start "
    for i in xrange(npushes):
        yield prefix+"SET PUSH, "+statement[-i-1]
        prefix = ""
    yield "JSR "+label
    yield "SET "+REG[0]+", POP"
    yield ":return SET PC, :return"
    

def test_translate():
    for case in translate_cases:
        source, dasm = case
        gendasm = list(translate(source))
        print source
        print dasm
        print gendasm
        assert gendasm == dasm
        print "\n".join(gendasm)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            program = list(translate(f.readlines()))
            print program
            sys.exit()
    test_translate()
