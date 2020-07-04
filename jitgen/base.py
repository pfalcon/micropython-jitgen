# pycopy-jitgen - Generate machine code from Pycopy
#
# This module is part of the Pycopy https://github.com/pfalcon/pycopy
# project.
#
# Copyright (c) 2018-2020 Paul Sokolovsky
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

import uctypes


class BaseCodegen:

    def __init__(self, buf, offset=0):
        self.b = buf
        self._addr = uctypes.addressof(buf)
        self.i = offset
        self.labels = []

    def get_label(self):
        label = len(self.labels)
        self.labels.append([None])
        return label

    # Put given label at the current position in instruction stream
    def put_label(self, label):
        self.labels[label][0] = self.i

    # Mark that current position in instruction stream references label
    def ref_label(self, label):
        self.labels[label].append(self.i)

    def link_labels(self):
        # Should be implemented by subclass
        raise NotImplementedError

    def emit(self, b):
        self.b[self.i] = b
        self.i += 1

    def save(self, fname):
        with open(fname, "wb") as f:
            f.write(memoryview(self.b)[:self.i])
