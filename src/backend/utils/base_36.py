import sys

basedigits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
BASE = len(basedigits)


def decode(s):
    ret, mult = 0, 1
    for c in reversed(s):
        ret += mult*basedigits.index(c)
        mult *= BASE
    return ret


def encode(num):
    if num < 0:
        raise Exception("positive number "+num)
    if num == 0:
        return '0'
    ret = ''
    while num != 0:
        ret = (basedigits[num % BASE]) + ret
        num = int(num/BASE)
    return ret


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: base_36.py <num>...")
        sys.exit(1)
    width = max(len(x) for x in sys.argv[1:])
    for argv in sys.argv[1:]:
        try:
            num = int(argv)
            print('%*s %s %s' % (width, argv, 'ENCODE', encode(num)))
        except ValueError:
            print('%*s %s %s' % (width, argv, 'DECODE', decode(argv)))
