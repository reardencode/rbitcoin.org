#!/usr/bin/env python3
"""Regenerate QR images from the displayed donation addresses.

Optional authoring tool: python3 -m pip install 'qrcode[pil]'
The committed website does not need Python packages or a build step.
"""
from html.parser import HTMLParser
from pathlib import Path

import qrcode

PUBLIC = Path(__file__).resolve().parents[1] / 'public'
ADDRESS_IDS = {'sp-donate', 'ln-strike', 'ln-cashapp'}


class Addresses(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = None
        self.values = {}

    def handle_starttag(self, tag, attrs):
        ident = dict(attrs).get('id')
        if tag == 'code' and ident in ADDRESS_IDS:
            self.active = ident
            self.values[ident] = ''

    def handle_data(self, data):
        if self.active:
            self.values[self.active] += data

    def handle_endtag(self, tag):
        if tag == 'code':
            self.active = None


def main():
    parser = Addresses()
    parser.feed((PUBLIC / 'about/index.html').read_text())
    if set(parser.values) != ADDRESS_IDS:
        raise ValueError('Expected all three donation addresses in about/index.html')
    for ident, address in parser.values.items():
        if not address or any(character.isspace() for character in address):
            raise ValueError(f'Unexpected whitespace or empty address: {ident}')
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=8, border=4)
        qr.add_data(address)
        qr.make(fit=True)
        qr.make_image(fill_color='black', back_color='white').convert('RGB').save(
            PUBLIC / 'assets/img' / f'qr-{ident}.png'
        )
        print(f'Generated qr-{ident}.png')


if __name__ == '__main__':
    main()
