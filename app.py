from pathlib import Path
import sqlite3
import streamlit as st

# 웹앱과 같은 폴더에 SQLite 데이터베이스 파일을 생성한다.
DB_PATH = Path(__file__).resolve().parent / "records.db"


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )


def get_records():
    with connect_db() as conn:
        return conn.execute(
            "SELECT id, title, content, created_at FROM records ORDER BY id DESC"
        ).fetchall()


def add_record(title, content):
    with connect_db() as conn:
        conn.execute(
            "INSERT INTO records (title, content) VALUES (?, ?)",
            (title, content),
        )


def update_record(record_id, title, content):
    with connect_db() as conn:
        conn.execute(
            "UPDATE records SET title = ?, content = ? WHERE id = ?",
            (title, content, record_id),
        )


def delete_record(record_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM records WHERE id = ?", (record_id,))


initialize_db()

st.set_page_config(page_title="SQLite CRUD 실험", page_icon="🗃️", layout="centered")
st.title("SQLite 데이터베이스 실험")
st.write("간단한 기록을 저장·조회·수정·삭제하며 웹앱과 데이터베이스의 연결 방식을 확인합니다.")
st.caption("저장 방식: SQLite 파일(records.db) · 사용 모듈: Python 기본 제공 sqlite3")
st.divider()

save_tab, manage_tab = st.tabs(["기록 저장", "기록 조회·수정·삭제"])

with save_tab:
    st.subheader("새 기록 저장")
    with st.form("add_record_form", clear_on_submit=True):
        title = st.text_input("제목", placeholder="예: 첫 번째 데이터")
        content = st.text_area("내용", placeholder="데이터베이스에 저장할 내용을 입력하세요.")
        submitted = st.form_submit_button("데이터베이스에 저장", type="primary")

    if submitted:
        if not title.strip() or not content.strip():
            st.warning("제목과 내용을 모두 입력해 주세요.")
        else:
            add_record(title.strip(), content.strip())
            st.success("데이터베이스에 저장했습니다.")
            st.rerun()

with manage_tab:
    st.subheader("저장된 기록")
    records = get_records()

    if not records:
        st.info("저장된 기록이 없습니다. '기록 저장' 탭에서 먼저 데이터를 추가해 주세요.")
    else:
        record_by_id = {record["id"]: record for record in records}
        selected_id = st.selectbox(
            "확인할 기록 선택",
            options=list(record_by_id.keys()),
            format_func=lambda rid: f'#{rid} · {record_by_id[rid]["title"]}',
        )
        selected = record_by_id[selected_id]

        st.markdown("**데이터베이스에서 조회한 값**")
        st.write(f'제목: {selected["title"]}')
        st.write(f'내용: {selected["content"]}')
        st.caption(f'기록 번호: {selected["id"]} · 저장 시각: {selected["created_at"]}')

        st.divider()
        st.markdown("**기록 수정**")
        with st.form(f"edit_form_{selected_id}"):
            edited_title = st.text_input("수정할 제목", value=selected["title"])
            edited_content = st.text_area("수정할 내용", value=selected["content"])
            update_clicked = st.form_submit_button("수정 내용 저장")

        if update_clicked:
            if not edited_title.strip() or not edited_content.strip():
                st.warning("제목과 내용을 모두 입력해 주세요.")
            else:
                update_record(selected_id, edited_title.strip(), edited_content.strip())
                st.success("데이터를 수정했습니다.")
                st.rerun()

        st.divider()
        st.markdown("**기록 삭제**")
        confirm_delete = st.checkbox("선택한 기록을 삭제하겠습니다.", key=f"confirm_delete_{selected_id}")
        if st.button("선택한 기록 삭제", disabled=not confirm_delete, key=f"delete_button_{selected_id}"):
            delete_record(selected_id)
            st.success("데이터를 삭제했습니다.")
            st.rerun()

st.divider()
st.caption(f"데이터베이스 파일: {DB_PATH.name} · 파일은 이 프로그램과 같은 폴더에 저장됩니다.")
