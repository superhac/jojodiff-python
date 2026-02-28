#!/usr/bin/env python3
"""simple Python port of JojoDiff's diff tool

This module uses Python's difflib.SequenceMatcher to compute a
binary diff between two files and emits a patch in the same format
that the original C++ ``jptch``/``jpatch`` program understands.

The algorithm is *not* identical to the C++ version; it is much simpler
and serves primarily as a convenience wrapper so that users can
produce and apply binary patches entirely from Python.

The patch format is described in ``JOutBin.cpp`` and replicated here
in the helper functions.  The companion script ``jpatch.py`` reads
and applies the patches produced by ``jdiff.py``.

Usage::

    python3 jdiff.py oldfile newfile [patchfile]

If ``patchfile`` is omitted the patch is written to stdout.

"""

import argparse
import sys
from difflib import SequenceMatcher

# control codes, mirrors values from the original C++ headers
ESC = 0xA7
MOD = 0xA6
INS = 0xA5
DEL = 0xA4
EQL = 0xA3
BKT = 0xA2


class PatchWriter:
    """Helper that emits patch operations to a file-like object."""

    def __init__(self, fobj):
        self.f = fobj
        # state used to escape data bytes exactly as the C++ writer does
        self._out_esc = False

    def _put_len(self, length: int) -> None:
        """Encode a length value using the variable-length scheme."""
        if length <= 252:
            self.f.write(bytes([length - 1]))
        elif length <= 508:
            self.f.write(bytes([252, length - 253]))
        elif length <= 0xFFFF:
            self.f.write(bytes([253, (length >> 8) & 0xFF, length & 0xFF]))
        elif length <= 0xFFFFFFFF:
            self.f.write(
                bytes([
                    254,
                    (length >> 24) & 0xFF,
                    (length >> 16) & 0xFF,
                    (length >> 8) & 0xFF,
                    length & 0xFF,
                ])
            )
        else:
            # large file support
            self.f.write(bytes([255]) + length.to_bytes(8, "big"))

    def _put_esc(self) -> None:
        self.f.write(bytes([ESC]))

    def _put_byte(self, b: int) -> None:
        """Write a single data byte, escaping as needed."""
        if self._out_esc:
            self._out_esc = False
            # if the byte could be interpreted as an operator, prefix
            # an extra ESC so the parser knows it is data
            if BKT <= b <= ESC:
                self.f.write(bytes([ESC]))
            # always write the extra ESC that signals the escape sequence
            self.f.write(bytes([ESC]))
        if b == ESC:
            # remember we just wrote an ESC so the next byte gets special
            # treatment
            self._out_esc = True
        else:
            self.f.write(bytes([b]))

    def write_eql(self, length: int) -> None:
        self._put_esc()
        self.f.write(bytes([EQL]))
        self._put_len(length)

    def write_del(self, length: int) -> None:
        self._put_esc()
        self.f.write(bytes([DEL]))
        self._put_len(length)

    def write_mod_byte(self, b: int) -> None:
        self._put_esc()
        self.f.write(bytes([MOD]))
        self._put_byte(b)

    def write_ins_byte(self, b: int) -> None:
        self._put_esc()
        self.f.write(bytes([INS]))
        self._put_byte(b)


def generate_patch(orig: bytes, new: bytes, writer: PatchWriter) -> None:
    """Build a patch for two byte sequences using SequenceMatcher."""

    sm = SequenceMatcher(None, orig, new)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            length = i2 - i1
            if length > 0:
                writer.write_eql(length)
        elif tag == "delete":
            length = i2 - i1
            if length > 0:
                writer.write_del(length)
        elif tag == "insert":
            for b in new[j1:j2]:
                writer.write_ins_byte(b)
        elif tag == "replace":
            dels = i2 - i1
            ins_bytes = new[j1:j2]
            # if there are as many replacements as deletions we output
            # MOD instructions, otherwise we emit a DEL followed by INS
            if dels == len(ins_bytes) and dels > 0:
                for b in ins_bytes:
                    writer.write_mod_byte(b)
            else:
                if dels > 0:
                    writer.write_del(dels)
                for b in ins_bytes:
                    writer.write_ins_byte(b)


def main():
    parser = argparse.ArgumentParser(description="Create a JojoDiff-style patch")
    parser.add_argument("original", help="path to original file")
    parser.add_argument("new", help="path to new file")
    parser.add_argument(
        "patch",
        nargs="?",
        help="output patch file (default stdout)",
        default="-",
    )
    args = parser.parse_args()

    with open(args.original, "rb") as fo:
        orig_bytes = fo.read()
    with open(args.new, "rb") as fn:
        new_bytes = fn.read()

    if args.patch == "-":
        writer = PatchWriter(sys.stdout.buffer)
    else:
        writer = PatchWriter(open(args.patch, "wb"))

    generate_patch(orig_bytes, new_bytes, writer)


if __name__ == "__main__":
    main()
