"""
Entrypoint for calculator worker

Copyright (c) 2012-2013 Heikki Nousiainen, F-Secure
See LICENSE for details
"""

import json
import optparse
import os
import sys

from . import calculator

__appname__ = "calculator worker"
__usage__   = "%prog -c <configuration file>"
__version__ = "1.0"
__author__  = "Heikki Nousiainen"

def main(argv):
    """ Main function """
    parser = optparse.OptionParser(description=__doc__, version=__version__)
    parser.set_usage(__usage__)
    parser.add_option("-c", dest="config_file", help="configuration filename")
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

    worker = calculator.CalculatorWorker(config)
    return worker.start()

def main_entry():
    return main(sys.argv)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

