---
ctf_name: "TJCTF"
challenge_name: "Treasure-hunt"
category: "web"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "Chik0magenta"
date: "2026-05-17"
points: 101
tags: [html, cookie, robots.txt]
---

# Cookie

## 문제 설명

> Let's go hunt down some treasure! The flag is split into 4 parts. I'll give you the first one right here: tjctf

treasure-hunt.tjc.tf

## 풀이

### 분석

문제 설명에서 플래그가 4개의 조각으로 나뉘어 있다고 알려 준다. 첫 번째 조각은 문제 설명에 직접 주어졌다.
```
tjctf
```

### 익스플로잇

브라우저 개발자 도구를 열어 웹사이트 쿠키를 확인해 보니, 다음의 값이 존재했다.
```
silber_coffer: {s1lv3r
```

아래는 페이지의 html 전문이다. 통상적인 방법으로는 확인할 수 없도록 hidden 속성이 부여된 요소 '_and_'가 있다. 
```
<html lang="en"><head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="/static/styles.css">
    <title>Pirates!</title>
</head>

<body>
    <h1>Learn about pirates!</h1>
    <h2>Wow!</h2>
    <form method="POST">
        <input type="submit" value="Learn More">
    </form>
    <img src="/static/ship.png" alt="ship">
    <p hidden="">_and_</p>

</body></html>
```

web CTF에서 자주 사용되는 /robots.txt 경로를 확인해 보니, 다음의 값이 존재했다.
```
User-agent: *
Disallow: /gold-coffer
Allow: /
```

/gold-coffer 경로로 접속해서 확인하니, 'g0ld}'를 얻을 수 있었다.

쿠키에 '{s1lv3r'
html 본문에 '_and_'
robots.txt에 'g0ld}'

## 플래그

```
tjctf{s1lv3r_and_g0ld}
```

## 배운 점

 - 웹사이트를 구성하는 기본적인 요소에 대해 복습할 수 있었다.