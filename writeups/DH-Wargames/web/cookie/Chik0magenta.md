---
ctf_name: "Dreamhack"
challenge_name: "Cookie"
category: "web"           # web / pwn / rev / crypto / misc
difficulty: "easy"      # easy / medium / hard / insane
author: "Chik0magenta"
date: "2026-05-05"
points: 0
tags: [cookie, authentication, logic-flaw]
---

# Cookie

## 문제 설명

> 쿠키로 인증 상태를 관리하는 간단한 로그인 서비스입니다. admin 계정으로 로그인에 성공하면 플래그를 획득할 수 있습니다.


## 풀이

### 분석

아래는 문제에서 주어진 app.py 전문이다.
```python
#!/usr/bin/python3
from flask import Flask, request, render_template, make_response, redirect, url_for

app = Flask(__name__)

try:
    FLAG = open('./flag.txt', 'r').read()
except:
    FLAG = '[**FLAG**]'

users = {
    'guest': 'guest',
    'admin': FLAG
}

@app.route('/')
def index():
    username = request.cookies.get('username', None)
    if username:
        return render_template('index.html', text=f'Hello {username}, {"flag is " + FLAG if username == "admin" else "you are not admin"}')
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            pw = users[username]
        except:
            return '<script>alert("not found user");history.go(-1);</script>'
        if pw == password:
            resp = make_response(redirect(url_for('index')) )
            resp.set_cookie('username', username)
            return resp 
        return '<script>alert("wrong password");history.go(-1);</script>'

app.run(host='0.0.0.0', port=8000)
```

### 취약점

index() 부분을 보면 admin을 검증하여 flag를 넘겨줄 때, 클라이언트가 전달한 username  쿠키 값만으로 판단한다.

### 익스플로잇

우선 id와 비밀번호를 알고 있는 guest 계정으로 로그인 후, 개발자 도구를 실행하여 쿠키를 확인한다. 이 서비스는 쿠키에 대한 무결성 검증(서명)이 없기 때문에, 사용자가 임의로 값을 변경해도 서버에서 이를 신뢰한다. guest로 되어 있는 username을 admin으로 변경 후 새로고침하면, 플래그를 얻을 수 있다.


## 플래그

```
DH{7952074b69ee388ab45432737f9b0c56}
```

## 배운 점

 - 클라이언트에서 전달되는 값(쿠키)을 신뢰할 경우 인증 우회가 발생할 수 있음을 이해했다.
 - 인증 정보는 서버 측 세션 또는 서명된 쿠키 등을 통해 무결성을 보장해야 함을 배웠다.