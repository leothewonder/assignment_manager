"""과제 마감일 알리미 (Assignment Deadline Manager - CLI & GUI)

실행 방법
    python assignment_manager.py          # GUI 모드 (기본)
    python assignment_manager.py --cli    # 콘솔(CLI) 모드
"""

import json
import os
import sys
import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "assignments.json")


# ---------------------------------------------------------------------------
# 공통 기능: 저장/불러오기, 날짜 계산, 정렬
# ---------------------------------------------------------------------------

def load_assignments() -> list:
    """저장된 과제 목록을 불러옵니다. 파일이 없으면 빈 목록을 반환합니다."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_assignments(assignments: list) -> None:
    """과제 목록을 파일에 저장합니다."""
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(assignments, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"안내: 파일 저장 중 오류가 발생했습니다: {e}")


def calculate_dday(deadline_str: str) -> str:
    """오늘 날짜 기준 D-day를 계산합니다 (D-3, D-Day, 마감 지남)."""
    try:
        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    except ValueError:
        return "날짜 오류"
    diff = (deadline_date - date.today()).days
    if diff > 0:
        return f"D-{diff}"
    elif diff == 0:
        return "D-Day"
    return "마감 지남"


def parse_date_input(date_str: str):
    """입력받은 날짜 문자열을 'YYYY-MM-DD'로 파싱합니다. 실패하면 None."""
    cleaned = date_str.strip().replace(".", "-").replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(cleaned, fmt).date().strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def sort_assignments(assignments: list) -> None:
    """과제 목록을 마감일이 가까운 순서대로 정렬합니다."""
    assignments.sort(key=lambda x: x.get("deadline", ""))


# ---------------------------------------------------------------------------
# 콘솔(CLI) 모드
# ---------------------------------------------------------------------------

def get_display_width(s: str) -> int:
    """한글/특수문자 너비를 고려한 출력 폭 계산."""
    return sum(2 if ord(c) > 127 else 1 for c in s)


def pad_str(s: str, target_width: int) -> str:
    """출력 폭에 맞게 공백을 채웁니다."""
    return s + " " * max(0, target_width - get_display_width(s))


def view_assignments(assignments: list) -> None:
    """마감이 가까운 순서로 과제 목록을 출력합니다."""
    sort_assignments(assignments)
    print("\n" + "=" * 60 + "\n                    [ 과제 목록 ]\n" + "=" * 60)
    if not assignments:
        print("  등록된 과제가 없습니다. 새로운 과제를 추가해보세요.\n" + "=" * 60)
        return
    print(f" {pad_str('번호', 6)}| {pad_str('D-Day', 12)}| {pad_str('마감일', 14)}| 과제 이름\n" + "-" * 60)
    for idx, item in enumerate(assignments, start=1):
        num_str = pad_str(str(idx), 6)
        dday_str = pad_str(calculate_dday(item.get("deadline", "")), 12)
        dl_str = pad_str(item.get("deadline", ""), 14)
        print(f" {num_str}| {dday_str}| {dl_str}| {item.get('title', '')}")
    print("=" * 60)


def add_assignment(assignments: list) -> None:
    """새 과제와 마감일을 입력받아 추가합니다."""
    print("\n[ 과제 추가 ]")
    title = input("과제 이름을 입력하세요 (취소: 엔터): ").strip()
    if not title:
        print("안내: 과제 이름이 입력되지 않아 메뉴로 돌아갑니다.")
        return
    raw_date = input("마감일을 입력하세요 (예: 2026-10-15): ").strip()
    parsed_date = parse_date_input(raw_date)
    if not parsed_date:
        print("안내: 잘못된 날짜 형식입니다. 'YYYY-MM-DD' 형식(예: 2026-10-15)으로 입력해주세요.")
        return
    assignments.append({"title": title, "deadline": parsed_date})
    sort_assignments(assignments)
    save_assignments(assignments)
    print(f"성공: 과제 '{title}' (마감일: {parsed_date})이(가) 등록되었습니다.")


def delete_assignment(assignments: list) -> None:
    """과제 번호를 입력받아 목록에서 삭제합니다."""
    print("\n[ 과제 삭제 ]")
    if not assignments:
        print("안내: 삭제할 과제가 없습니다.")
        return
    view_assignments(assignments)
    choice = input("\n삭제할 과제 번호를 입력하세요 (취소: 0): ").strip()
    try:
        idx = int(choice)
    except ValueError:
        print("안내: 올바른 숫자를 입력해주세요. 메뉴로 돌아갑니다.")
        return
    if idx == 0:
        print("삭제를 취소했습니다.")
        return
    if 1 <= idx <= len(assignments):
        deleted = assignments.pop(idx - 1)
        save_assignments(assignments)
        print(f"성공: 과제 '{deleted['title']}'이(가) 삭제되었습니다.")
    else:
        print(f"안내: 없는 과제 번호입니다. 1부터 {len(assignments)} 사이의 번호를 입력해주세요.")


def print_menu() -> None:
    """메인 메뉴 출력."""
    print("\n" + "=" * 32 + "\n      과제 마감일 알리미\n" + "=" * 32)
    print(" 1. 과제 목록 보기\n 2. 과제 추가\n 3. 과제 삭제\n 4. 종료")
    print(" (GUI 실행: g 입력)")
    print("=" * 32)


def run_cli() -> None:
    """콘솔 메인 실행 루프."""
    assignments = load_assignments()
    sort_assignments(assignments)
    print("과제 마감일 알리미 프로그램을 시작합니다.")
    while True:
        try:
            print_menu()
            choice = input("원하는 메뉴 번호를 입력하세요 (1-4): ").strip()
            if choice == "1":
                view_assignments(assignments)
            elif choice == "2":
                add_assignment(assignments)
            elif choice == "3":
                delete_assignment(assignments)
            elif choice == "4":
                save_assignments(assignments)
                print("과제 목록을 파일에 저장했습니다. 프로그램을 종료합니다.")
                break
            elif choice.lower() in ("g", "gui"):
                run_gui()
                assignments = load_assignments()
                sort_assignments(assignments)
            else:
                print("안내: 없는 메뉴 번호입니다. 1에서 4 사이의 숫자를 입력해주세요.")
        except (KeyboardInterrupt, EOFError):
            print("\n\n프로그램을 종료합니다.")
            save_assignments(assignments)
            break


# ---------------------------------------------------------------------------
# GUI 모드
# ---------------------------------------------------------------------------

class AssignmentGUIApp:
    """과제 마감일 알리미 GUI 애플리케이션."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("과제 마감일 알리미")
        self.root.geometry("640x520")
        self.root.minsize(560, 420)

        self.assignments = load_assignments()
        sort_assignments(self.assignments)

        self.setup_ui()
        self.refresh_table()

        # 창을 닫을 때 저장
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # 상단 입력 영역
        input_frame = ttk.LabelFrame(self.root, text="새 과제 등록", padding=12)
        input_frame.pack(fill="x", padx=14, pady=10)

        ttk.Label(input_frame, text="과제 이름:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.title_entry = ttk.Entry(input_frame, width=28)
        self.title_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(input_frame, text="마감일 (YYYY-MM-DD):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=16)
        self.date_entry.grid(row=0, column=3, sticky="ew", padx=5, pady=5)
        self.date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        ttk.Button(input_frame, text="과제 추가", command=self.add_task).grid(row=0, column=4, padx=8, pady=5)

        # 엔터 키로도 추가
        self.title_entry.bind("<Return>", lambda e: self.add_task())
        self.date_entry.bind("<Return>", lambda e: self.add_task())

        # 과제 목록 테이블
        table_frame = ttk.Frame(self.root, padding=14)
        table_frame.pack(fill="both", expand=True)

        columns = ("num", "dday", "deadline", "title")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col, heading, width, anchor in [
            ("num", "번호", 60, "center"),
            ("dday", "D-Day", 100, "center"),
            ("deadline", "마감일", 120, "center"),
            ("title", "과제 이름", 300, "w"),
        ]:
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor=anchor)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 마감 상태에 따른 행 색상
        self.tree.tag_configure("overdue", background="#ffebee", foreground="#c62828")
        self.tree.tag_configure("today", background="#fff9c4", foreground="#b78103")
        self.tree.tag_configure("urgent", background="#fff3e0", foreground="#e65100")

        # 하단 버튼과 상태 표시
        bottom_frame = ttk.Frame(self.root, padding=12)
        bottom_frame.pack(fill="x")

        ttk.Button(bottom_frame, text="선택한 과제 삭제", command=self.delete_selected).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="새로고침", command=self.refresh_table).pack(side="left", padx=5)

        self.status_label = ttk.Label(bottom_frame, text="", foreground="gray")
        self.status_label.pack(side="right", padx=5)

        self.tree.bind("<Delete>", lambda e: self.delete_selected())

    def get_tag(self, dday: str) -> str:
        """D-day 문자열에 맞는 색상 태그를 돌려줍니다."""
        if dday == "마감 지남":
            return "overdue"
        if dday == "D-Day":
            return "today"
        if dday.startswith("D-") and int(dday.split("-")[1]) <= 3:
            return "urgent"
        return ""

    def refresh_table(self):
        """목록을 다시 정렬하고 테이블을 갱신합니다."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        sort_assignments(self.assignments)

        for idx, task in enumerate(self.assignments, start=1):
            deadline = task.get("deadline", "")
            dday = calculate_dday(deadline)
            title = task.get("title", "")
            self.tree.insert("", "end", values=(idx, dday, deadline, title),
                             tags=(self.get_tag(dday),))

        self.status_label.config(text=f"총 {len(self.assignments)}개의 과제")

    def add_task(self):
        """과제 추가 처리."""
        title = self.title_entry.get().strip()
        date_raw = self.date_entry.get().strip()

        if not title:
            messagebox.showwarning("입력 안내", "과제 이름을 입력해주세요.")
            self.title_entry.focus()
            return

        parsed_date = parse_date_input(date_raw)
        if not parsed_date:
            messagebox.showwarning("날짜 오류", "올바른 날짜 형식(YYYY-MM-DD)으로 입력해주세요.\n예: 2026-10-15")
            self.date_entry.focus()
            return

        self.assignments.append({"title": title, "deadline": parsed_date})
        sort_assignments(self.assignments)
        save_assignments(self.assignments)
        self.refresh_table()

        self.title_entry.delete(0, tk.END)
        self.status_label.config(text=f"'{title}' 과제가 추가되었습니다.")
        self.title_entry.focus()

    def delete_selected(self):
        """선택된 과제 삭제 처리."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("안내", "삭제할 과제를 목록에서 클릭해 선택해주세요.")
            return

        values = self.tree.item(selected[0]).get("values", [])
        if not values:
            return

        idx = int(values[0]) - 1
        deleted = self.assignments.pop(idx)
        save_assignments(self.assignments)
        self.refresh_table()
        self.status_label.config(text=f"'{deleted['title']}' 과제가 삭제되었습니다.")

    def on_close(self):
        """창을 닫을 때 저장하고 종료."""
        save_assignments(self.assignments)
        self.root.destroy()


def run_gui() -> None:
    """GUI 모드로 애플리케이션을 실행합니다."""
    root = tk.Tk()
    AssignmentGUIApp(root)
    root.mainloop()


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()
