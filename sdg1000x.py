#! /usr/bin/env python3

import click
import logging
import os
import sys

import scpi

log = logging.getLogger('.sdg1000x')

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

addr_env_var = 'SDG1000X_ADDR'
addr_default = os.environ.get(addr_env_var)
port_env_var = 'SDG1000X_PORT'
port_default = os.environ.get(port_env_var, '5025')
@click.group()
@click.option('-a', '--ip-addr', default=addr_default, type=str, help=f"Target's IP address. Defualt={addr_default}. Override default with {addr_env_var} env var.")
@click.option('-p', '--port', default=port_default, type=int, help=f"Target's TCP port. Defualt={port_default}. Override default with {port_env_var} env var.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
@click.pass_context
def cli(context, ip_addr, port, verbose):
    """CLI control of a SDG1000X power supply via TCP."""
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    if ip_addr is None:
        raise click.BadParameter(f'Set ${addr_env_var} or use --ip-addr option', param_hint='--ip-addr')

    context.target = Sdg1000x(scpi.ScpiSocket(ip_addr, port))

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.argument('enable', nargs=1, required=False)
@click.pass_context
def out(context, channel, enable):
    """Show a channel's current output state."""
    print(context.parent.target.get_output(channel))

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.pass_context
def on(context, channel):
    """Turn on a channel's output."""
    context.parent.target.set_output(channel, 'ON')
    print(context.parent.target.get_output(channel))

@click.command()
@click.argument('channel', nargs=1, required=True)
@click.pass_context
def off(context, channel):
    """Turn off a channel's output."""
    context.parent.target.set_output(channel, 'OFF')
    print(context.parent.target.get_output(channel))

cli.add_command(out)
cli.add_command(on)
cli.add_command(off)

if __name__ == '__main__':
    try:
        cli()
    except (scpi.ScpiError, Sdg1000xError) as e:
        log.error(e)
        sys.exit(1)
