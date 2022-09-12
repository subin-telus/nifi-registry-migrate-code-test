#!/usr/bin/env bash
cond --version 0> /dev/null 1> /dev/null 2> /dev/null
laststat=$?
if ([ "${laststat}" == 0 ]) then
        echo -e "[`date --iso-8601=seconds`] - Conda Installed"
else
        echo -e "[`date --iso-8601=seconds`] - Conda Not Installed"
fi
