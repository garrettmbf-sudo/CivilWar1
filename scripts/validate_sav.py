"""Validate a .sav file heuristically.

This script runs basic checks (magic bytes, size vs width*height if encoded) and exits non-zero on error.
"""
import argparse
import sys


def validate(path):
    with open(path, 'rb') as f:
        data = f.read()
    if len(data) < 8:
        print('File too small to be valid')
        return 2
    magic = data[:4]
    if magic != b'HSAV':
        print('Warning: magic bytes not recognized (found', magic, ')')
    # naive width/height check if present
    try:
        width = int.from_bytes(data[4:6], 'little')
        height = int.from_bytes(data[6:8], 'little')
        expected = width * height
        actual = len(data) - 8
        if actual < expected:
            print(f'File appears truncated: expected at least {expected} tile bytes, found {actual}')
            return 3
    except Exception:
        pass
    print('Basic checks passed (note: format not fully known yet)')
    return 0

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('file')
    args = p.parse_args()
    code = validate(args.file)
    sys.exit(code)
