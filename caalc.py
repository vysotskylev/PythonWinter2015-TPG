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

class Vector(list):
    def __init__(self, *argp, **argn):
        list.__init__(self, *argp, **argn)

    def __str__(self):
        return "[" + " ".join(str(c) for c in self) + "]"

    def __op(self, a, op):
        try:
            return self.__class__(op(s,e) for s,e in zip(self, a))
        except TypeError:
            return self.__class__(op(c,a) for c in self)

    def __add__(self, a): return self.__op(a, lambda c,d: c+d)
    def __sub__(self, a): return self.__op(a, lambda c,d: c-d)
    def __div__(self, a): return self.__op(a, lambda c,d: c/d)
    def __mul__(self, a): return self.__op(a, lambda c,d: c*d)

    def __and__(self, a):
        try:
            return reduce(lambda s, (c,d): s+c*d, zip(self, a), 0)
        except TypeError:
            return self.__class__(c and a for c in self)

    def __or__(self, a):
        try:
            return self.__class__(itertools.chain(self, a))
        except TypeError:
            return self.__class__(c or a for c in self)

class Matrix(list):
    def __init__(self, *argp, **argn):
        list.__init__(self, *argp, **argn)
        if len(self) != 0:
            for row in self:
                if len(row) != len(self[0]):
                    raise TypeError("Rows must have equal lengths")
            self.nrows = len(self)
            self.ncols = len(self[0])
        else:
            self.nrows = self.ncols = 0
    def __str__(self):
        return "[" + " ".join(str(c) for c in self) + "]"

    def __op(self, a, op):
        try:
            return self.__class__(op(s,e) for s,e in zip(self, a))
        except TypeError:
            return self.__class__(op(c,a) for c in self)

    def __add__(self, a): return self.__op(a, lambda c,d: c+d)
    def __sub__(self, a): return self.__op(a, lambda c,d: c-d)
    def __mul__(self, a): 
        if self.ncols != a.nrows:
            raise TypeError("Inconsistent matrix sizes: {}x{} and {}x{}".format(self.nrows, self.ncols, a.nrows, a.ncols))
        res = list(
                list(
                    sum(self[i][j] * a[j][k] for j in xrange(self.ncols)) 
                    for k in xrange(a.ncols)
                ) for i in xrange(self.nrows))
        return self.__class__(res) 
    def __and__(self, a):
        try:
            return reduce(lambda s, (c,d): s+c*d, zip(self, a), 0)
        except TypeError:
            return self.__class__(c and a for c in self)

    def __or__(self, a):
        try:
            return self.__class__(itertools.chain(self, a))
        except TypeError:
            return self.__class__(c or a for c in self)

class Calc(tpg.Parser):
    r"""

    separator spaces: '\s+' ;
    separator comment: '#.*' ;

    token fnumber: '\d+[.]\d*' float ;
    token number: '\d+' int ;
    token op1: '[|&+-]' make_op ;
    token op2: '[*/]' make_op ;
    token id: '\w+' ;

    START/e -> Operator $e=None$ | Expr/e | $e=None$ ;
    Operator -> Assign ;
    Assign -> id/i '=' Expr/e $Vars[i]=e$ ;
    Expr/t -> Fact/t ( op1/op Fact/f $t=op(t,f)$ )* ;
    Fact/f -> Atom/f ( op2/op Atom/a $f=op(f,a)$ )* ;
    Atom/a ->   Matrix/a
              | id/i ( check $i in Vars$ | error $"Undefined variable '{}'".format(i)$ ) $a=Vars[i]$
              | fnumber/a
              | number/a
              | '\(' Expr/a '\)' ;
    Matrix/$Matrix(a)$ -> '\[' '\]' $a=[]$ | '\[' Lines/a '\]' ;
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
            print res
    except EOFError:
        Stop = True
        print 
