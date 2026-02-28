#!/usr/bin/env python3
"""Basic sanity check for the Python port.

This file is *not* a full test suite, just a simple script that
creates two small byte sequences, diffs them and patches them back.
"""

import subprocess
import sys

orig = b"Hello, world!\nThe quick brown fox jumps over the lazy dog."
new = b"Hello, world?\nThe quick brown fox jumps over the lazy dog!\n"

# include an escape byte (0xA7) in a couple of positions to ensure
# escape‑sequence handling is exercised later on
orig += bytes([0xA7, 0x01, 0x02])
new += bytes([0xA7, 0x03, 0x04])

with open("orig.bin", "wb") as f:
    f.write(orig)
with open("new.bin", "wb") as f:
    f.write(new)

# generate patch
subprocess.run([sys.executable, "python/jdiff.py", "orig.bin", "new.bin", "patch.bin"], check=True)

# apply patch
subprocess.run([sys.executable, "python/jpatch.py", "orig.bin", "patch.bin", "restored.bin"], check=True)

# compare
with open("new.bin","rb") as f:
    got = f.read()
with open("restored.bin","rb") as f:
    patched = f.read()

assert got == patched, "patched file does not match expected"
print("round-trip successful")
