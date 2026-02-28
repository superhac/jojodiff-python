# Python port of JojoDiff

This folder contains a minimal Python reimplementation of the core
functionality of the original `jdiff` / `jpatch` C++ utilities.

Two command‑line scripts are included:

* `jdiff.py` – computes a binary patch between two files
* `jpatch.py` – applies a patch to an original file to recreate the
  modified version

The patch format produced is compatible with the original C++
implementation, although the diff algorithm in `jdiff.py` is much
simpler (it uses `difflib.SequenceMatcher` and therefore may produce
larger patches).

## Usage

```bash
python3 python/jdiff.py old.bin new.bin > diff.jdf
python3 python/jpatch.py old.bin diff.jdf restored.bin
```

Both scripts accept `-` as an argument to read from or write to
standard input/output.

The Python code is provided for convenience and learning; for large
files or high performance you may still prefer to compile the original
C++ program using the top–level `Makefile`.
