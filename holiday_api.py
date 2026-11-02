"""공휴일 API 모듈 (Nager.Date)

한국 공휴일 정보를 Nager.Date API에서 받아와 파일에 저장해 두고,
마감까지 남은 평일 수와 마감일이 쉬는 날인지를 계산합니다.
API 키는 필요 없습니다.
"""

import json
import os
from datetime import date, datetime, timedelta

import requests

API_URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/KR"
TIMEOUT_SECONDS = 5      # 서버가 응답하지 않을 때 기다리는 최대 시간
CACHE_DAYS = 7           # 받아온 지 7일이 안 된 정보는 다시 받지 않음

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "holidays_cache.json")

WEEKDAY_NAMES = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

# 공휴일 정보 상태 (화면에 안내할 때 사용)
STATUS_FRESH = "최신 공휴일 정보"
STATUS_OLD = "저장된 공휴일 정보 사용 (공휴일 서버 연결 실패)"
STATUS_NONE = "공휴일 정보 없음 (공휴일 서버 연결 실패)"


# ---------------------------------------------------------------------------
# 저장 파일(캐시) 읽기/쓰기
# ---------------------------------------------------------------------------

def load_cache() -> dict:
    """저장된 공휴일 정보를 불러옵니다. 형식: {"2026": {"fetched": "2026-11-02", "holidays": {...}}}"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache: dict) -> None:
    """공휴일 정보를 파일에 저장합니다."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # 저장에 실패해도 이번 실행에서는 받아온 정보를 그대로 쓸 수 있음


def is_fresh(entry: dict) -> bool:
    """저장된 정보가 CACHE_DAYS일 안에 받아온 것인지 확인합니다."""
    try:
        fetched = datetime.strptime(entry.get("fetched", ""), "%Y-%m-%d").date()
    except ValueError:
        return False
    return (date.today() - fetched).days < CACHE_DAYS


# ---------------------------------------------------------------------------
# API 호출
# ---------------------------------------------------------------------------

def fetch_holidays(year: int):
    """API에서 해당 연도의 한국 공휴일을 받아옵니다.

    성공하면 {"2026-10-03": "개천절", ...} 형태의 딕셔너리,
    인터넷 연결 실패나 잘못된 응답이면 None을 돌려줍니다.
    """
    try:
        response = requests.get(API_URL.format(year=year), timeout=TIMEOUT_SECONDS)
        response.raise_for_status()      # 404, 500 같은 오류 응답이면 예외 발생
        items = response.json()          # JSON 글자를 파이썬 리스트로 변환
    except (requests.RequestException, ValueError):
        return None
    if not isinstance(items, list):
        return None

    holidays = {}
    for item in items:
        day = item.get("date")
        name = item.get("localName") or item.get("name") or "공휴일"
        if not day:
            continue
        # 같은 날 공휴일이 두 개면 이름을 이어 붙임
        if day in holidays and name not in holidays[day]:
            holidays[day] += ", " + name
        else:
            holidays[day] = name
    return holidays


def load_holidays(years, force: bool = False):
    """필요한 연도들의 공휴일을 모아 돌려줍니다.

    저장된 정보가 최신이면 그대로 쓰고, 아니면 API를 부릅니다.
    API 호출에 실패하면 예전에 저장한 정보로 대신합니다.
    force=True이면 저장된 정보와 상관없이 API를 다시 부릅니다.

    돌려주는 값: (공휴일 딕셔너리, 상태 문구)
    """
    cache = load_cache()
    merged = {}
    status = STATUS_FRESH
    changed = False

    for year in sorted(set(years)):
        key = str(year)
        entry = cache.get(key)

        if entry and is_fresh(entry) and not force:
            merged.update(entry.get("holidays", {}))
            continue

        fetched = fetch_holidays(year)
        if fetched is not None:
            cache[key] = {"fetched": date.today().strftime("%Y-%m-%d"), "holidays": fetched}
            merged.update(fetched)
            changed = True
        elif entry:
            merged.update(entry.get("holidays", {}))
            if status == STATUS_FRESH:
                status = STATUS_OLD
        else:
            status = STATUS_NONE

    if changed:
        save_cache(cache)
    return merged, status


def years_needed(assignments: list) -> list:
    """올해, 내년, 그리고 과제 마감일에 들어 있는 연도를 모읍니다."""
    this_year = date.today().year
    years = {this_year, this_year + 1}
    for item in assignments:
        deadline = item.get("deadline", "")
        if len(deadline) >= 4 and deadline[:4].isdigit():
            years.add(int(deadline[:4]))
    return sorted(years)


# ---------------------------------------------------------------------------
# 계산 기능
# ---------------------------------------------------------------------------

def day_note(deadline_str: str, holidays: dict) -> str:
    """마감일이 쉬는 날이면 공휴일 이름이나 '토요일'/'일요일'을, 아니면 빈 문자열을 돌려줍니다."""
    if deadline_str in holidays:
        return holidays[deadline_str]
    try:
        weekday = datetime.strptime(deadline_str, "%Y-%m-%d").weekday()
    except ValueError:
        return ""
    if weekday >= 5:                     # 5 = 토요일, 6 = 일요일
        return WEEKDAY_NAMES[weekday]
    return ""


def count_workdays(deadline_str: str, holidays: dict, today: date = None) -> str:
    """오늘부터 마감일까지(마감일 포함) 주말·공휴일을 뺀 평일 수를 글자로 돌려줍니다.

    마감이 지났거나 날짜가 잘못되었으면 "-"를 돌려줍니다.
    """
    today = today or date.today()
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return "-"
    if deadline < today:
        return "-"

    count = 0
    day = today
    while day <= deadline:
        if day.weekday() < 5 and day.strftime("%Y-%m-%d") not in holidays:
            count += 1
        day += timedelta(days=1)
    return f"{count}일"


def upcoming_holidays(holidays: dict, days: int = 60, today: date = None) -> list:
    """오늘부터 days일 안의 공휴일을 [(날짜, 요일, 이름), ...] 형태로 날짜순 정렬해 돌려줍니다."""
    today = today or date.today()
    end = today + timedelta(days=days)
    result = []
    for day_str, name in holidays.items():
        try:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
        except ValueError:
            continue
        if today <= day <= end:
            result.append((day_str, WEEKDAY_NAMES[day.weekday()], name))
    result.sort()
    return result
