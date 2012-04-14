#!/usr/bin/env python

translate_cases = [
("(ADD 1 2)",
"""\
SET PC, :start
:op_ADD SET Z, POP
SET X, POP
SET Y, POP
ADD X, Y
SET PUSH, X
SET PC, Z
:start SET PUSH, 2
SET PUSH, 1
JSR :op_ADD
SET X, POP
:return SET PC, :return\
""".split("\n"))

#,("(MUL (ADD 1 2) (SUB 5 3))",
#"""\
#""".split("\n"))
]

REG = "XYIJABCZ"

########
def tokenize(stream):
    in_comment = False
    last = []
    for c in stream:
        if in_comment:
            if c == "\n":
                in_comment = False
                if len(last) > 0:
                    yield "".join(last)
                    last = []
        elif c == ";":
            in_comment = True
        elif c == " " or c == "\t" or c == "\n":
            if len(last) > 0:
                yield "".join(last)
                last = []
        elif c == "(" or c == ")":
            if len(last) > 0: 
                yield "".join(last)
                last = []
            yield c
        else:
            last.append(c)
    if len(last) > 0:
        yield "".join(last)

def is_balanced(tokens):
    depth = 0
    for t in tokens:
        if t == "(":
            depth += 1
        elif t == ")":
            depth -= 1
    return depth == 0

def is_valid(tokens):
    return tokens[0]  == "(" and \
           tokens[-1] == ")" and \
           len(tokens) >= 2 and \
           is_balanced(tokens)
#######

def translate_statement(statement):
    npushes = len(statement)-1
    if npushes > len(REG)-1 or npushes == 0:
        raise Exception("Bad number of arguments: "+npushes)

    op = statement[0]
    label = ":op_"+statement[0]

    yield label+" SET "+REG[-1]+", POP"
    for i in xrange(npushes):
        yield "SET "+REG[i]+", POP"
    yield op+" "+", ".join(REG[:npushes])
    yield "SET PUSH, "+REG[0]
    yield "SET PC, "+REG[-1]
    
    prefix = ":start "
    for i in xrange(npushes):
        yield prefix+"SET PUSH, "+statement[-i-1]
        prefix = ""
    yield "JSR "+label
    
def translate_tokens(tokens):
    tokens = iter(tokens)
    statement = []
    while True:
        try:
            token = tokens.next()
            if token == "(":
                translate_tokens(tokens)
            elif token == ")":
                for item in translate_statement(statement):
                    yield item
                return
            else:
                statement.append(token)
        except StopIteration:
            raise Exception("No closing brace")

def translate(source):
    tokens = tokenize(source)
    prologue = ["SET PC, :start"]
    epilogue = ["SET "+REG[0]+", POP", ":return SET PC, :return"]
    
    for item in prologue:
        yield item
    for item in translate_tokens(tokens):
        yield item
    for item in epilogue:
        yield item

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
