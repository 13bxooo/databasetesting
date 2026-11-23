from pathlib import Path
import sqlite3

db_path = Path(__file__).resolve().parent / "records.db"

if not db_path.exists():
    print("records.db가 없습니다. 먼저 app.py를 실행하고 기록을 저장해 주세요.")
    raise SystemExit(0)

with sqlite3.connect(db_path) as conn:
    rows = conn.execute(
        "SELECT id, title, content, created_at FROM records ORDER BY id"
    ).fetchall()

print(f"데이터베이스 파일: {db_path.name}")
print(f"저장된 기록 수: {len(rows)}")

for row in rows:
    record_id, title, content, created_at = row
    print("-" * 40)
    print(f"ID: {record_id}")
    print(f"제목: {title}")
    print(f"내용: {content}")
    print(f"저장 시각: {created_at}")
