# Name: Phu Lam
import libTinyFS
from others import *

# Make a file system with default params
libTinyFS.tfs_mkfs()

# Mount file system

libTinyFS.tfs_mount("not_formatted_file_system")  # Message: File system not formatted
libTinyFS.tfs_mount(DEFAULT_DISK_NAME)

# Open/Create files
file0 = libTinyFS.tfs_open("file0")
file1 = libTinyFS.tfs_open("file1")
file2 = libTinyFS.tfs_open("file2")


# Close files
libTinyFS.tfs_close(file2)
libTinyFS.tfs_close(file2)  # Message: File not found


# Write to files
write = "0123456789"
libTinyFS.tfs_write(file0, write, len(write))
write = "file already closed"
libTinyFS.tfs_write(file2, write, len(write))  # Message: File not found


# Delete
libTinyFS.tfs_delete(file1)

# readByte
byte = bytearray(1)
byte1 = bytearray(1)
byte2 = bytearray(1)
libTinyFS.tfs_readByte(file0, byte)
libTinyFS.tfs_readByte(file0, byte1)
libTinyFS.tfs_readByte(file0, byte2)
print(byte)  # 0
print(byte1)  # 1
print(byte2)  # 2

# seek
libTinyFS.tfs_seek(file0, 9)
libTinyFS.tfs_readByte(file0, byte)
print(byte)  # 9

# Addtional functionality

# rename
libTinyFS.tfs_rename(file0, "rename0")
libTinyFS.tfs_rename(file1, "rename1") # file1 is closed
libTinyFS.tfs_rename(file2, "rename2")  # file2 is deleted
libTinyFS.tfs_readdir()

# show fragmentation
libTinyFS.tfs_displayFragments()
libTinyFS.tfs_defrag()
libTinyFS.tfs_displayFragments()


libTinyFS.tfs_unmount()

