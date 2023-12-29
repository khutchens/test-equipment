alias lab="$HOME/spd1000x/venv/bin/python $HOME/spd1000x/scpi.py"

export SPD1000X_TCPADDR="10.1.0.6:5025"
alias lab-dc="$HOME/spd1000x/venv/bin/python $HOME/spd1000x/spd1000x.py"

export SDG1000X_TCPADDR="10.1.0.5:5025"
alias lab-sig="$HOME/spd1000x/venv/bin/python $HOME/spd1000x/sdg1000x.py"

export DPO2014_USBDEVICE="/dev/usbtmc0"
alias lab-scope="$HOME/spd1000x/venv/bin/python $HOME/spd1000x/dpo2014.py"
