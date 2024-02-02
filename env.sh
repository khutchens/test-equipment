repo=$0:a:h

alias lab="$repo/venv/bin/python $repo/scpi.py"

export SPD1000X_TCPADDR="10.1.0.6:5025"
alias lab-dc="$repo/venv/bin/python $repo/spd1000x.py"

export SDG1000X_TCPADDR="10.1.0.5:5025"
alias lab-sig="$repo/venv/bin/python $repo/sdg1000x.py"

export DPO2014_USBDEVICE="/dev/usbtmc0"
alias lab-scope="$repo/venv/bin/python $repo/dpo2014.py"
