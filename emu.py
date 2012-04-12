#!/usr/bin/env python

from common import *
from disassembler import read_words, decompile
from assembler import assemble

emu_cases = [
    ["SET A, 0x30", 1, lambda s: s.registers["A"] == 0x30 and s.registers["PC"] == 2],
    ["SET [0x1000], 0x20", 1, lambda s: s.memory[0x1000] == 0x20 and s.registers["PC"] == 3],
    ["SET B, 0x1\nADD B, 0x2", 2, lambda s: s.registers["B"] == 0x3 and s.registers["PC"] == 2 ],
    ["SET B, 0xffff\nADD B, 0x3", 2, lambda s: s.registers["B"] == 0x2 and s.registers["O"] == 0x1 ],
    ["SET B, 0x2\nSUB B, 0x4", 2, lambda s: s.registers["B"] == 0xfffe and s.registers["O"] == 0xffff ],
    ["SET B, 0x2\nMUL B, 0x3", 2, lambda s: s.registers["B"] == 0x6 and s.registers["O"] == 0 ],
    ["SET B, 0xdddd\nMUL B, 0xeeee", 2, lambda s: s.registers["B"] == 0xb976 and s.registers["O"] == 0xcf11 ],
    ["SET B, 0x6\nDIV B, 0x3", 2, lambda s: s.registers["B"] == 0x2 and s.registers["O"] == 0 ],
    ["SET B, 0x0\nDIV B, 0x3", 2, lambda s: s.registers["B"] == 0 and s.registers["O"] == 0 ],
    ["SET B, 0x5\nMOD B, 0x3", 2, lambda s: s.registers["B"] == 0x2 and s.registers["O"] == 0 ],
    ["SET B, 0x0\nMOD B, 0x3", 2, lambda s: s.registers["B"] == 0 and s.registers["O"] == 0 ],
    ["SET B, 0x2\nSHL B, 0x1", 2, lambda s: s.registers["B"] == 0x4 and s.registers["O"] == 0],
    ["SET B, 0x2\nSHR B, 0x1", 2, lambda s: s.registers["B"] == 0x1 and s.registers["O"] == 0]
]

