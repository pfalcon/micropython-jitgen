from jitgen import alloc_exec
from jitgen.x86 import *


b = alloc_exec(16)

c = Codegen(b)
c.prolog()
c.load(EAX, EBP, 8)
c.load(EBX, EBP, 12)
c.add(EAX, EBX)
c.epilog()

addr = uctypes.addressof(b)
f = ffi.func("i", addr, "ii")

print("result:", f(1, 2))
