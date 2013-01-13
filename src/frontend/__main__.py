#!/usr/bin/env python
""" Module entrypoint for distci-frontend """

import sys
import os
import optparse
from flup.server.fcgi import WSGIServer

from . import frontend

__appname__ = "distci-frontend"
__usage__   = "%prog -c <configuration file> [-s <socket filename>]"
__version__ = "1.0"
__author__  = "Heikki Nousiainen"

def main(args_in):
    """ Main function """
    parser = optparse.OptionParser(description=__doc__, version=__version__)
    parser.set_usage(__usage__)
    parser.add_option("-c", dest="config_file", help="configuration filename")
    parser.add_option("-s", dest="socket_file", help="listening socket filename", default="/var/run/distci-frontend.socket")
    opts, _ = parser.parse_args(args_in)

    if not opts.config_file:
        print "configuration file not specified"
        parser.print_help()
        return -1

    frontend_app = frontend.Frontend(opts.config_file)

    try:
        WSGIServer(frontend_app.handle_request,
                   bindAddress=opts.socket_file,
                   umask=0111).run()
    finally:
        os.unlink(opts.socket_file)

    return 0

def main_entry():
    return main(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

