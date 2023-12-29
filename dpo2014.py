#! /usr/bin/env python3

import click
import logging
import os
import sys

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

class Dpo2014:
    def __init__(self, scpi):
        self._scpi = scpi

    def set_label(self, channel, label):
        self._scpi.set(f'{channel}:LAB "{label}"')

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
@click.argument('channel', nargs=1, required=True)
@click.argument('label', nargs=1, required=True)
@click.pass_context
def label(context, channel, label):
    """Set a channel's display label."""
    context.parent.target.set_label(CHANNEL[channel], label)

cli.add_command(info)
cli.add_command(label)

if __name__ == '__main__':
    try:
        cli()
    except (scpi.ScpiError, Dpo2014Error) as e:
        log.error(e)
        sys.exit(1)
