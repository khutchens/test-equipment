#! /usr/bin/env python3

import click
import logging
import os
import socket
import sys
import time

log_formatter = logging.Formatter('%(name)s:%(levelname)s: %(message)s')

log_handler = logging.StreamHandler()
log_handler.setLevel(logging.WARNING)
log_handler.setFormatter(log_formatter)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(log_handler)

class ScpiError(Exception):
    pass

class Scpi:
    def __init__(self, device):
        self._device = device

    def query(self, command):
        log.info(f'SCPI query: {command}')

        if command[-1] != '\n':
            command += '\n'

        self._device.send(command.encode('utf-8'))
        response = self._device.recv(4096).decode('utf-8').rstrip()
        log.info(f'SCPI response: {response}')
        return response

    def set(self, command):
        log.info(f'SCPI set: {command}')
        self._device.send(command.encode('utf-8'))

        code, message = self.query('SYST:ERR?').split(',', 1)
        if int(code) != 0:
            raise ScpiError(f'SCPI set failed, command:"{command}", result:{code},"{message}"')

    def get_id(self):
        return self.query('*IDN?').split(',')

class ScpiSocket(Scpi):
    def __init__(self, address, port):
        scpi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        log.info(f'Connecting: {address}:{port}')
        scpi_socket.connect((address, port))
        log.info('Connected')

        super().__init__(scpi_socket)

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

addr_env_var = 'SPD1000X_ADDR'
addr_default = os.environ.get(addr_env_var)
port_env_var = 'SPD1000X_PORT'
port_default = os.environ.get(port_env_var, '5025')
@click.group()
@click.option('-a', '--ip-addr', default=addr_default, type=str, help=f"Target's IP address. Defualt={addr_default}. Override default with {addr_env_var} env var.")
@click.option('-p', '--port', default=port_default, type=int, help=f"Target's TCP port. Defualt={port_default}. Override default with {port_env_var} env var.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
def cli(ip_addr, port, verbose):
    """CLI control of a SPD1000X power supply via TCP."""
    if verbose:
        log_handler.setLevel(logging.INFO)

    if ip_addr is None:
        raise click.BadParameter(f'Set ${addr_env_var} or use --ip-addr option', param_hint='--ip-addr')

    global scpi
    scpi = ScpiSocket(ip_addr, port)
    global target
    target = Spd1000x(scpi)

@click.command()
def info():
    """Show the target's version strings."""
    print(scpi.get_id())

@click.command()
def status():
    """Show the target's current setpoint and output state."""
    print(target.get_state())

@click.command()
@click.argument('voltage', nargs=1, required=True)
@click.argument('current', nargs=1, required=True)
def set(voltage, current):
    """Set the target's voltage/current setpoints. Output must be off."""
    target.set_vi(voltage, current)
    print(target.get_state())

@click.command()
def on():
    """Turn on the target's output."""
    target.output(True)
    time.sleep(0.500)
    print(target.get_state())

@click.command()
def off():
    """Turn off the target's output."""
    target.output(False)
    time.sleep(0.500)
    print(target.get_state())

cli.add_command(info)
cli.add_command(status)
cli.add_command(set)
cli.add_command(on)
cli.add_command(off)

if __name__ == '__main__':
    try:
        cli()
    except (ScpiError, Spd1000xError) as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)
