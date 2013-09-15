""" Module entrypoint for DistCI command line interface

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import sys
from . import cli

def main_entry():
    """ Main entrypoint for the console script """
    return cli.main()

if __name__ == "__main__":
    sys.exit(cli.main())
