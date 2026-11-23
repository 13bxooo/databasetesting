from pathlib import Path
import sqlite3

db_path = Path(__file__).resolve().parent / "records.db"

if not db_path.exists():
    print("records.db가 없습니다. 먼저 app.py를 실행하고 기록을 저장해 주세요.")
    raise SystemExit(0)

with sqlite3.connect(db_path) as conn:
    structure = conn.execute("PRAGMA table_info(records)").fetchall()
    rows = conn.execute(
        "SELECT id, title, content, created_at FROM records ORDER BY id"
    ).fetchall()

print("=== records 테이블 구조 ===")
for column in structure:
    print(
        f"열 이름: {column[1]}, 자료형: {column[2]}, "
        f"NOT NULL: {column[3]}, 기본값: {column[4]}, 기본 키: {column[5]}"
    )

print(f"\n=== 저장된 데이터: {len(rows)}개 ===")
for row in rows:
    print("-" * 40)
    print(f"ID: {row[0]}")
    print(f"제목: {row[1]}")
    print(f"내용: {row[2]}")
    print(f"저장 시각: {row[3]}")
