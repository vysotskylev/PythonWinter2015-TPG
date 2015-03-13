#!/usr/bin/python
# coding: utf

import readline
import sys
import tpg

def make_op(s):
    return {
        '+': lambda x,y: x+y,
        '-': lambda x,y: x-y,
        '*': lambda x,y: x*y,
        '/': lambda x,y: x/y,
    }[s]

class Vector(list):
    def __init__(self, *argp, **argn):
        list.__init__(self, *argp, **argn)

    def __str__(self):
        return "[" + " ".join(str(c) for c in self) + "]"

class Calc(tpg.Parser):
    r"""

    separator spaces: '\s+' ;

    token fnumber: '\d+[.]\d*' float ;
    token number: '\d+' int ;
    token op1: '[+-]' make_op ;
    token op2: '[*/]' make_op ;

    START/e -> Expr/e ;
    Expr/t -> Fact/t ( op1/op Fact/f $t=op(t,f)$ )* ;
    Fact/f -> Atom/f ( op2/op Atom/a $f=op(f,a)$ )* ;
    Atom/a -> Vector/a | fnumber/a | number/a | '\(' Expr/a '\)' ;
    Vector/$Vector(a)$ -> '\[' '\]' $a=[]$ | '\[' Atoms/a '\]' ;
    Atoms/v -> Atom/a Atoms/t $v=[a]+t$ | Atom/a $v=[a]$ ;

    """

calc = Calc()
PS1='--> '

Stop=False
while not Stop:
    line = raw_input(PS1)
    print calc(line)
