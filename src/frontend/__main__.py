#!/usr/bin/env python
"""
Module entrypoint for distci-frontend

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import sys
import os
import optparse
import logging
import json
from flup.server.fcgi import WSGIServer

from . import frontend

__appname__ = "distci-frontend"
__usage__   = "%prog -c <configuration file> [-s <socket filename>]"
__version__ = "1.0"
__author__  = "Heikki Nousiainen"

def main(argv):
    """ Main function """
    parser = optparse.OptionParser(description=__doc__, version=__version__)
    parser.set_usage(__usage__)
    parser.add_option("-c", dest="config_file", help="configuration filename")
    parser.add_option("-s", dest="socket_file", help="listening socket filename", default="/var/run/distci-frontend.socket")
    opts, _ = parser.parse_args(argv)

    if not opts.config_file:
        print "configuration file not specified"
        parser.print_help()
        return -1

    try:
        config = json.load(file(opts.config_file, 'rb'))
    except:
        print "failed to parse configuration file"
        return -1

    if config.get('log_file'):
        log_level = logging._levelNames.get(config.get('log_level', 'info').upper())
        logging.basicConfig(level=log_level, format='%(asctime)s\t%(threadName)s\t%(name)s\t%(levelname)s\t%(message)s', filename=config.get('log_file'))

    frontend_app = frontend.Frontend(config)

    try:
        WSGIServer(frontend_app.handle_request,
                   bindAddress=opts.socket_file,
                   umask=0111).run()
    finally:
        os.unlink(opts.socket_file)

    return 0

def main_entry():
    return main(sys.argv)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

