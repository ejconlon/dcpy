#!/usr/bin/env python

translate_cases = [
#("(MUL (ADD 1 2) (SUB 5 3))", ""),

("(ADD 1 2)",
"""\
SET PC, :start0
:start_ADD SET Z, POP
SET X, POP
SET Y, POP
ADD X, Y
SET PUSH, X
:return_ADD SET PC, Z
:start0 SET PUSH, 2
SET PUSH, 1
JSR :start_ADD
SET X, POP
:return0 SET PC, :return0\
""".split("\n"))

,("(MUL (ADD 1 2) (SUB 5 3))",
"""\
SET PC, :start0
:start_ADD SET Z, POP
SET X, POP
SET Y, POP
ADD X, Y
SET PUSH, X
:return_ADD SET PC, Z
:start_SUB SET Z, POP
SET X, POP
SET Y, POP
SUB X, Y
SET PUSH, X
:return_SUB SET PC, Z
:start_MUL SET Z, POP
SET X, POP
SET Y, POP
MUL X, Y
SET PUSH, X
:return_MUL SET PC, Z
:start0 SET PUSH, 2
SET PUSH, 1
JSR :start_ADD
:start1 SET PUSH, 3
SET PUSH, 5
JSR :start_SUB
:start2 SET Y, POP
SET X, POP
SET PUSH, Y
SET PUSH, X
JSR :start_MUL
SET X, POP
:return0 SET PC, :return0\
""".split("\n"))
]

REG = "XYIJABCZ"

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

class Node(object):
    def __init__(self, inner=None, terminal=None):
        self.inner = inner
        self.terminal = terminal
        assert inner is None or terminal is None
        self.children = []
    def __str__(self):
        return self.nodestr()
    def __repr__(self):
        return self.nodestr()
    def nodestr(self, depth=0):
        start = '<Node>' 
        end = '</Node>'
        tabs = lambda t: "\t"*t
        s =  tabs(depth)+start+"\n"
        if self.inner is not None:
            s += tabs(depth+1)+"INNER: "+self.inner+"\n"
        if self.terminal is not None:
            s += tabs(depth+1)+"TERMINAL: "+self.terminal+"\n"
        child_strs = [child.nodestr(depth+1) for child in self.children]
        for line in child_strs:
            s += line+"\n"
        s += tabs(depth)+end
        return s
    def accept_postorder(self, visitor, depth=0):
        if self.inner is not None:
            for child in self.children:
                for item in child.accept_postorder(visitor, depth+1):
                    yield item
            for item in visitor.visit(self, depth):
                yield item

def astify(tokens, depth=0):
    tokens = iter(tokens)
    root = Node(inner="__ROOT__")
    while True:
        try:
            token = tokens.next()
            print token
            if token == "(":
                root.children.append(astify(tokens, depth+1))
                if depth == 0:
                    return root.children[0]
            elif token == ")":
                return root
            else:
                if root.inner == "__ROOT__":
                    root.inner = token
                else:
                    root.children.append(Node(terminal=token))
        except StopIteration:
            raise Exception("No closing brace")

class TranslateVisitor(object):
    def __init__(self, definitions_only):
        self.definitions_only = definitions_only
        self.defined = []
        self.index = 0

    def define(self, op, nargs):
        if nargs > len(REG)-1 or nargs == 0:
            raise Exception("Bad number of arguments: "+nargs)
        start_label = ":start_"+op
        return_label = ":return_"+op
        yield start_label+" SET "+REG[-1]+", POP"
        for i in xrange(nargs):
            yield "SET "+REG[i]+", POP"
        yield op+" "+", ".join(REG[:nargs])
        yield "SET PUSH, "+REG[0]
        yield return_label+" SET PC, "+REG[-1]

    def translate_statement(self, op, args, start_label, swap_indices):
        nargs = len(args)
        if nargs > len(REG)-1 or nargs == 0:
            raise Exception("Bad number of arguments: "+nargs)
        op_start_label = ":start_"+op
        prefix = start_label+" "
        if len(swap_indices) > 0:
            for i in reversed(swap_indices):
                yield prefix+"SET "+REG[i]+", POP"
                prefix = ""
        for i in xrange(nargs):
            if i not in swap_indices:
                yield prefix+"SET PUSH, "+args[-i-1]
            else:
                yield prefix+"SET PUSH, "+REG[nargs-i-1]
            prefix = ""
        yield "JSR "+op_start_label

    def visit(self, node, depth):
        if node.inner not in self.defined:
            op = node.inner
            args = []
            swap_indices = []
            child_index = 0
            for child in node.children:
                if child.terminal is not None:
                    args.append(child.terminal)
                else:
                    args.append(None)
                    swap_indices.append(child_index)
                child_index += 1

            if self.definitions_only:
                for item in self.define(op, len(args)):
                    self.defined.append(op)
                    yield item
            else:
                start_label = ":start"+str(self.index)
                self.index += 1
                
                for item in self.translate_statement(op, args, start_label, swap_indices):
                    yield item

def translate_ast(ast):
    # walk the tree and define everything first
    for item in ast.accept_postorder(TranslateVisitor(True)):
        yield item
    # now write the program
    for item in ast.accept_postorder(TranslateVisitor(False)):
        yield item

def translate(source):
    tokens = tokenize(source)
    prologue = ["SET PC, :start0"]
    epilogue = ["SET "+REG[0]+", POP", ":return0 SET PC, :return0"]
    
    ast = astify(tokens)
    print ast

    for item in prologue:
        yield item
    for item in translate_ast(ast):
        yield item
    for item in epilogue:
        yield item

def test_translate():
    for case in translate_cases:
        source, dasm = case
        gendasm = []
        for item in translate(source):
            print item
            gendasm.append(item)
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
