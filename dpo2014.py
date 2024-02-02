#! /usr/bin/env python3

import click
import datetime
import logging
import os
import sys
import time

import scpi

log = logging.getLogger('.dpo2014')

CHANNEL = {
    '1': 'CH1',
    '2': 'CH2',
    '3': 'CH3',
    '4': 'CH4',
}

class Dpo2014Error(Exception):
    pass

class Dpo2014Status:
    __slots__ = 'power_on', 'user_request', 'command_error', 'execution_error', 'device_error', 'query_error', 'request_control', 'operation_complete'

    def __str__(self):
        return (f'Power on:           {self.power_on}\n'
                f'User request:       {self.user_request}\n'
                f'Command error:      {self.command_error}\n'
                f'Execution Error:    {self.execution_error}\n'
                f'Device Error:       {self.device_error}\n'
                f'Query Error:        {self.query_error}\n'
                f'Request Control:    {self.request_control}\n'
                f'Operation Complete: {self.operation_complete}')

class Dpo2014:
    def __init__(self, scpi):
        self._scpi = scpi

    def _bulk_read_to_file(self, filename):
        log.info(f'Streaming to file: {filename}"')
        with open(filename, 'wb') as file:
            done = False
            while not done:
                data = self._scpi._device.recv(128)
                if data.endswith(b'IEND\xae\x42\x60\x82'):
                    done = True

                file.write(data)

    def busy(self):
        return bool(int(self._scpi.query('BUSY?')))

    def status(self):
        response = int(self._scpi.query('*ESR?'))
        status = Dpo2014Status()

        status.power_on = bool(response & 0x80)
        status.user_request = bool(response & 0x40)
        status.command_error = bool(response & 0x20)
        status.execution_error = bool(response & 0x10)
        status.device_error = bool(response & 0x08)
        status.query_error = bool(response & 0x04)
        status.request_control = bool(response & 0x02)
        status.operation_complete = bool(response & 0x01)

        return status

    def set_label(self, channel, label):
        self._scpi.set(f'{channel}:LAB "{label}"')

    def image(self, prefix):
        timestamp = datetime.datetime.now().isoformat()
        filename = f'{prefix}-{timestamp}.png'

        self._scpi.set(f'SAV:IMAG:FILEF PNG; :SAV:IMAG "TMP.PNG"')
        while self.busy():
            time.sleep(0.100)

        self._scpi.set(f'FILES:READF "TMP.PNG"')
        self._bulk_read_to_file(filename)

        self._scpi.set(f'FILES:DELE "TMP.PNG"')

    def waveform(self, prefix):
        # TODO: This should be essentially the same things as image() but using
        # a different SET and a different filename
        #
        # self._scpi.set(f'SAV:WAVE:FILEF SPREADS; :SAV:WAVE ALL,"E:/tmp-{filename}.csv"')
        pass

tcpaddr_env_var = 'DPO2014_TCPADDR'
tcpaddr_default = os.environ.get(tcpaddr_env_var)
usbdev_env_var = 'DPO2014_USBDEVICE'
usbdev_default = os.environ.get(usbdev_env_var)
@click.group()
@click.option('-t', '--tcp-addr', default=tcpaddr_default, type=str, help=f"Target IP address. Override default with {tcpaddr_env_var} env var.")
@click.option('-u', '--usb-device', default=usbdev_default, type=str, help=f"Target USB device. Override default with {usbdev_env_var} env var.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
@click.pass_context
def cli(context, tcp_addr, usb_device, verbose):
    """CLI control of a DPO2014 oscilloscope."""
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    if tcp_addr:
        context.target = Dpo2014(scpi.ScpiSocket(tcp_addr))
    elif usb_device:
        context.target = Dpo2014(scpi.ScpiUsb(usb_device))
    else:
        raise click.BadParameter('TCP address or USB device required.')

@click.command()
@click.pass_context
def info(context):
    """Show the target's version strings."""
    print(context.parent.target._scpi.get_id())

@click.command()
@click.pass_context
def status(context):
    """Show the target's status."""
    print(context.parent.target.status())

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.argument('label', nargs=1, required=True)
@click.pass_context
def label(context, channel, label):
    """Set a channel's display label."""
    context.parent.target.set_label(CHANNEL[channel], label)

@click.command()
@click.argument('prefix', nargs=1, required=True)
@click.pass_context
def image(context, prefix):
    """Capture screen image."""
    context.parent.target.image(prefix)

cli.add_command(info)
cli.add_command(status)
cli.add_command(label)
cli.add_command(image)

if __name__ == '__main__':
    try:
        cli()
    except (scpi.ScpiError, Dpo2014Error) as e:
        log.error(e)
        sys.exit(1)
