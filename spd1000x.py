#! /usr/bin/env python3

import click
import logging
import os
import sys
import time

import scpi

log = logging.getLogger('.spd1000x')

class Spd1000xError(Exception):
    pass

class Spd1000xState:
    __slots__ = 'v_set', 'i_set', 'v_meas', 'i_meas', 'output', 'regulation', 'mode'

    def __str__(self):
        output_mode = 'on' if self.output else 'off'
        return (f'Set:  {self.v_set:>6s}V {self.i_set:>6s}A\n'
                f'Meas: {self.v_meas:>6s}V {self.i_meas:>6s}A\n'
                f'Output: {output_mode}, {self.regulation}, {self.mode}')

class Spd1000x:
    def __init__(self, scpi):
        self._channel = 'CH1'
        self._scpi = scpi

    def set_vi(self, voltage, current):
        state = self.get_state()
        if state.output:
            raise Spd1000xError('Cannot change setpoints while output is enabled')

        self._scpi.set(f'{self._channel}:VOLT {voltage}')
        self._scpi.set(f'{self._channel}:CURR {current}')

    def output(self, enable):
        self._scpi.query('INST?')
        state = 'ON' if enable else 'OFF'
        self._scpi.set(f'OUTP {self._channel},{state}')

    def get_state(self):
        state = Spd1000xState()

        state.v_set = self._scpi.query(f'{self._channel}:VOLT?')
        state.i_set = self._scpi.query(f'{self._channel}:CURR?')
        state.v_meas = self._scpi.query(f'MEAS:VOLT? {self._channel}')
        state.i_meas = self._scpi.query(f'MEAS:CURR? {self._channel}')

        status = int(self._scpi.query('SYST:STAT?'), 16)
        state.regulation = 'constant-current' if status & 0x1 else 'constant-voltage'
        state.output = bool(status & 0x10)
        state.mode = '4-wire' if status & 0x20 else '2-wire'

        return state

tcpaddr_env_var = 'SPD1000X_TCPADDR'
tcpaddr_default = os.environ.get(tcpaddr_env_var)
usbdev_env_var = 'SPD1000X_USBDEVICE'
usbdev_default = os.environ.get(usbdev_env_var)
@click.group()
@click.option('-t', '--tcp-addr', default=tcpaddr_default, type=str, help=f"Target IP address. Override default with {tcpaddr_env_var} env var.")
@click.option('-u', '--usb-device', default=usbdev_default, type=str, help=f"Target USB device. Override default with {usbdev_env_var} env var.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
@click.pass_context
def cli(context, tcp_addr, usb_device, verbose):
    """CLI control of a SPD1000X power supply."""
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    if tcp_addr:
        context.target = Spd1000x(scpi.ScpiSocket(tcp_addr))
    elif usb_device:
        context.target = Spd1000x(scpi.ScpiUsb(usb_device))
    else:
        raise click.BadParameter('TCP address or USB device required.')

@click.command()
@click.pass_context
def status(context):
    """Show the target's current setpoint and output state."""
    print(context.parent.target.get_state())

@click.command()
@click.argument('voltage', nargs=1, required=True)
@click.argument('current', nargs=1, required=True)
@click.pass_context
def set(context, voltage, current):
    """Set the target's voltage/current setpoints. Output must be off."""
    target.set_vi(voltage, current)
    print(context.parent.target.get_state())

@click.command()
@click.pass_context
def on(context):
    """Turn on the target's output."""
    target.output(True)
    time.sleep(0.500)
    print(context.parent.target.get_state())

@click.command()
@click.pass_context
def off(context):
    """Turn off the target's output."""
    target.output(False)
    time.sleep(0.500)
    print(context.parent.target.get_state())

cli.add_command(status)
cli.add_command(set)
cli.add_command(on)
cli.add_command(off)

if __name__ == '__main__':
    try:
        cli()
    except (scpi.ScpiError, Spd1000xError) as e:
        log.error(e)
        sys.exit(1)
