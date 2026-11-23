from contextlib import contextmanager
from pathlib import Path
import sqlite3

import streamlit as st

# SQLite 파일은 이 앱 파일과 같은 폴더에 저장한다.
DB_PATH = Path(__file__).resolve().parent / "records.db"


@contextmanager
def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_db():
    # 기존 데이터는 유지하고 테이블이 없을 때만 생성한다.
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


def get_table_sql():
    with connect_db() as conn:
        result = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'records'"
        ).fetchone()
    return result["sql"] if result else "테이블 정의를 찾을 수 없습니다."


def get_table_columns():
    with connect_db() as conn:
        return conn.execute("PRAGMA table_info(records)").fetchall()


def node(title, detail, code=None):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(detail)
        if code:
            st.code(code, language="text")


def arrow(label="데이터 전달"):
    st.markdown(
        f"<div style='text-align:center;color:#718096;padding:3px 0;'>"
        f"<div style='font-size:24px;line-height:1;'>↓</div>"
        f"<div style='font-size:12px;'>{label}</div></div>",
        unsafe_allow_html=True,
    )


def info_card(title, detail):
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(detail)


initialize_db()

st.set_page_config(
    page_title="데이터 저장 방식 비교 탐구",
    page_icon="🗃️",
    layout="wide",
)

st.title("웹 애플리케이션의 데이터 저장 방식 탐구")
st.write(
    "PROJECT : LOGIC에서 사용한 브라우저 저장 방식과 "
    "별도로 구현한 SQLite 데이터베이스의 저장 구조를 시각적으로 비교합니다."
)
st.caption("Python · Streamlit · JavaScript localStorage · SQLite")

st.info(
    "핵심 구분: 기존 게임은 상세 진행 정보를 브라우저 localStorage에 JSON 형태로 저장했고, "
    "Streamlit의 st.session_state는 페이지·세션 상태를 관리했습니다. "
    "이번 실험은 SQLite 파일에 데이터를 테이블 형태로 저장합니다."
)

visual_tab, crud_tab, structure_tab = st.tabs(
    ["저장 방식 시각화", "SQLite 직접 실험", "SQLite 내부 구조"]
)

