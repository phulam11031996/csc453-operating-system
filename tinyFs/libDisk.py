import os
from others import *



def open_disk(filename, nBytes):
    """_summary_
    This function opens a regular UNIX file and designates the first nBytes of
    it as space for the emulated disk. nBytes should be a number that is evenly
    divisible by the block size. If nBytes > 0 and there is already a file by
    the given filename, that disk is resized to nBytes, and that file’s
    contents may be overwritten. If nBytes is 0, an existing disk is opened,
    and should not be overwritten. There is no requirement to maintain
    integrity of any content beyond nBytes. Errors must be returned for any
    other failures, as defined by your own error code system.

    Args:
        filename (str): _description_
        nBytes (int): _description_

    Returns:
        int: _description_
    """
    try:
        file_descriptor = os.open(filename, os.O_CREAT | os.O_RDWR)
        if not nBytes == 0:
            os.truncate(file_descriptor, 0)
            os.truncate(file_descriptor, nBytes)
        return file_descriptor
    except:
        return INTERNAL_ERROR


def read_block(disk, bNum, block):
    """_summary_
    readBlock() reads an entire block of BLOCKSIZE bytes from the open disk
    (identified by ‘disk’) and copies the result into a local buffer (must be
    at least of BLOCKSIZE bytes). The bNum is a logical block number, which
    must be translated into a byte offset within the disk. The translation from
    logical to physical block is straightforward: bNum=0 is the very first byte
    of the file. bNum=1 is BLOCKSIZE bytes into the disk, bNum=n is n*BLOCKSIZE
    bytes into the disk. On success, it returns 0. Errors must be returned if
    ‘disk’ is not available (i.e. hasn’t been opened) or for any other
    failures, as defined by your own error code system.

    Args:
        disk (int): _description_
        bNum (int): _description_
        block (bytearray): _description_

    Returns:
        int: _description_
    """
    try:
        os.lseek(disk, bNum * BLOCK_SIZE, 0)
        block[:] = os.read(disk, len(block))
        return 0
    except:
        return INTERNAL_ERROR


def write_block(disk, bNum, block):
    """_summary_
    writeBlock() takes disk number ‘disk’ and logical block number ‘bNum’ and
    writes the content of the buffer ‘block’ to that location. BLOCKSIZE bytes
    will be written from ‘block’ regardless of its actual size. The disk must
    be open. Just as in readBlock(), writeBlock() must translate the logical
    block bNum to the correct byte position in the file. On success, it returns
    0. Errors must be returned if ‘disk’ is not available (i.e. hasn’t been
    opened) or for any other failures, as defined by your own error code system.

    Args:
        disk (int): _description_
        bNum (int): _description_
        block (bytearray): _description_

    Returns:
        int: _description_
    """
    try:
        os.lseek(disk, bNum * BLOCK_SIZE, 0)
        block = os.write(disk, block)
        return 0
    except:
        return INTERNAL_ERROR


def close_disk(disk):
    """_summary_
    closeDisk() takes a disk number ‘disk’ and makes the disk closed to further
    I/O; i.e. any subsequent reads or writes to a closed disk should return an
    error. Closing a disk should also close the underlying file, committing any
    writes being buffered by the real OS.

    Args:
        disk (int): _description_

    Returns:
        _type_: _description_
    """
    try:
        os.close(disk)
    except:
        return INTERNAL_ERROR
