#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from ryu.cmd import manager


def main():
    #sys.argv.append('simple_switch_13')
    sys.argv.append('mud_controller')
    sys.argv.append('--verbose')
    sys.argv.append('--enable-debugger')
    manager.main()

if __name__ == '__main__':
    main()
