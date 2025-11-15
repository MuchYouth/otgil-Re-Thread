# setting

## 1. node.js + npm 설치

[https://nodejs.org/ko](https://nodejs.org/ko)

다운로드 후 설치 (따로 체크할거 없이 next 누르면서 진행)

## 2. git clone

[https://github.com/MuchYouth/Otgil-Re-Thread.git](https://github.com/MuchYouth/Otgil-Re-Thread.git)

## 3. run server

```bash
# 프로젝트폴더에서 frontend\src로 이동한 후에 진행
.\otgil_re_thread\frontend\src> npm install
.\otgil_re_thread\frontend\src> npm run dev
```

- localhost:3000으로 접속가능

# backend

## 1. python 설정

- vscode 기준
- 프로젝트 루트 밑에서 아래 명령어 입력

```bash
# Windows
python -m venv backend\venv

# macOS/Linux
python3 -m venv backend/venv
```

- backend 폴더 밑에 venv 폴더 있는지 확인

## 2. 가상환경 진입

1. `Ctrl+Shift+P` 키를 눌러 '명령 팔레트(Command Palette)' 열기
2. `Python: Select Interpreter` 검색 후 선택
3. 목록에서 `backend` 폴더 안에 있는 가상 환경을 선택
    - 뜨지 않는 경우 **`./backend/venv/bin/python`** 또는 **`backend\venv\Scripts\python.exe`**
        
        경로 직접 지정
        
4. 바뀌는게 없다면 ctrl + shift + (물결표시)로 reload
5. 터미널 커서 앞부분에 (venv) 로 변경되어야 성공

## 3. fast api 설치

- 가상환경 진입 상태에서

```bash
pip install fastapi uvicorn
pip install sqlalchemy, passlib
pip install pydantic
pip install 'pydantic[email]'
```

- ctrl + shift + d : 디버그 앤 실행

- create a launch.json file 링크 선택
- python > fastapi 선택 후 main 입력

파일 생성되면 내용을 아래 내용으로 바꾸기

```
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI (backend)",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": true,
      "cwd": "${workspaceFolder}/backend/"
    }
  ]
}
```

## 4. 서버열기

### 디버깅 없이 실행 모드 (ctrl+f5)

- 디버깅이라는 말이 어려우면 이 방법으로만 진행
- 디버깅 모드를 하고 싶다면 아래 방법 참고

### 디버깅 모드 (F5)

- 라인번호 옆에 중단점 (빨간색 동그라미) 설정

- f5 누르고, 터미널에 에러없이 뜨면 성공

## 5. 웹 열기

- [http://localhost:8000/docs](http://localhost:8000/docs) 으로 접속

<aside>
💡

- 현재 0.0.0.0:8000으로 서버를 연 건 나의 접속 아이피를 이용해 다른 장치가 접근할 수 있도록 서버를 연 것
- 서버를 연 컴퓨터는 본인 컴퓨터니까 [localhost](http://localhost) (본인 서버를 가리키는 문자열) 의 8000번포트에 접근하여 웹 을 열겠다는 의미
</aside>

끝!