---
ctf_name: "TJCTF 2026"
challenge_name: "rotated"
category: "rev"
difficulty: "medium"
author: "ttzero25"
date: "2026-05-16"
points: 1000
tags: [byte rotation]
---

# rotated

## 문제 설명

> this file isn't making any sense to me. can you discover what it means? hint:look at the title hint hint2: consider each byte separately

- 바이너리 파일 chall 주어짐

## 풀이

### 분석

1. 주어진 chall 바이너리 파일을 `file` 명령어로 확인하면 ELF가 아닌 `data`로 인식되어 실행이 불가능

2. 파일 형식 분석 : 바이트 회전(Rotation)
- hex dump로 파일 앞부분을 확인하면 정상적인 ELF 파일과 다름을 확인
```
정상 ELF 매직: 7f 45 4c 46 02 01 01 00 ...
chall 앞부분:  9c 62 69 63 1f 1e 1e 1d ...
```

이 차이를 계산해보면 모든 바이트가 정확히 +0x1d(29)만큼 shift되어 있음
```
9c - 7f = 1d ✓
62 - 45 = 1d ✓
69 - 4c = 1d ✓
63 - 46 = 1d ✓
```

3. 따라서 문제 이름 `rotated`는 이를 의미하고, 각 바이트에서 0x1d를 빼면 ELF를 복원할 수 있음
```python
data = open('chall', 'rb').read()
recovered = bytes((b - 0x1d) % 256 for b in data)
open('chall_recovered', 'wb').write(recovered)
```

4. 복원 후 확인하면 UPX로 패킹된 ELF임을 알 수 있음
```
$ file chall_recovered
chall_recovered: ELF 64-bit LSB shared object, x86-64, statically linked, no section header

$ strings chall_recovered | grep UPX
UPX!
```

### 취약점

- 파일 인코딩 레이어가 3단계로 겹쳐 있음
1. 바이트 로테이션 — 전체 바이트에 +0x1d 적용
2. UPX 패킹 — 복원된 ELF가 UPX로 압축되어 있음
3. bash 난독화 스크립트 — 언패킹 후 내부에 eval 기반 난독화 스크립트 내장

언패킹 된 바이너리에서 `strings`로 확인하면 아래와 같은 난독화된 bash 스크립트가 나옴
```
#!/bin/bash
${*,} e\val "$(
    'p'r\i"n"tf 'H4sIAEDAzmkC/...(base64)...'
    | b""'a'''s"e"6"4 -d
    | \gu"n"z"i"p -c
)"
```

- e\val, b""'a'''s"e"6"4 — 문자열 분할로 명령어를 감춤
- ${*,}, ${@//...} — bash 파라미터 확장을 노이즈로 삽입
- 실제 동작: printf [base64] | base64 -d | gunzip

### 익스플로잇

```python
import base64, zlib

# 1단계: base64 디코딩 → gzip 압축 해제
b64 = 'H4sIAEDAzmkC/0tNzshXUPLJz8/OzEtXSMsvUkhUSMtJTLdX' \
      'UlBWSHEvyEpxjzKPzAo0THSzzPY18jL0y7Es8XMJNfY19rJ0Tre1' \
      'BQCGqZA9QQAAAA=='

compressed = base64.b64decode(b64)
content = zlib.decompress(compressed[10:], -15)  # raw deflate
print(content)
# b'echo "Looking for a flag?" # dGpjdGZ7YjQ1aF9kM2J1Nl9tNDU3M3J9Cg=='

# 2단계: 주석 속 base64 최종 디코딩
inner_b64 = 'dGpjdGZ7YjQ1aF9kM2J1Nl9tNDU3M3J9Cg=='
flag = base64.b64decode(inner_b64)
print(flag.decode())
```

## 플래그

```
tjctf{b45h_d3bu6_m4573r}
```

## 배운 점

- file 명령어가 data를 반환할 때 hex dump로 매직 바이트와 비교하면 인코딩 방식을 빠르게 특정할 수 있다.
- bash 난독화는 eval과 파라미터 확장을 제거하고 핵심 명령어만 추려내면 된다.