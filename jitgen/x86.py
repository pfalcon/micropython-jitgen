# pycopy-jitgen - Generate machine code from Pycopy
#
# This module is part of the Pycopy https://github.com/pfalcon/pycopy
# project.
#
# Copyright (c) 2018 Paul Sokolovsky
#
# The MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import ffi
import uctypes

from .base import BaseCodegen


MOD_IND = 0
MOD_IND8 = 1
MOD_IND32 = 2
MOD_REG = 3

PRE_OPSIZE = 0x66
PRE_ADDRSIZE = 0x67

RET = 0xc3
MOV_R_IMM = 0xb8
PUSH_R = 0x50
POP_R = 0x58
PUSH_IMM32 = 0x68
JCOND_SHORT = 0x70
JMP_SHORT = 0xeb
JMP = 0xe9
CALL = 0xe8
#JMP_ABS = 0xea
#CALL_ABS = 0x9a
ADD = 0x01
OR  = 0x09
ADC = 0x11
SBB = 0x19
AND = 0x21
SUB = 0x29
XOR = 0x31
CMP = 0x39
ARITH_IMM8 = 0x83
ARITH_IMM32 = 0x81
ADD_IMM = 0
OR_IMM  = 1
ADC_IMM = 2
SBB_IMM = 3
AND_IMM = 4
SUB_IMM = 5
XOR_IMM = 6
CMP_IMM = 7
MOV_RM_R_32 = 0x89
MOV_R_RM_32 = 0x8b

EXT = 0xff
EXT_CALL_RM = 2


class Reg32:

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "<Reg32 %d>" % self.id


EAX = Reg32(0)
ECX = Reg32(1)
EDX = Reg32(2)
EBX = Reg32(3)
ESP = Reg32(4)
EBP = Reg32(5)
ESI = Reg32(6)
EDI = Reg32(7)


py = ffi.open(None)


class Codegen(BaseCodegen):

    def emit32(self, v):
        v &= 0xffffffff
        for i in range(4):
            self.b[self.i] = v & 0xff
            self.i += 1
            v >>= 8

    def modrm(self, mod, r_op, r_m):
        return (mod << 6) | (r_op << 3) | r_m

    def mov_imm(self, r, v):
        self.emit(MOV_R_IMM + r)
        self.emit32(v)

    def mov_rr32(self, dest_reg, src_reg):
        self.emit(MOV_R_RM_32)
        self.emit(self.modrm(MOD_REG, dest_reg, src_reg))

    def mov(self, dst, src):
        if isinstance(src, Reg32):
            self.mov_rr32(dst.id, src.id)
        elif isinstance(src, int):
            self.mov_imm(dst.id, src)
        else:
            raise NotImplementedError

    def load(self, dest_reg, base_reg, offset):
        self.emit(MOV_R_RM_32)
        self.emit(self.modrm(MOD_IND8, dest_reg.id, base_reg.id))
        self.emit(offset & 0xff)

    def ret(self):
        self.emit(RET)

    def push_r(self, r):
        self.emit(PUSH_R + r)

    def pop_r(self, r):
        self.emit(POP_R + r)

    def push_imm(self, v):
        self.emit(PUSH_IMM32)
        self.emit32(v)

    def push(self, src):
        if isinstance(src, Reg32):
            self.push_r(src.id)
        elif isinstance(src, int):
            self.push_imm(src)
        else:
            raise NotImplementedError

    def pop(self, dst):
        if isinstance(dst, Reg32):
            self.pop_r(dst.id)
        else:
            raise NotImplementedError

    def call_imm(self, v):
        self.emit(CALL)
        na = self._addr + self.i + 4
        #print(na, v, v - na)
        self.emit32(v - na)

    def call_sym(self, sym):
        p = py.addr(sym)
        #print("Addr of %s:" % sym, hex(p))
        self.call_imm(p)

    def call_r(self, r):
        self.emit(EXT)
        self.emit(self.modrm(MOD_REG, EXT_CALL_RM, r))

    def call(self, arg):
        if isinstance(arg, Reg32):
            self.call_r(arg.id)
        elif isinstance(arg, int):
            self.call_imm(arg)
        elif isinstance(arg, str):
            self.call_sym(arg)
        else:
            raise NotImplementedError

    def arith_rr32(self, op, reg1, reg2):
        self.emit(op)
        self.emit(self.modrm(MOD_REG, reg2.id, reg1.id))

    def arith_r32_imm8(self, op, reg, v):
        self.emit(ARITH_IMM8)
        self.emit(self.modrm(MOD_REG, op, reg.id))
        self.emit(v)

    def add(self, arg1, arg2):
        if isinstance(arg2, int):
            self.arith_r32_imm8(ADD_IMM, arg1, arg2)
        else:
            self.arith_rr32(ADD, arg1, arg2)

    def sub(self, arg1, arg2):
        if isinstance(arg2, int):
            self.arith_r32_imm8(SUB_IMM, arg1, arg2)
        else:
            self.arith_rr32(SUB, arg1, arg2)

    def and_(self, arg1, arg2):
        if isinstance(arg2, int):
            self.arith_r32_imm8(AND_IMM, arg1, arg2)
        else:
            self.arith_rr32(AND, arg1, arg2)

    def or_(self, arg1, arg2):
        if isinstance(arg2, int):
            self.arith_r32_imm8(OR_IMM, arg1, arg2)
        else:
            self.arith_rr32(OR, arg1, arg2)

    def pop_args(self, num_args):
        self.sub(ESP, num_args * 4)

    def prolog(self):
        self.push(EBP)
        self.mov(EBP, ESP)

    def epilog(self):
        self.pop(EBP)
        self.ret()
