"""Small helper scripts for initial binary inspection of Hex of Steel .sav files.

These are intentionally small and dependency-light. They are not full parsers — they help with reverse engineering.
"""
import argparse
import binascii


def hexdump(data, width=16):
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hexbytes = ' '.join(f"{b:02X}" for b in chunk)
        ascii_rep = ''.join((chr(b) if 32 <= b < 127 else '.') for b in chunk)
        print(f"{i:08X}  {hexbytes:<{width*3}}  |{ascii_rep}|")


def dump_header(path, length=256):
    with open(path, 'rb') as f:
        data = f.read(length)
    print(f"== File: {path} (first {length} bytes) ==")
    hexdump(data)
    print('\n== ASCII scan ==')
    try:
        print(data.decode('ascii', errors='replace'))
    except Exception:
        pass


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Dump header bytes from a .sav file')
    p.add_argument('file', help='path to .sav file')
    p.add_argument('--len', type=int, default=256, help='how many bytes to dump')
    args = p.parse_args()
    dump_header(args.file, args.len)
