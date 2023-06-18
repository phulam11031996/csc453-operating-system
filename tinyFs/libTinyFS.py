import struct

from others import *
import libDisk


superblock = bytearray(BLOCK_SIZE)
root_inode = bytearray(BLOCK_SIZE)
mounted_disk = None
resource_table = {}


def tfs_mkfs(filename=DEFAULT_DISK_NAME, nBytes=DEFAULT_DISK_SIZE):
    """_summary_
    Makes an empty TinyFS file system of size nBytes on the file specified by
    ‘filename’. This function should use the emulated disk library to open the
    specified file, and upon success, format the file to be mountable. This
    includes initializing all data to 0x00, setting magic numbers, initializing
    and writing the superblock and other metadata, etc. Must return a specified
    success/error code.

    Args:
        filename (str, optional): _description_. Defaults to DEFAULT_DISK_NAME.
        nBytes (int, optional): _description_. Defaults to DEFAULT_DISK_SIZE.

    Returns:
        int: _description_
    """
    if nBytes < BLOCK_SIZE * 3:
        message = "Disk size is too small"
        return error(BAD_REQUEST, message)

    global DISK_SIZE, NUMBER_OF_DATABLOCKS, superblock, root_inode
    DISK_SIZE = nBytes
    NUMBER_OF_DATABLOCKS = nBytes // BLOCK_SIZE - 2

    fd = libDisk.open_disk(filename, nBytes)
    libDisk.read_block(fd, 0, superblock)
    libDisk.read_block(fd, 1, root_inode)
    superblock[0] = MAGIC_NUMBER
    size = INODE_SIZE + NUMBER_OF_DATABLOCKS
    superblock[OFFSET_BITMAP_INODE: OFFSET_BITMAP_INODE + size] = \
        struct.pack('{}B'.format(size), *[1]*size)
    for i in range(0, BLOCK_SIZE, INODE_SIZE):
        root_inode[i + OFFSET_DATABLOCK_POINTER] = 255
    libDisk.write_block(fd, 0, superblock)
    libDisk.write_block(fd, 1, root_inode)
    libDisk.close_disk(fd)
    return SUCCESS


def tfs_mount(filename):
    """_summary_
    tfs_mount(char *filename) “mounts” a TinyFS file system located within
    ‘filename’. As part of the mount operation, tfs_mount should verify the
    file system is the correct type. Only one file system may be mounted at a
    time. Use tfs_unmount to cleanly unmount the currently mounted file system.
    Must return a specified success/error code.

    Args:
        filename (str): _description_.

    Returns:
        int: _description_.
    """
    global mounted_disk, superblock, root_inode
    if mounted_disk == None:
        fd = libDisk.open_disk(filename, 0)
        libDisk.read_block(fd, 0, superblock)
        libDisk.read_block(fd, 1, root_inode)
        if not len(superblock) == 0 and superblock[0] == MAGIC_NUMBER:
            mounted_disk = fd
            return SUCCESS
        superblock = bytearray(BLOCK_SIZE)
        root_inode = bytearray(BLOCK_SIZE)
        mounted_disk = None
        return error(BAD_REQUEST, "File system not formatted")
    return error(BAD_REQUEST, "A file system already mounted")


def tfs_unmount():
    """_summary_
    tfs_unmount(void) “unmounts” the currently mounted file system.
    As part of the mount operation, tfs_mount should verify the file system is
    the correct type. 

    Returns:
        int: _description_
    """
    global mounted_disk, superblock, root_inode
    if not mounted_disk == None:
        libDisk.close_disk(mounted_disk)
        libDisk.write_block(mounted_disk, 0, superblock)
        libDisk.write_block(mounted_disk, 1, root_inode)
        root_inode = bytearray(BLOCK_SIZE)
        superblock = bytearray(BLOCK_SIZE)
        mounted_disk = None
        return SUCCESS
    return error(BAD_REQUEST, "No disk mounted")


