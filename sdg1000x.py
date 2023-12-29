#! /usr/bin/env python3

import click
import logging
import os
import sys

import scpi

log = logging.getLogger('.sdg1000x')

CHANNEL = {
    '1': 'C1',
    '2': 'C2',
}

class Sdg1000xError(Exception):
    pass

class Sdg1000x:
    def __init__(self, scpi):
        self._scpi = scpi

    def reset(self):
        self._scpi.set('*RST')

    def get_output(self, channel):
        return self._scpi.query(f'{channel}:OUTP?')

    def set_output(self, channel, enable):
        self._scpi.set(f'{channel}:OUTP {enable}')

tcpaddr_env_var = 'SDG1000X_TCPADDR'
tcpaddr_default = os.environ.get(tcpaddr_env_var)
usbdev_env_var = 'SDG1000X_USBDEVICE'
usbdev_default = os.environ.get(usbdev_env_var)
@click.group()
@click.option('-t', '--tcp-addr', default=tcpaddr_default, type=str, help=f"Target IP address. Override default with {tcpaddr_env_var} env var.")
@click.option('-u', '--usb-device', default=usbdev_default, type=str, help=f"Target USB device. Override default with {usbdev_env_var} env var.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
@click.pass_context
def cli(context, tcp_addr, usb_device, verbose):
    """CLI control of a SDG1000X power supply."""
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    if tcp_addr:
        context.target = Sdg1000x(scpi.ScpiSocket(tcp_addr))
    elif usb_device:
        context.target = Sdg1000x(scpi.ScpiUsb(usb_device))
    else:
        raise click.BadParameter('TCP address or USB device required.')

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.pass_context
def out(context, channel):
    """Show a channel's current output state."""
    print(context.parent.target.get_output(CHANNEL[channel]))

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.pass_context
def on(context, channel):
    """Turn on a channel's output."""
    context.parent.target.set_output(channel, 'ON')
    print(context.parent.target.get_output(CHANNEL[channel]))

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.pass_context
def off(context, channel):
    """Turn off a channel's output."""
    context.parent.target.set_output(channel, 'OFF')
    print(context.parent.target.get_output(CHANNEL[channel]))

cli.add_command(out)
cli.add_command(on)
cli.add_command(off)

if __name__ == '__main__':
    try:
        cli()
    except (scpi.ScpiError, Sdg1000xError) as e:
        log.error(e)
        sys.exit(1)