with visual_tab:
    st.subheader("① 기존 PROJECT : LOGIC의 저장 방식")
    st.write(
        "게임의 상세 진행 정보와 Streamlit의 페이지 상태는 서로 다른 역할을 맡았습니다."
    )

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("#### A. 게임 진행 정보 저장")
        node("게임에서 상태 변화 발생", "플레이어 위치 · 남은 시간 · 퍼즐 상태 · 인벤토리")
        arrow("JavaScript 함수가 저장할 값을 모음")
        node(
            "JSON 문자열로 변환",
            "객체 형태의 진행 정보를 문자열로 직렬화",
            "JSON.stringify({ playerX, playerY, seconds, codeSolved, puzzle, found, items, inventory })",
        )
        arrow("localStorage.setItem()")
        node(
            "브라우저 localStorage",
            "브라우저 저장 공간에 키와 값으로 기록",
            'key: "project_logic_stage01_save_v1"',
        )
        st.caption(
            "저장된 값은 같은 브라우저 저장 공간에서 다시 읽어 JSON.parse()로 객체로 복원합니다."
        )
        st.code(
            'const saved = JSON.parse(\n'
            '  localStorage.getItem("project_logic_stage01_save_v1")\n'
            ');',
            language="javascript",
        )

    with right:
        st.markdown("#### B. Streamlit 세션 상태 관리")
        node(
            "Streamlit 페이지 및 게임 흐름",
            "시작 여부 · 일시정지 여부 · 현재 스테이지 · 페이지 이동",
        )
        arrow("Python 코드에서 상태값 갱신")
        node(
            "st.session_state",
            "현재 Streamlit 세션에서 사용할 상태값 관리",
            'st.session_state.game_paused\n'
            'st.session_state.stage01_started\n'
            'st.session_state.game_started',
        )
        st.warning(
            "st.session_state는 SQLite 같은 데이터베이스가 아닙니다. "
            "게임의 상세 진행 데이터를 저장한 localStorage와 역할이 달랐습니다."
        )

    st.divider()
    st.subheader("② 이번에 새로 구현한 SQLite 저장 방식")
    st.write("이번 실험에서는 웹앱의 입력값을 Python이 받아 SQL 명령으로 SQLite 파일에 기록합니다.")

    sqlite_left, sqlite_right = st.columns([1, 1], gap="large")

    with sqlite_left:
        node("Streamlit 입력 화면", "사용자가 제목과 내용을 입력")
        arrow("입력값을 Python 함수에 전달")
        node(
            "Python + sqlite3",
            "데이터베이스 파일에 연결하고 SQL 명령 실행",
            "conn.execute(\n"
            '  "INSERT INTO records (title, content) VALUES (?, ?)",\n'
            "  (title, content)\n"
            ")",
        )
        arrow("SQL INSERT 실행")
        node(
            "records.db",
            "앱 폴더에 생성되는 SQLite 데이터베이스 파일",
            "하나의 파일 안에 테이블과 실제 데이터가 저장됨",
        )

    with sqlite_right:
        st.markdown("#### records.db 안의 구조")
        node("데이터베이스 파일", "records.db")
        arrow("파일 안에 테이블이 존재")
        node("테이블", "records")
        arrow("테이블은 열과 행으로 구성")
        field_cols = st.columns(2)
        with field_cols[0]:
            info_card("id · INTEGER", "각 행을 구별하는 기본 키")
            info_card("title · TEXT", "기록 제목")
        with field_cols[1]:
            info_card("content · TEXT", "기록 내용")
            info_card("created_at · TEXT", "저장 시각")
        st.caption("열(Column)은 데이터의 항목을 정의하고, 행(Row)은 실제 기록 한 건을 나타냅니다.")

    st.divider()
    st.subheader("③ 두 방식에서 데이터가 관리되는 모습")
    comparison_cols = st.columns(2, gap="large")
    with comparison_cols[0]:
        with st.container(border=True):
            st.markdown("**기존 PROJECT : LOGIC**")
            st.code(
                '{\n'
                '  "playerX": 50,\n'
                '  "playerY": 43,\n'
                '  "seconds": 480,\n'
                '  "codeSolved": false,\n'
                '  "inventory": [...]\n'
                '}',
                language="json",
            )
            st.caption(
                "하나의 JSON 객체에 게임 진행에 필요한 여러 값을 묶어 저장"
            )
    with comparison_cols[1]:
        with st.container(border=True):
            st.markdown("**SQLite 실험 프로그램**")
            st.code(
                "records\n"
                "┌────┬─────────┬───────────────┐\n"
                "│ id │ title   │ content       │\n"
                "├────┼─────────┼───────────────┤\n"
                "│ 1  │ 기록 A  │ 저장 실험      │\n"
                "│ 2  │ 기록 B  │ 구조 탐구      │\n"
                "└────┴─────────┴───────────────┘",
                language="text",
            )
            st.caption(
                "정해진 열에 맞춰 각 기록을 행 단위로 저장하고 SQL로 관리"
            )

    st.subheader("핵심 차이")
    difference_cols = st.columns(3)
    with difference_cols[0]:
        info_card(
            "저장 위치",
            "localStorage: 브라우저 저장 공간\n\nSQLite: records.db 파일",
        )
    with difference_cols[1]:
        info_card(
            "데이터 구성",
            "localStorage: 키에 연결된 JSON 문자열\n\nSQLite: 테이블·행·열",
        )
    with difference_cols[2]:
        info_card(
            "관리 방법",
            "localStorage: JavaScript API\n\nSQLite: SQL 명령어와 sqlite3",
        )

    st.caption(
        "참고: 두 방식은 서로 대체 관계라고 단정할 수 없습니다. "
        "데이터의 형태와 사용 목적에 따라 적합한 저장 방식을 선택합니다."
    )