def tfs_open(name):
    """_summary_
    Opens a file for reading and writing on the currently mounted file system.
    Creates a dynamic resource table entry for the file (the structure that
    tracks open files, the internal file pointer, etc.), and returns a file
    descriptor (integer) that can be used to reference this file while the
    filesystem is mounted.

    Args:
        name (str): _description_

    Returns:
        int: _description_
    """
    global mounted_disk, resource_table, superblock, root_inode
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    fd = generate_fd(name)
    if name in resource_table:
        return fd

    if len(root_inode) == 0 or root_inode[0] == MAGIC_NUMBER:
        for i in range(0, BLOCK_SIZE, INODE_SIZE):
            inode = root_inode[i:i+INODE_SIZE]
            filename, db = struct.unpack('8s 4x I', inode)
            filename = filename.rstrip(b'\x00')
            if filename == name:
                resource_table[filename] = Resource(fd, 0, db)
                return fd

    i_inode, i_datablock = find_free_inode_and_datablock(superblock)
    if i_inode == None or i_datablock == None:
        return error(OUT_OFF_MEMMORY, "Out off memmory")
    superblock[OFFSET_BITMAP_INODE + i_inode] = 0
    superblock[OFFSET_BITMAP_BLOCK + i_datablock] = 0
    root_inode[i_inode * INODE_SIZE: i_inode * INODE_SIZE + INODE_SIZE] = \
        struct.pack('8s 4x b 3x', name[0:MAX_FILE_LEN].encode(), i_datablock)
    resource_table[name] = Resource(fd, 0, i_datablock)
    libDisk.write_block(mounted_disk, 1, root_inode)
    libDisk.write_block(mounted_disk, 0, superblock)
    libDisk.write_block(mounted_disk, i_datablock + 2, bytearray(256))
    return fd


def tfs_close(fd):
    """_summary_
    Closes the file and removes dynamic resource table entry

    Args:
        fd (int): _description_

    Returns:
        int: _description_
    """
    global resource_table, superblock, root_inode
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    for filename, resource in resource_table.items():
        if resource.fd == fd:
            del resource_table[filename]
            return SUCCESS
    return error(NOT_FOUND, "File not found")


def tfs_write(fd, buffer, size):
    """_summary_
    Writes buffer ‘buffer’ of size ‘size’, which represents an entire file’s
    contents, to the file described by ‘FD’. Sets the file pointer to 0 (the
    start of file) when done. Returns success/error codes.

    Args:
        fd (int): _description_
        buffer (bytearray): _description_
        size (int): _description_

    Returns:
        int: _description_
    """
    global mounted_disk, resource_table
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    for resource in resource_table.values():
        if fd == resource.fd:
            data_block = buffer.encode() + b'\x00' * (BLOCK_SIZE - len(buffer))
            libDisk.write_block(mounted_disk, resource.db + 2, data_block)
            return SUCCESS
    return error(NOT_FOUND, "File not found")


