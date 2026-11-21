#!/usr/bin/env python3
import sys
import subprocess
import time

SCANCODES = {
    'a': ['1e', '9e'], 'b': ['30', 'b0'], 'c': ['2e', 'ae'], 'd': ['20', 'a0'],
    'e': ['12', '92'], 'f': ['21', 'a1'], 'g': ['22', 'a2'], 'h': ['23', 'a3'],
    'i': ['17', '97'], 'j': ['24', 'a4'], 'k': ['25', 'a5'], 'l': ['26', 'a6'],
    'm': ['32', 'b2'], 'n': ['31', 'b1'], 'o': ['18', '98'], 'p': ['19', '99'],
    'q': ['10', '90'], 'r': ['13', '93'], 's': ['1f', '9f'], 't': ['14', '94'],
    'u': ['16', '96'], 'v': ['2f', 'af'], 'w': ['11', '91'], 'x': ['2d', 'ad'],
    'y': ['15', '95'], 'z': ['2c', 'ac'],
    '0': ['0b', '8b'], '1': ['02', '82'], '2': ['03', '83'], '3': ['04', '84'],
    '4': ['05', '85'], '5': ['06', '86'], '6': ['07', '87'], '7': ['08', '88'],
    '8': ['09', '89'], '9': ['0a', '8a'],
    ' ': ['39', 'b9'],
    '-': ['0c', '8c'],
    '_': ['2a', '0c', '8c', 'aa'],
    '=': ['0d', '8d'],
    '+': ['2a', '0d', '8d', 'aa'],
    '.': ['34', 'b4'],
    '>': ['2a', '34', 'b4', 'aa'],
    ',': ['33', 'b3'],
    '<': ['2a', '33', 'b3', 'aa'],
    '/': ['35', 'b5'],
    '?': ['2a', '35', 'b5', 'aa'],
    '\\': ['2b', 'ab'],
    '|': ['2a', '2b', 'ab', 'aa'],
    ';': ['27', 'a7'],
    ':': ['2a', '27', 'a7', 'aa'],
    "'": ['28', 'a8'],
    '"': ['2a', '28', 'a8', 'aa'],
    '`': ['29', 'a9'],
    '~': ['2a', '29', 'a9', 'aa'],
    '!': ['2a', '02', '82', 'aa'],
    '@': ['2a', '03', '83', 'aa'],
    '#': ['2a', '04', '84', 'aa'],
    '$': ['2a', '05', '85', 'aa'],
    '%': ['2a', '06', '86', 'aa'],
    '^': ['2a', '07', '87', 'aa'],
    '&': ['2a', '08', '88', 'aa'],
    '*': ['2a', '09', '89', 'aa'],
    '(': ['2a', '0a', '8a', 'aa'],
    ')': ['2a', '0b', '8b', 'aa'],
    '[': ['1a', '9a'],
    ']': ['1b', '9b'],
    '{': ['2a', '1a', '9a', 'aa'],
    '}': ['2a', '1b', '9b', 'aa'],
    '\n': ['1c', '9c']
}

def type_string(vm_name, text):
    codes = []
    for ch in text:
        if ch.isupper():
            low = ch.lower()
            if low in SCANCODES:
                codes.extend(['2a', SCANCODES[low][0], SCANCODES[low][1], 'aa'])
        elif ch in SCANCODES:
            codes.extend(SCANCODES[ch])
        elif ch == '\t':
            codes.extend(['0f', '8f'])
    
    if codes:
        cmd = ["VBoxManage", "controlvm", vm_name, "keyboardputscancode"] + codes
        subprocess.run(cmd, check=True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: send_vbox_cmd.py <command_string>")
        sys.exit(1)
    
    cmd_str = sys.argv[1]
    if not cmd_str.endswith('\n'):
        cmd_str += '\n'
    
    type_string("vyron os", cmd_str)
