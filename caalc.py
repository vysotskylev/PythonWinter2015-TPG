#!/usr/bin/python
# coding: utf

import readline
import sys
import tpg
import itertools

def make_op(s):
    return {
        '+': lambda x,y: x+y,
        '-': lambda x,y: x-y,
        '*': lambda x,y: x*y,
        '/': lambda x,y: x/y,
        '&': lambda x,y: x&y,
        '|': lambda x,y: x|y,
    }[s]


class Promise(object):
    def get(self):
        raise NotImplementedError()

class PromMatrix(Promise):
    def __init__(self, m):
        self.m = m
    def get(self):
        return Matrix([(x.get() if isinstance(x, Promise) else x) 
                         for x in row] for row in self.m)

class PromOp(Promise):
    def __init__(self, op, *args):
        self.op = op
        self.args = args
    def get(self):
        return self.op(*(arg.get() if isinstance(arg, Promise) else arg for arg in self.args))

class PromVar(Promise):
    def __init__(self, varName):
        self.varName = varName
    def get(self):
        return Vars[self.varName]

class PromAssign(Promise):
    def __init__(self, varName, val):
        self.varName = varName
        self.val = val
    def get(self):
        Vars[self.varName] = (self.val.get() if isinstance(self.val, Promise) else self.val)


class Matrix(list):
    @staticmethod
    def __blockMatrix(M):
        s = [[((m.nrows, m.ncols) if isinstance(m, Matrix) else (1,1)) for m in row] for row in M]
        for row in s:
            for i in xrange(1, len(row)):
                if row[i][0] != row[i-1][0]: 
                    raise TypeError("Inconsistent sizes in block matrix construction")
        for j in xrange(len(s[0])):
            for i in xrange(1,len(s)):
                if s[i][j][1] != s[i-1][j][1]:
                    raise TypeError("Inconsistent sizes in block matrix construction")
        nrows = sum(row[0][0] for row in s)
        ncols = sum(x[1] for x in s[0])
        new = [[] for  i in xrange(nrows)]
        offi = 0
        for rowidx, row in enumerate(M):
            for m in row:
                if isinstance(m, Matrix):
                    for i, row in enumerate(m):
                        new[offi + i].extend(row)
                else:
                    new[offi].append(m)
            offi += s[rowidx][0][0]
        return new

    def __init__(self, *argp, **argn):
        list.__init__(self, *argp, **argn)
        if len(self) != 0:
            for row in self:
                if len(row) != len(self[0]):
                    raise TypeError("Rows must have equal lengths")
            list.__init__(self, Matrix.__blockMatrix(self))
            self.nrows = len(self)
            self.ncols = len(self[0])
        else:
            self.nrows = self.ncols = 0
    def __str__(self):
        widths = [max(len(str(self[i][j])) for i in xrange(self.nrows)) for j in xrange(self.ncols)]
        fmt = " ".join(" {:>" + str(w) + "}" for w in widths)
        return "[" + ";\n ".join(fmt.format(*row) for row in self) + " ]"

    def __elwiseop(self, a, op):
        if self.nrows != a.nrows or self.ncols != a.ncols:
            raise TypeError("Matrices must be of equal sizes, given {}x{} and {}x{}".format(self.nrows, self.ncols, a.nrows, a.ncols))
        return Matrix([op(x, y) for x,y in zip(row1, row2)] for row1, row2 in zip(self, a))

    def __add__(self, a): return self.__elwiseop(a, lambda c,d: c+d)
    def __sub__(self, a): return self.__elwiseop(a, lambda c,d: c-d)
    def __mul__(self, a): 
        if self.ncols != a.nrows:
            raise TypeError("Inconsistent matrix sizes: {}x{} and {}x{}".format(self.nrows, self.ncols, a.nrows, a.ncols))
        return Matrix([sum(self[i][j] * a[j][k] for j in xrange(self.ncols)) 
                        for k in xrange(a.ncols)]
                      for i in xrange(self.nrows))

class Calc(tpg.Parser):
    r"""

    separator spaces: '\s+' ;
    separator comment: '#.*' ;

    token fnumber: '\d+[.]\d*' float ;
    token number: '\d+' int ;
    token op1: '[+-]' make_op ;
    token op2: '[*/]' make_op ;
    token id: '\w+' ;

    START/e -> Operator $e=None$ | Expr/e | $e=None$ ;
    Operator -> Assign | FuncDecl;
    FuncDecl -> 'fun' ;
    Assign -> id/i '=' Expr/e $Vars[i]=(e.get() if isinstance(e, Promise) else e) $ ;
    Expr/t -> Fact/t ( op1/op Fact/f $t=PromOp(op, t,f)$ )* ;
    Fact/f -> Atom/f ( op2/op Atom/a $f=PromOp(op, f,a)$ )* ;
    Atom/a ->   Matrix/a
              | id/i  $a=PromVar(i)$
              | fnumber/a
              | number/a
              | '\(' Expr/a '\)' ;
    Matrix/$PromMatrix(a)$ -> '\[' '\]' $a=[]$ | '\[' Lines/a '\]' ;
    Lines/l -> Atoms/v ';' Lines/l $l=[v]+l$ | Atoms/v $l=[v]$ ;
    Atoms/v -> Atom/a Atoms/t $v=[a]+t$ | Atom/a $v=[a]$ ;

    """

calc = Calc()
Vars={}
PS1='--> '

if len(sys.argv) == 2: 
    # It's script file
    with open(sys.argv[1], 'r') as f:
        linesIter = iter(f.readlines())
    def get_line():
        try:
            return linesIter.next()
        except:
            raise EOFError
elif len(sys.argv) == 1:
    def get_line():
        return raw_input(PS1)

Stop=False
while not Stop:
    try:
        line = get_line()
        try:
            res = calc(line)
        except tpg.Error as exc:
            print >> sys.stderr, exc
            res = None
        if res != None:
            print res.get()
    except EOFError:
        Stop = True
        print 
