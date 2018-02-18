#!/bin/bash

# https://unix.stackexchange.com/questions/25945/how-to-check-if-there-are-no-parameters-provided-to-a-command
if [ $# -eq 0 ]; then
    echo "[!] Pass at least the name of the app to be analysed."
    echo -e "\t - Remember to mount the volume and pass the container path to the app."
    exit 1
fi

python /StaCoAn/src/stacoan.py -p $@
# https://stackoverflow.com/questions/90418/exit-shell-script-based-on-process-exit-code
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

# Redirect to start.html
echo '<meta http-equiv="refresh" content="0; url=/start.html" />' > /StaCoAn/src/report/index.html
cd /StaCoAn/src/report/ && python -m http.server
