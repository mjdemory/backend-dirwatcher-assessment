# !/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = """Michael DeMory, with help from Zac Gerber, Mav Watts, video by Piero Madar,
Nikal Morgan, Chris Warren, and David R.""" 

import os
import sys
import argparse
from datetime import datetime as dt
import logging.handlers
import logging
import time
import signal
import errno

logger = logging.getLogger(__name__)

files = {}
exit_flag = False


def find_magic(filename,starting_line,magic_word):
    line_number = 0
    with open(filename) as f:
        for line_number, line in enumerate(f):
            if line_number >= starting_line:
                if magic_word in line:
                    logger.info(
                        f"This file: {filename} found: {magic_word} on line: {line_number + 1}"
                    )
    return line_number + 1


def watch_directory(args):
    file_list = os.listdir(args.directory)
    
    add_file(file_list, args.ext)
    remove_file(file_list)
    for f in files:
        files[f]= find_magic(
            os.path.join(args.directory, f),
            files[f],
            args.magic
        )
    
def add_file(file_list, ext):
    global files
    for f in file_list:
        if f.endswith(ext) and f not in files:
            files[f] = 0
            logger.info(f'{f} added to watchlist.')
    return file_list
def remove_file(file_list):
    global files
    for f in list(files):
        if f not in file_list:
            logger.info(f'{f} removed from watchlist.')
            del files[f]
    return file_list
    

def signal_handler(sig_num, frame):
    """
    This is a handler for SIGTERM and SIGINT. Other signals can be mapped here as well (SIGHUP?)
    Basically, it just sets a global flag, and main() will exit its loop if the signal is trapped.
    :param sig_num: The integer signal number that was trapped from the OS.
    :param frame: Not used
    :return None
    """

    logger.warning('Received ' + signal.Signals(sig_num).name)
    global exit_flag
    exit_flag = True


def create_parser():
    """Returns an instance of argparse.ArgumentParser"""
    parser = argparse.ArgumentParser(description="Watch for change in directories.")
    parser.add_argument('-i', '--interval', type=float, default=1.0, help="Number of seconds between polling")
    parser.add_argument('-e', '--ext', type=str, default='.txt', help="Filters the type of file to watch for")
    parser.add_argument('directory', help="directory to watch")
    parser.add_argument('magic', help='Text to watch for')
    return parser

def main(args):
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(name) - 12s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG
    )
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(filename='mywatcher.log')
    logger.addHandler(fh)

    start_time = dt.now()
    logger.info(
        '\n'
        '-------------------------------------------------------\n'
        f'   Running {__file__}\n'
        f'   PID is {os.getpid()}\n'
        f'   Started on {start_time.isoformat()}\n'
        '-------------------------------------------------------\n'
    )
    parser= create_parser()
    args = parser.parse_args()


    # Hook into these two signals from the OS
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    # Now my signal_handler will get called if OS sends
    # either of these to my process.

    while not exit_flag:
        try:
            # call my directory watching function
            watch_directory(args)
        except OSError as e:
            # This is an UNHANDLED exception
            # Log an ERROR level message here
            if e.errno == errno.ENOENT:
                time.sleep(2)
            else:
                logger.error(e)
        except Exception as e:
            logger.error(f"UNHANDLED EXCEPTION:{e}")

        # put a sleep inside my while loop so I don't peg the cpu usage at 100%
        time.sleep(int(float(args.interval)))

    # final exit point happens here
    # Log a message that we are shutting down
    # Include the overall uptime since program start
    time_on = dt.now() - start_time
    logger.info(
        '\n'
        '-------------------------------------------------------\n'
        f'   Running {__file__}\n'
        f'   Time was {str(time_on)}\n'
        '-------------------------------------------------------\n'
    )
    logging.shutdown()

if __name__ == '__main__':
    main(sys.argv[1:])