def tfs_delete(fd):
    """_summary_
    deletes a file and marks its blocks as free on disk.

    Args:
        fd (int): _description_

    Returns:
        int: _description_
    """
    global resource_table, mounted_disk, superblock, root_inode
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    for filename, resource in resource_table.items():
        if fd == resource.fd:
            del resource_table[filename]
            for i in range(0, BLOCK_SIZE, INODE_SIZE):
                name = struct.unpack('8s 4x I', root_inode[i: i+INODE_SIZE])[0]
                name = name.rstrip(b'\x00').decode()
                if filename == name:
                    root_inode[i:i+INODE_SIZE] = \
                        bytearray(b'\x00' * INODE_SIZE)
                    superblock[OFFSET_BITMAP_INODE + i // INODE_SIZE] = 1
                    superblock[OFFSET_BITMAP_BLOCK + i // INODE_SIZE] = 1
                    libDisk.write_block(mounted_disk, 0, superblock)
                    libDisk.write_block(mounted_disk, 1, root_inode)
                    return SUCCESS
    return error(NOT_FOUND, "File not found")


def tfs_readByte(fd, buffer):
    """_summary_
    reads one byte from the file and copies it to ‘buffer’, using the current
    file pointer location and incrementing it by one upon success. If the file
    pointer is already at the end of the file then tfs_readByte() should return
    an error and not increment the file pointer.

    Args:
        fd (int): _description_
        buffer (bytearray): _description_

    Returns:
        int: _description_
    """
    global mounted_disk, resource_table
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    for resource in resource_table.values():
        if fd == resource.fd:
            if resource.fp == 255:
                return -1
            data_block = bytearray(BLOCK_SIZE)
            libDisk.read_block(mounted_disk, resource.db + 2, data_block)
            buffer[0] = data_block[resource.fp]
            resource.fp += 1
            return SUCCESS
    return error(NOT_FOUND, "File not found")


def tfs_seek(fd, offset):
    """_summary_
    change the file pointer location to offset (absolute). Returns success/error codes.

    Args:
        fd (int): _description_
        offset (int): _description_

    Returns:
        int: _description_
    """
    global mounted_disk, resource_table
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    for resource in resource_table.values():
        if fd == resource.fd:
            resource.fp = offset if offset < 255 else 255
            return SUCCESS
    return error(NOT_FOUND, "File not found")


# Additional

def tfs_rename(fd, new_name):
    """_summary_
    Renames a file.  New name should be passed in.

    Args:
        fd (int): _description_
        new_name (str): _description_

    Returns:
        int: _description_
    """
    global mounted_disk, resource_table
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    delete_filename = None
    for filename, resource in resource_table.items():
        if fd == resource.fd:
            swap_resource = resource
            delete_filename = filename
            break

    if delete_filename == None:
        return error(NOT_FOUND, "File not found")

    del resource_table[delete_filename]
    resource_table[new_name] = swap_resource

    for i in range(0, BLOCK_SIZE, INODE_SIZE):
        inode = root_inode[i:i+INODE_SIZE]
        swap_name = struct.unpack('8s 4x I', inode)[0]
        swap_name = swap_name.rstrip(b'\x00').decode()
        if swap_name == delete_filename:
            root_inode[i:i+MAX_FILE_LEN] = \
                new_name.encode() + b'\x00' * (MAX_FILE_LEN - len(new_name))
            return SUCCESS


def tfs_readdir():
    """_summary_
    lists all the files and directories on the disk
    """
    global mounted_disk, resource_table, root_inode
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    for i in range(0, BLOCK_SIZE, INODE_SIZE):
        inode = root_inode[i:i+INODE_SIZE]
        filename = struct.unpack('8s 4x I', inode)[0]
        filename = filename.rstrip(b'\x00').decode()
        if not filename == "":
            print(filename)


def tfs_displayFragments():
    """_summary_
    This function allows the user to see a map of all blocks with the non-free
    blocks clearly designated. You can return this as a linked list or a bitmap
    which you can use to display the map with.
    """
    global mounted_disk, resource_table, superblock
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    print("Block Bitmap:")
    for i in range(OFFSET_BITMAP_BLOCK, OFFSET_BITMAP_BLOCK + NUMBER_OF_DATABLOCKS):
        if superblock[i] == 1:
            print("Block " + str(i - OFFSET_BITMAP_BLOCK) + " is free")
        else:
            print("Block " + str(i - OFFSET_BITMAP_BLOCK) + " is allocated")


def tfs_defrag():
    """_summary_
    moves blocks such that all free blocks are contiguous at the end of the
    disk. This should be verifiable with the tfs_displayFraments() function.
    """
    global mounted_disk, resource_table, superblock, root_inode
    if mounted_disk == None:
        return error(BAD_REQUEST, "No disk mounted")

    bitmap_arr_data_block = \
        superblock[OFFSET_BITMAP_BLOCK: OFFSET_BITMAP_BLOCK +
                   NUMBER_OF_DATABLOCKS]

    buffer_one = bytearray(BLOCK_SIZE)
    buffer_two = bytearray(BLOCK_SIZE)
    swap_arr = swap_zeros_to_end(bitmap_arr_data_block)
    for l, r in swap_arr.items():
        superblock[OFFSET_BITMAP_BLOCK+r], superblock[OFFSET_BITMAP_BLOCK+l] = \
            superblock[OFFSET_BITMAP_BLOCK +
                       l], superblock[OFFSET_BITMAP_BLOCK+r]
        libDisk.read_block(mounted_disk, l + FIRST_DATABLOCK, buffer_one)
        libDisk.read_block(mounted_disk, r + FIRST_DATABLOCK, buffer_two)
        libDisk.write_block(mounted_disk, l + FIRST_DATABLOCK, buffer_two)
        libDisk.write_block(mounted_disk, r + FIRST_DATABLOCK, buffer_one)

    for i in range(0, BLOCK_SIZE, INODE_SIZE):
        if root_inode[i+OFFSET_DATABLOCK_POINTER] in swap_arr:
            l = root_inode[i+OFFSET_DATABLOCK_POINTER]
            r = swap_arr.get(l)
            root_inode[i+OFFSET_DATABLOCK_POINTER] = r

    libDisk.write_block(mounted_disk, 0, superblock)
    libDisk.write_block(mounted_disk, 1, root_inode)


def find_free_inode_and_datablock(superblock):
    inode_idex = None
    data_block_index = None
    for i in range(OFFSET_BITMAP_INODE, OFFSET_BITMAP_INODE + INODE_SIZE):
        if superblock[i] == 1:
            inode_idex = i
            break
    for i in range(OFFSET_BITMAP_BLOCK, OFFSET_BITMAP_BLOCK + NUMBER_OF_DATABLOCKS):
        if superblock[i] == 1:
            data_block_index = i
            break
    return inode_idex - OFFSET_BITMAP_INODE, data_block_index - OFFSET_BITMAP_BLOCK
