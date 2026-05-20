---
ctf_name: “tjctf"
challenge_name: "polaroid"
category: "rev"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "kimdohyeong0204"
date: "2026-05-17"
points: 115
tags: [x]
---

# 문제명
polaroid
## 문제 설명

> 문제에서 주어진 설명을 여기에 작성합니다.
this old polaroid won’t develop. it needs a password, and the password is somewhere on the film.

- 문제 URL / 파일 등 접속 정보
https://ctf.tjctf.org/challs
## 풀이
바이너리 파일을 Ghidra로 변환 후 password 획득 후 프로그램 실행을 통해 flag 획득
### 분석
문제에 password가 필요하다고 나와있지만 파일이 바이너리이기 때문에 직접 분석할 수 없다. 따라서 Ghidra를 사용해 코드로 변환 후 password를 획득해야 된다고 생각했다.
### 취약점
x

### 익스플로잇
분석 결과 password=exposeTheNegative 임을 확인할 수 있었음
polaroid 프로그램 실행 후 password 입력 후 flag.png 파일 획득

```python
x
```

## 플래그

```
tjctf{develop_the_picture}
```

## 배운 점
reversing 분야에도 관심을 가져 처음으로 rev 분야 문제를 풀어봤는데 이 분야에 대한 감을 조금 잡을 수 있는 기회였다


