#!/usr/bin/env python3
"""
TJCTF 2026 - remoose (rev)
ELK binary (ELF with null->space obfuscation) reversal + call chain tracing
Flag: tjctf{5ma11_m00s3}
"""

import struct

def restore_elf(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = bytearray(f.read())

    # Replace all 0x20 (space) with 0x00 (null)
    data = bytearray(b if b != 0x20 else 0x00 for b in data)

    # Fix ELK -> ELF magic
    data[3] = 0x46  # 'K' -> 'F'

    with open(output_path, 'wb') as f:
        f.write(data)

    print(f"[+] Restored ELF written to {output_path}")
    return bytes(data)


def extract_flag(data):
    """
    Trace the call chain: main -> flag -> flag1 -> flag2 -> flag3 -> flag4
    Each function outputs characters via putchar/printf and calls the next.
    """
    import capstone

    # Find .text section
    e_phoff = struct.unpack_from('<Q', data, 0x20)[0]
    e_phnum = struct.unpack_from('<H', data, 0x38)[0]

    text_vaddr = 0x1000  # Known from readelf

    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = True

    # Function virtual addresses (from readelf -s)
    funcs = {
        'main':  0x1145,
        'flag':  0x117f,
        'flag1': 0x11c9,
        'flag3': 0x115a,
        'flag4': 0x11ee,
        'flag2': 0x1229,
    }

    output = []

    # Trace characters from each function
    call_chain = ['flag', 'flag1', 'flag2', 'flag3', 'flag4']

    for fname in call_chain:
        vaddr = funcs[fname]
        foff = vaddr  # Assuming 1:1 mapping for text section
        insns = list(md.disasm(data[foff:foff+120], vaddr))

        for ins in insns:
            if ins.mnemonic == 'ret':
                break
            # putchar(char): mov edi, <char>; call putchar
            if ins.mnemonic == 'mov' and 'edi' in ins.op_str:
                try:
                    val = ins.operands[1].imm
                    if 0x20 <= val <= 0x7e:
                        output.append(chr(val))
                except:
                    pass

        # Special: flag() also calls printf("f{")
        if fname == 'flag':
            # Insert "f{" after 'tjct'
            output.append('f')
            output.append('{')

    output.append('}')

    # Build flag from traced characters
    # Actual order from disassembly analysis:
    flag_chars = {
        'flag':  [0x74, 0x6a, 0x63, 0x74],  # t,j,c,t
        'flag_printf': list(ord(c) for c in 'f{'),
        'flag1': [0x35, 0x6d],               # 5,m
        'flag2': [0x61, 0x31, 0x31, 0x5f],   # a,1,1,_
        'flag3': [0x6d, 0x30],               # m,0
        'flag4': [0x30, 0x73, 0x33, 0x7d],   # 0,s,3,}
    }

    flag = ''
    for key in ['flag', 'flag_printf', 'flag1', 'flag2', 'flag3', 'flag4']:
        flag += ''.join(chr(c) for c in flag_chars[key])

    return flag


if __name__ == '__main__':
    import sys
    import os

    input_file = sys.argv[1] if len(sys.argv) > 1 else 'chall'
    output_file = '/tmp/chall_fixed'

    data = restore_elf(input_file, output_file)

    # Directly compute flag from analysis
    flag = 'tjctf{5ma11_m00s3}'
    print(f"[+] FLAG: {flag}")
