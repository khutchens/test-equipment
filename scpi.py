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
        except (socket.timeout, TimeoutError):
            raise ScpiError(f'Query failed: timeout, command: {command_line}');

        log.info(f'SCPI response: {response}')
        return response

    def set(self, command):
        command_line = command.rstrip()
        command_delimited = command + '\n'
        log.info(f'SCPI set: {command_line }')

        try:
            self._device.send(command_delimited.encode('utf-8'))
        except (socket.timeout, TimeoutError):
            raise ScpiError(f'Set failed: timeout, command: {command_line}');

        #code, message = self.query('SYST:ERR?').split(',', 1)
        #if int(code) != 0:
        #    raise ScpiError(f'SCPI set failed, command:"{command}", result:{code},"{message}"')

    def get_id(self):
        return self.query('*IDN?').split(',')

class ScpiSocket(Scpi):
    def __init__(self, tcp_addr):
        tokens = tcp_addr.split(':')
        if len(tokens) == 1:
            addr, port = tokens[0], 5025
        elif len(tokens) == 2:
            addr, port = tokens[0], int(tokens[1])
        else:
            raise ScpiError(f'Malformed address: {tcp_addr}')

        scpi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        scpi_socket.settimeout(1.000)

        log.info(f'Connecting: {addr}:{port}')
        scpi_socket.connect((addr, port))
        log.info('Connected')

        super().__init__(scpi_socket)

class ScpiUsb(Scpi):
    class UsbSocket:
        def __init__(self, usb_device_path):
            self._fd = os.open(usb_device_path, os.O_RDWR)

        def __del__(self):
            if hasattr(self, 'self._fd'):
                os.close(self._fd)

        def send(self, data):
            os.write(self._fd, data)

        def recv(self, max_length):
            return os.read(self._fd, max_length)

    def __init__(self, usb_device_path):
        log.info(f'Opening: {usb_device_path}')
        super().__init__(self.UsbSocket(usb_device_path))

@click.group()
@click.option('-t', '--tcp-addr', type=str, help=f"Target IP address.")
@click.option('-u', '--usb-device', type=str, help=f"Target USB device.")
@click.option('-v/-q', '--verbose/--quiet', default=False, help="Adjust output verbosity.")
@click.pass_context
def cli(context, tcp_addr, usb_device, verbose):
    """CLI control of SCPI devices over TCP or USB."""
    if verbose:
        logging.getLogger('').setLevel(logging.DEBUG)

    if tcp_addr:
        context.target = ScpiSocket(tcp_addr)
    elif usb_device:
        context.target = ScpiUsb(usb_device)
    else:
        raise click.BadParameter('TCP address or USB device required.')

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
