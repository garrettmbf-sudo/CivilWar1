"""Generate a minimal .sav skeleton. Use only for testing the game loader; this will NOT be a complete format until reverse-engineering completes.
"""
import argparse


def generate_minimal(path, width=10, height=10):
    # This writes a placeholder header and zeroed tile data.
    # TODO: Replace with real format once known.
    with open(path, 'wb') as f:
        f.write(b'HSAV')  # magic (placeholder)
        f.write(width.to_bytes(2, 'little'))
        f.write(height.to_bytes(2, 'little'))
        # write zeroed tile data
        f.write(bytes(width * height))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('out', help='output .sav path')
    p.add_argument('--width', type=int, default=10)
    p.add_argument('--height', type=int, default=10)
    args = p.parse_args()
    generate_minimal(args.out, args.width, args.height)
    print('Wrote', args.out)
