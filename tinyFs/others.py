import hashlib


class Resource:
    def __init__(self, fd, fp, db) -> None:
        self.fd = fd
        self.fp = fp
        self.db = db


def generate_fd(filename):
    sha256 = hashlib.sha256()
    sha256.update(filename.encode('utf-8'))
    unique_id = int(sha256.hexdigest(), 16)
    return int(str(unique_id)[:3])


def swap_zeros_to_end(arr):
    swaps = {}
    l, r = 0, len(arr) - 1

    while l < r:
        if arr[l] == 0 and arr[r] == 1:
            swaps[l] = r
            l += 1
            r -= 1
        if arr[l] == 1 and arr[r] == 0:
            l += 1
            r -= 1
        if arr[l] == 1 and arr[r] == 1:
            l += 1
        if arr[l] == 0 and arr[r] == 0:
            r -= 1
    return swaps


def error(code, message):
    print("Message: " + message)
    return code


OUT_OFF_MEMMORY = -505
INTERNAL_ERROR = -500
BAD_REQUEST = -400
NOT_FOUND = -404
SUCCESS = 200


DEFAULT_DISK_NAME = 'tinyFSDisk'
DEFAULT_DISK_SIZE = 10240
MAGIC_NUMBER = 90
BLOCK_SIZE = 256

NUMBER_OF_DATABLOCKS = None
DISK_SIZE = None
MAX_FILE_LEN = 8
INODE_SIZE = 16
ROOT_INODE_POINTER = 256
FIRST_DATABLOCK = 2
OFFSET_BITMAP_INODE = 8
OFFSET_BITMAP_BLOCK = 24
OFFSET_DATABLOCK_POINTER = 12
