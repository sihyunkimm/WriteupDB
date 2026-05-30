---
ctf_name: "Dreamhack"
challenge_name: "Inject ME!!!"
category: "rev"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "ssong17"
date: "2026-05-26"
points: -
tags: [태그1, 태그2]
---

# 문제명

## 문제 설명

드림이가 수상한 DLL 파일을 획득하였습니다.

DLL 파일과 함께 있던 TXT 파일에는 조건을 맞춰서 DLL을 로드시키면 플래그를 얻을 수 있다고만 쓰여 있었습니다.

어떻게 해야 DLL 파일을 로드할 수 있을까요?

- 문제 URL / 파일 등 접속 정보: prob_rev.dll 파일

## 풀이

### 분석

prob_rev.dll 파일이 주어졌으며, 특정 조건을 만족해야 플래그를 획득할 수 있다는 힌트만 존재했다.
 
디버거로 DLL을 열어 분석하던 중, 내부 문자열로 `dreamhack.exe`와 `flag` 관련 문자열을 발견하였다.
 
DLL을 로드하는 실행 파일의 이름을 확인하는 로직이 존재하며, 해당 이름이 `dreamhack.exe`일 경우 플래그 출력 루틴이 실행되는 구조였다.
 
구체적으로는 `RAX` 레지스터에 실행 파일 이름이 담겨 조건 분기에 사용되고 있었다.


### 취약점

DLL 내부에서 자신을 로드한 프로세스의 이름을 문자열 비교로 검증하는 방식을 사용하고 있다. 

이 검증은 암호학적 인증이나 무결성 체크가 아닌 단순 문자열 비교이므로, 해당 이름을 가진 실행 파일을 직접 만들어 DLL을 로드하는 것만으로도 우회가 가능하다.

### 익스플로잇

실행 파일에서 `prob_rev.dll`을 명시적으로 로드하는 C 코드를 작성하여 컴파일 및 실행하였다.

**환경 구성**
 
```bash
# MSYS2 설치 후 MinGW 64-bit 터미널에서 실행
pacman -Syu
pacman -S mingw-w64-x86_64-gcc
``` 

```c
#include <windows.h>
#include <stdio.h>
 
int main() {
    HMODULE hDll = LoadLibraryA("prob_rev.dll");
    if (hDll == NULL) {
        printf("DLL 로드 실패: %lu\n", GetLastError());
        return 1;
    }
    printf("DLL 로드 성공\n");
    FreeLibrary(hDll);
    return 0;
}
```

**컴파일 및 실행**
 
```bash
gcc dreamhack.c -o dreamhack.exe
./dreamhack.exe
```

## 플래그

```
DH{reng@r_is_cute}
```

## 배운 점

.
