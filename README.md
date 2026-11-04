# 과제 마감일 알리미

과제 이름과 마감일을 입력하면 남은 날짜를 D-day로 보여주고, 마감이 가까운 순서로 정렬해 주는 프로그램이다. 5주차에 만든 프로그램에 이번에 공휴일 API를 붙여서, 마감까지 남은 평일 수와 마감일이 주말이나 공휴일인지도 같이 보이도록 업데이트했다. 이번 기획안은 `api-plan.md`에 있다.

## 실행 방법

uv가 설치되어 있으면 아래 명령으로 실행할 수 있다. 파이썬 3.14와 requests 라이브러리는 uv가 `pyproject.toml`과 `uv.lock`을 보고 알아서 설치한다.

```bash
git clone https://github.com/leothewonder/assignment_manager.git
cd assignment_manager
uv run assignment_manager.py         # 창(GUI) 모드
uv run assignment_manager.py --cli   # 콘솔 모드
```

사용한 Nager.Date API는 키가 필요 없어서 `.env` 파일은 만들지 않아도 된다. 인터넷이 안 되면 공휴일 기능만 빠지고 나머지 기능은 그대로 쓸 수 있다.

## 파일 구성

- `assignment_manager.py`: 메인 프로그램 (과제 관리, 콘솔 화면, 창 화면)
- `holiday_api.py`: 공휴일 API를 부르고 평일 수를 계산하는 모듈 (이번에 추가)
- `pyproject.toml`, `uv.lock`, `.python-version`: uv 실행 환경 설정
- `api-plan.md`: 이번 기획안 / `plan-1 (1).md`, `newplan2.md`: 이전 기획안
- `conversation_log.md`: AI와 나눈 대화 기록

실행하면 `assignments.json`(과제 목록)과 `holidays_cache.json`(공휴일 저장본)이 생긴다. 개인 데이터라서 `.gitignore`에 넣어 저장소에는 올리지 않았다.

## 코드 설명

### assignment_manager.py

과제 하나는 `{"title": "물리 레포트", "deadline": "2026-11-13"}` 같은 딕셔너리이고, 전체 과제는 이 딕셔너리들의 리스트로 관리한다.

`load_assignments()`는 `assignments.json`을 읽어서 과제 리스트를 돌려준다. 파일이 없거나 내용이 깨져 있으면 빈 리스트를 돌려줘서 처음 실행해도 멈추지 않는다. `save_assignments()`는 과제를 추가하거나 지울 때마다 불러서 바로 파일에 저장한다.

`parse_date_input()`은 날짜를 `2026.11.13`, `2026/11/13`, `20261113`처럼 입력해도 `2026-11-13` 형식으로 바꿔 준다. 형식이 틀리면 None을 돌려주고, 그러면 안내 문구를 보여준 뒤 메뉴로 돌아간다. `calculate_dday()`는 마감일에서 오늘 날짜를 빼서 `D-3`, `D-Day`, `마감 지남` 중 하나로 표시한다. `sort_assignments()`는 마감일 문자열로 정렬하는데, 날짜를 `YYYY-MM-DD` 형식으로 통일해 두었기 때문에 글자 순서로 정렬해도 날짜 순서와 같다.

콘솔 모드는 `run_cli()`가 메뉴를 반복해서 보여주고, 입력한 번호에 따라 목록 보기, 추가, 삭제, 다가오는 공휴일 보기, 종료를 실행한다. 한글은 영어보다 화면에서 두 칸을 차지해서 표가 어긋나는데, `get_display_width()`와 `pad_str()`로 한글을 2칸으로 계산해서 칸을 맞췄다.

창 모드는 tkinter로 만든 `AssignmentGUIApp` 클래스다. 위쪽 입력칸에서 과제를 추가하고, 가운데 표(Treeview)에 목록을 보여준다. `get_tag()`에서 D-day에 따라 색을 정해서, 마감이 지난 과제는 빨간색, 오늘 마감은 노란색, 3일 이내는 주황색으로 보인다. 창을 닫을 때는 `on_close()`에서 저장하고 끝낸다.

### holiday_api.py

`fetch_holidays(year)`가 실제로 API를 부르는 함수다.

```python
response = requests.get(API_URL.format(year=year), timeout=TIMEOUT_SECONDS)
response.raise_for_status()
items = response.json()
```

`https://date.nager.at/api/v3/PublicHolidays/2026/KR`처럼 연도를 넣은 주소로 요청을 보내고, 받은 JSON에서 날짜와 한국어 이름(`localName`)만 꺼내 `{"2026-12-25": "기독탄신일"}` 같은 딕셔너리로 만든다. 딕셔너리로 만든 이유는 어떤 날이 공휴일인지 `날짜 in holidays`로 바로 확인할 수 있어서다. `timeout=5`를 줘서 서버가 응답하지 않아도 5초 뒤에는 넘어가게 했고, 연결 실패나 404·500 같은 오류 응답, 잘못된 JSON은 `except`로 잡아서 None을 돌려준다.

`load_holidays(years)`는 매번 API를 부르지 않으려고 만든 함수다. 받아온 공휴일을 받은 날짜와 함께 `holidays_cache.json`에 저장해 두고, 7일이 안 지났으면 저장된 것을 쓴다. 7일이 지났거나 저장된 게 없으면 API를 부르고, API가 실패하면 예전 저장본이라도 쓴다. 저장본도 없으면 공휴일 없이 동작하고 화면에 "공휴일 정보 없음"이라고 알려준다. 어떤 연도를 받아올지는 `years_needed()`가 올해, 내년, 과제 마감일의 연도를 모아서 정한다.

나머지는 계산하는 함수다. `count_workdays()`는 오늘부터 마감일까지 하루씩 넘기면서 월~금요일(`weekday() < 5`)이고 공휴일이 아닌 날만 센다. `day_note()`는 마감일이 공휴일이면 그 이름을, 토요일이나 일요일이면 요일을 돌려준다. `upcoming_holidays()`는 앞으로 60일 안의 공휴일을 날짜순으로 모은다.

### 두 파일이 연결되는 부분

프로그램을 켜면 먼저 `load_holidays()`로 공휴일을 받아 둔다. 목록을 그릴 때마다 과제별로 `count_workdays()`와 `day_note()`를 불러서 "평일"과 "비고" 칸을 채운다. 과제를 추가할 때는 `add_assignment()`가 새 마감일을 돌려주도록 바꿨고, 그 날짜가 쉬는 날이면 `warn_if_day_off()`로 미리 끝내두라는 안내를 보여준다.

## 아쉬운 점

Nager.Date는 해외 서비스라서 선거일 같은 임시공휴일이 빠질 수 있다. 학교 휴강일이나 시험 기간도 반영하지 못한다.