class DCPU(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.registers = dict((x, 0) for x in "A B C X Y Z I J SP PC O".split())
        self.memory = [0 for x in xrange(0x10000)]
        self.registers["SP"] = 0xffff
        self.last_pc = -1
        self.skip_next = False

    def load_program(self, prog):
        i = 0
        for word in prog:
            self.memory[i] = word
            i += 1

    def __str__(self):
        s = "DCPU\n"
        s += "REGISTERS\n"
        for k,v in self.registers.iteritems():
            s += "%s\t=>\t0x%x\n" % (k, v)
        s += "MEMORY\n"
        for i in xrange(0x10000/8):
            st = i*8
            m = self.memory[st:st+8]
            if any(m):
                s += "0x%x\t%s\n" % (st, ["0x%4x" % x for x in m])
        return s

    def _raise(self, msg):
        raise Exception(msg)

    def _target(self, op, container, index, val):
        """
        0x1: SET a, b - sets a to b
        0x2: ADD a, b - sets a to a+b, sets O to 0x0001 if there's an overflow, 0x0 otherwise
        0x3: SUB a, b - sets a to a-b, sets O to 0xffff if there's an underflow, 0x0 otherwise
        0x4: MUL a, b - sets a to a*b, sets O to ((a*b)>>16)&0xffff
        0x5: DIV a, b - sets a to a/b, sets O to ((a<<16)/b)&0xffff. if b==0, sets a and O to 0 instead.
        0x6: MOD a, b - sets a to a%b. if b==0, sets a to 0 instead.
        0x7: SHL a, b - sets a to a<<b, sets O to ((a<<b)>>16)&0xffff
        0x8: SHR a, b - sets a to a>>b, sets O to ((a<<16)>>b)&0xffff
        0x9: AND a, b - sets a to a&b
        0xa: BOR a, b - sets a to a|b
        0xb: XOR a, b - sets a to a^b
        """
        if op == "SET":
            container[index] = val
        elif op == "ADD":
            container[index] += val
            if container[index] > 0xffff:
                container[index] -= 0x10000
                self.registers["O"] = 0x1
            else:
                self.registers["O"] = 0
        elif op == "SUB":
            container[index] -= val
            if container[index] < 0:
                container[index] += 0x10000;
                self.registers["O"] = 0xffff
            else:
                self.registers["O"] = 0
        elif op == "MUL":
            x = container[index] * val
            container[index] = x & 0xffff
            self.registers["O"] = (x >> 16) & 0xffff
        elif op == "DIV":
            if container[index] == 0:
                container[index] = 0
                self.registers["O"] = 0
            else:
                x = container[index] / val
                o = ((container[index] << 16) / val) & 0xffff
                container[index] = x
                self.registers["O"] = o
        elif op == "MOD":
            if container[index] == 0:
                container[index] = 0
                self.registers["O"] = 0
            else:
                container[index] %= val
        elif op == "SHL":
            x = (container[index] << val) & 0xffff
            o = ((container[index] << val) >> 16) & 0xffff
            container[index] = x
            self.registers["O"] = o
        elif op == "SHR":
            x = (container[index] >> val) & 0xffff
            o = ((container[index] << 16) >> val) & 0xffff
            container[index] = x
            self.registers["O"] = o
        elif op == "AND":
            container[index] = (container[index] & val) & 0xffff
        elif op == "BOR":
            container[index] = (container[index] | val) & 0xffff
        elif op == "XOR":
            container[index] = (container[index] ^ val) & 0xffff
        elif op not in ["IFE", "IFN", "IFG", "IFB"]:
            raise Exception("UNKNOWN OPERATION: "+op)
        return container[index]

    def _run_cond(self, ctype, a, b):
        if ctype == "IFE":
            return a == b
        elif ctype == "IFN":
            return a != b
        elif ctype == "IFG":
            return a > b
        elif ctype == "IFB":
            return (a&b) != 0
        else:
            raise Exception("Unknown op: "+ctype)

    def _push(self, value):
        self.memory[self.registers["SP"]] = value
        self.registers["SP"] -= 1

    def _pop(self):
        self.registers["SP"] += 1
        v = self.memory[self.registers["SP"]]
        return v

    def step(self):
        if self.registers["PC"] == self.last_pc:
            return False
        else:
            self.last_pc = self.registers["PC"]
        iriter = decompile(self.memory[self.registers["PC"]:])
        self.registers["PC"] += 1

        op = iriter.next()
        print "op", op

        target = iriter.next()
        print "target", target
        value = iriter.next()
        print "value", value
        setter = lambda x: self._raise("setter undefined")
        getter = lambda: self._raise("getter undefined")

        # fix our PC if we read words to get value
        self.registers["PC"] += value[-1]

        if self.skip_next:
            print "SKIPPED"
            self.skip_next = False
        elif op[1] == "JSR":
            self._push(self.registers["PC"])
            self.registers["PC"] = target[1]
        else:
            if target[0] == "regname":
                setter = lambda x: self._target(op[1], self.registers, target[1], x)
            elif target[0] == "regval":
                setter = lambda x: self._target(op[1], self.memory, self.registers[target[1]], x)
            elif target[0] == "address":
                setter = lambda x: self._target(op[1], self.memory, target[1], x)
            elif target[0] == "lit+reg":
                setter = lambda x: self._target(op[1], self.memory, self.registers[target[1][1]] + target[1][0], x)
            elif target[0] == "pcname":
                setter = lambda x: self._target(op[1], self.registers, "PC", x)
            elif target[0] == "pushname":
                self.registers["SP"] -= 1
                setter = lambda x: self._target(op[1], self.memory, self.registers["SP"]+1, x)
            else:
                raise Exception("Unknown target: "+str(target))

            if value[0] == "literal":
                getter = lambda: value[1]
            elif value[0] == "regname":
                getter = lambda: self.registers[value[1]]
            elif value[0] == "regval":
                getter = lambda: self.memory[self.registers[value[1]]]
            elif value[0] == "address":
                getter = lambda: self.memory[value[1]]
            elif value[0] == "lit+reg":
                getter = lambda: self.memory[self.registers[value[1][1]] + value[1][0]]
            elif value[0] == "popname":
                getter = lambda: self._pop()
            else:
                raise Exception("Unkown value: "+str(value))

            had_gotten = getter()
            had_set = setter(had_gotten)

            if op[1] in ["IFE", "IFN", "IFG", "IFB"]:
                cond_true = self._run_cond(op[1], had_set, had_gotten)
                if not cond_true:
                    self.skip_next = True

        return True

def run_emu(prog, steps):
    dcpu = DCPU()
    dcpu.load_program(prog)
    print "STEP 0"
    print dcpu
    for i in xrange(steps):
        print "STEP", i+1
        if not dcpu.step(): break
        print dcpu
    print dcpu
    return dcpu

def test_emu_cases():
    for case in emu_cases:
        source, steps, predicate = case
        prog = assemble(source.split("\n"))
        dcpu = run_emu(prog, steps)
        assert predicate(dcpu)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prog = None
        with open(sys.argv[1], 'rb') as f:
            prog = list(read_words(f))
        run_emu(prog, 10000)
        sys.exit()
    else:
        test_emu_cases()
