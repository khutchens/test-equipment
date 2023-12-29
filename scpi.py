#! /usr/bin/env python3

import click
import logging
import os
import socket
import sys
import time

log_formatter = logging.Formatter('%(name)s:%(levelname)s: %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
logging.getLogger('').addHandler(log_handler)

log = logging.getLogger('.scpi')

class ScpiError(Exception):
    pass

class Scpi:
    def __init__(self, device):
        self._device = device

    def query(self, command):
        command_line = command.rstrip()
        command_delimited = command + '\n'
        log.info(f'SCPI query: {command_line}')

        try:
            self._device.send(command_delimited.encode('utf-8'))
            response = self._device.recv(4096).decode('utf-8').rstrip()
        except socket.timeout:
            raise ScpiError(f'Query failed: socket timeout, command: {command_line}');

        log.info(f'SCPI response: {response}')
        return response

    def set(self, command):
        command_line = command.rstrip()
        command_delimited = command + '\n'
        log.info(f'SCPI set: {command_line }')

        try:
            self._device.send(command_delimited.encode('utf-8'))
        except socket.timeout:
            raise ScpiError(f'Set failed: socket timeout, command: {command_line}');

        #code, message = self.query('SYST:ERR?').split(',', 1)
        #if int(code) != 0:
        #    raise ScpiError(f'SCPI set failed, command:"{command}", result:{code},"{message}"')

    def get_id(self):
        return self.query('*IDN?').split(',')

class ScpiSocket(Scpi):
    def __init__(self, address, port):
        scpi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        scpi_socket.settimeout(1.000)

        log.info(f'Connecting: {address}:{port}')
        scpi_socket.connect((address, port))
        log.info('Connected')

        super().__init__(scpi_socket)

addr_default = None
port_default = '5025'
@click.group()
@click.option('-a', '--ip-addr', default=addr_default, type=str, help=f"Target's IP address. Defualt={addr_default}.")
@click.option('-p', '--port', default=port_default, type=int, help=f"Target's TCP port. Defualt={port_default}.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
@click.pass_context
def cli(context, ip_addr, port, verbose):
    """CLI control of a SPD1000X power supply via TCP."""
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    if ip_addr is None:
        raise click.BadParameter(f'Use --ip-addr option', param_hint='--ip-addr')

    context.target = ScpiSocket(ip_addr, port)

@click.command()
@click.pass_context
def info(context):
    """Show the target's version strings."""
    print(context.parent.target.get_id())

cli.add_command(info)

if __name__ == '__main__':
    try:
        cli()
    except ScpiError as e:
        log.error(e)
        sys.exit(1)