with crud_tab:
    st.subheader("SQLite 데이터 직접 저장·관리")
    st.write(
        "아래에서 입력한 내용은 브라우저 화면 상태가 아니라 "
        "`records.db` 파일의 `records` 테이블에 저장됩니다."
    )

    save_col, list_col = st.columns([1, 1], gap="large")

    with save_col:
        with st.container(border=True):
            st.markdown("#### 새 데이터 저장")
            with st.form("add_record_form", clear_on_submit=True):
                title = st.text_input("제목", placeholder="예: 첫 번째 기록")
                content = st.text_area("내용", placeholder="데이터베이스에 저장할 내용")
                submitted = st.form_submit_button("INSERT · 저장", type="primary")

            if submitted:
                if not title.strip() or not content.strip():
                    st.warning("제목과 내용을 모두 입력해 주세요.")
                else:
                    add_record(title.strip(), content.strip())
                    st.success("records.db에 저장했습니다.")
                    st.rerun()

    with list_col:
        with st.container(border=True):
            st.markdown("#### 데이터 조회")
            records = get_records()
            st.metric("저장된 행 수", len(records))
            if records:
                for record in records:
                    st.markdown(
                        f"**#{record['id']} · {record['title']}**"
                    )
                    st.caption(
                        f"{record['content']} · {record['created_at']}"
                    )
                    st.divider()
            else:
                st.info("저장된 데이터가 없습니다.")

    records = get_records()
    if records:
        st.divider()
        st.subheader("기존 데이터 수정 및 삭제")
        record_map = {record["id"]: record for record in records}
        selected_id = st.selectbox(
            "관리할 데이터 선택",
            options=list(record_map.keys()),
            format_func=lambda rid: f"#{rid} · {record_map[rid]['title']}",
        )
        selected = record_map[selected_id]

        edit_col, delete_col = st.columns(2, gap="large")
        with edit_col:
            with st.container(border=True):
                st.markdown("#### UPDATE · 수정")
                with st.form(f"edit_form_{selected_id}"):
                    edited_title = st.text_input(
                        "수정할 제목", value=selected["title"]
                    )
                    edited_content = st.text_area(
                        "수정할 내용", value=selected["content"]
                    )
                    update_clicked = st.form_submit_button("수정 내용 저장")

                if update_clicked:
                    if not edited_title.strip() or not edited_content.strip():
                        st.warning("제목과 내용을 모두 입력해 주세요.")
                    else:
                        update_record(
                            selected_id,
                            edited_title.strip(),
                            edited_content.strip(),
                        )
                        st.success("데이터를 수정했습니다.")
                        st.rerun()

        with delete_col:
            with st.container(border=True):
                st.markdown("#### DELETE · 삭제")
                st.write(f"선택한 기록: **{selected['title']}**")
                confirm_delete = st.checkbox(
                    "이 기록을 삭제하겠습니다.",
                    key=f"confirm_delete_{selected_id}",
                )
                if st.button(
                    "선택한 데이터 삭제",
                    disabled=not confirm_delete,
                    key=f"delete_button_{selected_id}",
                ):
                    delete_record(selected_id)
                    st.success("데이터를 삭제했습니다.")
                    st.rerun()

with structure_tab:
    st.subheader("SQLite 데이터베이스 내부 구조")
    st.write(
        "SQLite가 관리하는 테이블 정의와 실제 저장된 행을 각각 시각적으로 확인합니다."
    )

    st.markdown("#### 1. 데이터베이스 파일")
    file_col, table_col = st.columns([1, 2], gap="large")
    with file_col:
        info_card(
            "records.db",
            f"파일 크기: {DB_PATH.stat().st_size:,} bytes\n\n"
            "앱과 같은 폴더에 저장되는 SQLite 파일",
        )
    with table_col:
        info_card(
            "records 테이블",
            "데이터베이스 파일 안에 생성된 테이블. "
            "각 열의 정의에 따라 여러 기록(Row)을 저장합니다.",
        )

    st.markdown("#### 2. 테이블을 구성하는 열(Column)")
    columns = get_table_columns()
    field_grid = st.columns(2)
    for index, column in enumerate(columns):
        with field_grid[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{column['name']}**")
                st.caption(f"자료형: {column['type']}")
                if column["pk"]:
                    st.success("PRIMARY KEY")
                if column["notnull"]:
                    st.caption("NOT NULL · 빈 값 허용 안 함")
                if column["dflt_value"] is not None:
                    st.caption(f"기본값: {column['dflt_value']}")

    st.markdown("#### 3. 테이블 생성 SQL")
    st.code(get_table_sql(), language="sql")

    st.markdown("#### 4. 실제 저장된 행(Row)")
    records = get_records()
    st.metric("현재 저장된 행", len(records))
    if records:
        for record in records:
            with st.container(border=True):
                st.markdown(f"**ROW · {record['id']}**")
                st.markdown(f"**title:** {record['title']}")
                st.write(f"**content:** {record['content']}")
                st.caption(f"created_at: {record['created_at']}")
    else:
        st.info("저장된 행이 없습니다. 'SQLite 직접 실험' 탭에서 데이터를 추가해 보세요.")

    st.markdown("#### 5. 구조를 직접 조회하는 명령")
    st.code("PRAGMA table_info(records);", language="sql")
    st.caption(
        "PRAGMA table_info는 테이블의 열 이름, 자료형, 기본값, "
        "NOT NULL 및 기본 키 여부 등을 확인하는 SQLite 명령입니다."
    )

st.divider()
st.caption(
    "이 프로그램은 로컬 환경에서 SQLite의 파일 기반 저장 구조를 확인하기 위한 실험용 웹앱입니다. "
    "records.db 파일을 삭제하면 그 안의 기록도 함께 삭제됩니다."
)
