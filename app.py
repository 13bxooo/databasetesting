from contextlib import contextmanager
from pathlib import Path
import sqlite3

import streamlit as st

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
    return result["sql"] if result else "테이블 정의를 찾을 수 없음"


def get_table_columns():
    with connect_db() as conn:
        return conn.execute("PRAGMA table_info(records)").fetchall()


def inject_css():
    st.markdown(
        """
        <style>
        .block-container {max-width: 1100px; padding-top: 2rem; padding-bottom: 4rem;}
        .small-note {color:#6b7280; font-size:0.93rem; line-height:1.6;}
        .section-title {font-size:1.55rem; font-weight:800; margin:0.2rem 0 0.8rem 0;}
        .section-desc {color:#4b5563; line-height:1.75; margin-bottom:1rem;}
        .diagram-wrap {
            background:#faf7f7;
            border:1px solid #e8dfdf;
            border-radius:24px;
            padding:1.1rem 1.1rem 1.2rem 1.1rem;
            margin-bottom:1rem;
        }
        .diagram-head {
            font-size:1.2rem;
            font-weight:800;
            margin-bottom:0.25rem;
            color:#2d2325;
        }
        .diagram-sub {
            color:#6b7280;
            font-size:0.92rem;
            line-height:1.6;
            margin-bottom:1rem;
        }
        .flow-row {
            display:block;
            margin-bottom:0;
        }
        .flow-card {
            background:#ffffff;
            border:1px solid #eadfdf;
            border-left:6px solid var(--flow-accent, #b19898);
            border-radius:14px;
            padding:0.95rem 1rem;
        }
        .flow-title {
            font-size:1.02rem;
            font-weight:800;
            margin-bottom:0.3rem;
            color:#251b1d;
        }
        .flow-desc {
            font-size:0.92rem;
            line-height:1.62;
            color:#59545a;
        }
        .flow-arrow {
            text-align:center;
            color:#a58f93;
            font-size:1.55rem;
            line-height:1.2;
            padding:0.35rem 0;
        }
        .state-note {
            margin-top:0.9rem;
            background:#fff8df;
            border:1px solid #f0df9f;
            border-radius:16px;
            padding:0.95rem 1rem;
            color:#775b0a;
            line-height:1.65;
            font-size:0.93rem;
        }
        .compare-grid {
            display:grid;
            grid-template-columns: repeat(3, 1fr);
            gap:14px;
            margin-top:0.6rem;
            margin-bottom:0.8rem;
        }
        .compare-card {
            background:#fbfbfb;
            border:1px solid #ece6e6;
            border-radius:18px;
            padding:1rem 1rem 0.95rem 1rem;
        }
        .compare-card b {display:block; margin-bottom:0.55rem; font-size:1rem; color:#2b2426;}
        .compare-card div {color:#5a5560; line-height:1.62; font-size:0.93rem;}
        .schema-card {
            background:#fcfbfb;
            border:1px solid #ece6e6;
            border-radius:16px;
            padding:0.95rem 1rem;
            margin-bottom:0.7rem;
        }
        .schema-title {font-weight:800; color:#2a2325; margin-bottom:0.3rem;}
        .schema-meta {color:#625d66; line-height:1.6; font-size:0.93rem;}
        @media (max-width: 900px) {
            .compare-grid {grid-template-columns: 1fr;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section(title, desc):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-desc">{desc}</div>', unsafe_allow_html=True)


def render_flow_diagram(title, subtitle, items, accent, note=None):
    html = [
        '<div class="diagram-wrap">',
        f'<div class="diagram-head">{title}</div>',
        f'<div class="diagram-sub">{subtitle}</div>',
    ]
    for index, (name, desc) in enumerate(items):
        html.append(
            f"""<div class="flow-row">
                    <div class="flow-card" style="border-left-color:{accent};">
                        <div class="flow-title">{name}</div>
                        <div class="flow-desc">{desc}</div>
                    </div>
                </div>"""
        )
        if index < len(items) - 1:
            html.append('<div class="flow-arrow">↓</div>')
    if note:
        html.append(f'<div class="state-note">{note}</div>')
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def render_compare_cards(cards):
    html = ['<div class="compare-grid">']
    for title, body in cards:
        html.append(
            f'<div class="compare-card"><b>{title}</b><div>{body}</div></div>'
        )
    html.append('</div>')
    st.markdown("".join(html), unsafe_allow_html=True)


initialize_db()

st.set_page_config(
    page_title="웹 애플리케이션 데이터 저장 방식 탐구",
    page_icon="🗃️",
    layout="wide",
)
inject_css()

st.title("웹 애플리케이션의 데이터 저장 방식 탐구")
st.caption("PROJECT : LOGIC의 기존 저장 방식과 SQLite 구조 비교")
st.markdown(
    "웹 애플리케이션에서 데이터를 저장하는 두 방식을 비교하고, SQLite의 구조를 직접 확인하는 탐구"
)

viz_tab, crud_tab, structure_tab = st.tabs([
    "저장 방식 시각화",
    "SQLite 직접 실험",
    "SQLite 내부 구조",
])

with viz_tab:
    render_section(
        "01. 탐구의 출발점",
        "PROJECT : LOGIC을 개발하며 게임 진행 정보를 저장하고 복원하는 기능을 구현했다. "
        "이 과정에서 브라우저에 저장하는 방식과 데이터베이스 파일에 저장하는 방식이 "
        "구조적으로 어떻게 다른지 비교해 보고자 했다.",
    )

    with st.container(border=True):
        st.markdown("**핵심 질문**")
        st.markdown(
            "웹 애플리케이션의 데이터는 어떤 구조로 저장되며, "
            "브라우저 기반 저장 방식과 관계형 데이터베이스는 어떻게 다르게 데이터를 관리하는가?"
        )

    col1, col2 = st.columns(2, gap="large")

    with col1:
        render_flow_diagram(
            "기존 PROJECT : LOGIC의 저장 방식",
            "게임 진행 데이터는 JavaScript의 localStorage에 저장하고, Streamlit 페이지 흐름은 별도로 관리하는 구조",
            [
                ("게임 화면", "플레이어 이동, 타이머, 퍼즐 진행, 인벤토리 변화 발생"),
                ("JavaScript 상태 객체", "playerX, playerY, seconds, inventory 등 여러 값을 하나의 객체로 정리"),
                ("JSON 문자열", "JSON.stringify()로 객체를 문자열로 직렬화"),
                ("브라우저 localStorage", "키와 값 형태로 저장. 같은 브라우저에서 다시 읽어 복원"),
            ],
            accent="#b19898",
            note=(
                "보조 상태 관리: <b>st.session_state</b>는 데이터베이스가 아니라 Streamlit 세션 상태 관리 기능이다. "
                "게임 시작 여부, 현재 스테이지, 페이지 이동 같은 흐름 제어에 사용했다."
            ),
        )

        st.markdown("#### 코드 예시")
        st.code(
            'localStorage.setItem(\n'
            '  "project_logic_stage01_save_v1",\n'
            '  JSON.stringify(gameState)\n'
            ')',
            language="javascript",
        )

    with col2:
        render_flow_diagram(
            "SQLite를 이용한 저장 방식",
            "사용자 입력값이 Python과 sqlite3를 거쳐 records.db 파일 내부의 records 테이블에 저장되는 구조",
            [
                ("Streamlit 입력 화면", "사용자가 제목과 내용을 입력"),
                ("Python 처리 함수", "app.py에서 입력값 검증 후 데이터베이스 연결"),
                ("SQL 명령 실행", "INSERT, SELECT, UPDATE, DELETE 명령 수행"),
                ("records 테이블", "열(Column)과 행(Row)의 구조로 실제 데이터 저장"),
                ("records.db 파일", "SQLite 데이터베이스 파일. 앱 재실행 후에도 데이터 유지"),
            ],
            accent="#8a7a80",
        )

        st.markdown("#### 코드 예시")
        st.code(
            'conn.execute(\n'
            '  "INSERT INTO records (title, content) VALUES (?, ?)",\n'
            '  (title, content)\n'
            ')',
            language="python",
        )

    render_section(
        "02. 두 저장 방식의 핵심 차이",
        "두 방식 모두 데이터를 저장할 수 있지만, 저장 위치와 데이터 구성, 관리 방법이 다르다.",
    )

    render_compare_cards([
        (
            "저장 위치",
            "기존 방식: 브라우저의 localStorage<br>SQLite 방식: records.db 데이터베이스 파일",
        ),
        (
            "데이터 구성",
            "기존 방식: 하나의 JSON 객체를 문자열로 저장<br>SQLite 방식: 테이블·행·열 구조로 저장",
        ),
        (
            "관리 방법",
            "기존 방식: JavaScript API로 저장·조회<br>SQLite 방식: SQL과 sqlite3로 생성·조회·수정·삭제",
        ),
    ])

    st.caption(
        "두 방식은 우열 관계라기보다 목적과 데이터 구조에 따라 선택하는 서로 다른 저장 방식이다."
    )

with crud_tab:
    render_section(
        "03. SQLite 직접 실험",
        "아래에서 입력한 데이터는 화면 상태가 아니라 records.db 파일의 records 테이블에 저장한다.",
    )

    form_col, list_col = st.columns([1, 1], gap="large")

    with form_col:
        st.markdown("#### 데이터 입력")
        with st.form("add_record_form", clear_on_submit=True):
            title = st.text_input("제목", placeholder="예: 첫 번째 기록")
            content = st.text_area("내용", placeholder="데이터베이스에 저장할 내용")
            submitted = st.form_submit_button("데이터 저장")

        if submitted:
            if not title.strip() or not content.strip():
                st.warning("제목과 내용을 모두 입력해야 한다.")
            else:
                add_record(title.strip(), content.strip())
                st.success("records.db에 데이터 저장 완료")
                st.rerun()

    with list_col:
        st.markdown("#### 저장된 데이터 조회")
        records = get_records()
        st.metric("현재 저장된 행 수", len(records))
        if records:
            for record in records:
                with st.container(border=True):
                    st.markdown(f"**ROW {record['id']} · {record['title']}**")
                    st.write(record["content"])
                    st.caption(f"저장 시각: {record['created_at']}")
        else:
            st.info("저장된 데이터가 없음")

    records = get_records()
    if records:
        st.divider()
        st.markdown("#### 기존 데이터 수정 및 삭제")
        record_map = {record["id"]: record for record in records}
        selected_id = st.selectbox(
            "관리할 데이터 선택",
            options=list(record_map.keys()),
            format_func=lambda rid: f"ROW {rid} · {record_map[rid]['title']}",
        )
        selected = record_map[selected_id]

        edit_col, delete_col = st.columns(2, gap="large")

        with edit_col:
            with st.container(border=True):
                st.markdown("**UPDATE · 데이터 수정**")
                with st.form(f"edit_form_{selected_id}"):
                    edited_title = st.text_input("수정할 제목", value=selected["title"])
                    edited_content = st.text_area("수정할 내용", value=selected["content"])
                    update_clicked = st.form_submit_button("수정 내용 저장")

                if update_clicked:
                    if not edited_title.strip() or not edited_content.strip():
                        st.warning("제목과 내용을 모두 입력해야 한다.")
                    else:
                        update_record(selected_id, edited_title.strip(), edited_content.strip())
                        st.success("데이터 수정 완료")
                        st.rerun()

        with delete_col:
            with st.container(border=True):
                st.markdown("**DELETE · 데이터 삭제**")
                st.write(f"선택한 데이터: **{selected['title']}**")
                confirm_delete = st.checkbox(
                    "선택한 기록을 삭제함",
                    key=f"confirm_delete_{selected_id}",
                )
                if st.button(
                    "선택한 데이터 삭제",
                    disabled=not confirm_delete,
                    key=f"delete_button_{selected_id}",
                ):
                    delete_record(selected_id)
                    st.success("데이터 삭제 완료")
                    st.rerun()

with structure_tab:
    render_section(
        "04. SQLite 내부 구조 확인",
        "데이터베이스 파일, 테이블 정의, 열(Column), 실제 행(Row)을 구분해 확인한다.",
    )

    top1, top2 = st.columns([1, 1], gap="large")
    with top1:
        with st.container(border=True):
            st.markdown("**records.db 파일**")
            st.write(f"파일 위치: `{DB_PATH}`")
            st.write(f"파일 크기: {DB_PATH.stat().st_size:,} bytes")
            st.caption("앱과 같은 폴더에 생성되는 SQLite 데이터베이스 파일")
    with top2:
        with st.container(border=True):
            st.markdown("**records 테이블**")
            st.write("records.db 파일 내부에 생성되는 테이블")
            st.caption("여러 행을 저장하며, 각 행은 동일한 열 구조를 공유한다.")

    st.markdown("#### 테이블을 구성하는 열(Column)")
    columns = get_table_columns()
    col_a, col_b = st.columns(2, gap="large")
    target_cols = [col_a, col_b]
    for idx, column in enumerate(columns):
        with target_cols[idx % 2]:
            st.markdown(
                f'''<div class="schema-card">
                        <div class="schema-title">{column['name']} · {column['type']}</div>
                        <div class="schema-meta">'''
                + (
                    "PRIMARY KEY · 각 행을 구분하는 기본 키<br>" if column["pk"] else ""
                )
                + (
                    "NOT NULL · 빈 값 입력 제한<br>" if column["notnull"] else ""
                )
                + (
                    f"DEFAULT · {column['dflt_value']}" if column["dflt_value"] is not None else ""
                )
                + "</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("#### 테이블 생성 SQL")
    st.code(get_table_sql(), language="sql")

    st.markdown("#### 실제 저장된 행(Row)")
    current_records = get_records()
    if current_records:
        for record in current_records:
            with st.container(border=True):
                st.markdown(f"**ROW {record['id']}**")
                st.markdown(f"- title: {record['title']}")
                st.markdown(f"- content: {record['content']}")
                st.markdown(f"- created_at: {record['created_at']}")
    else:
        st.info("현재 저장된 행이 없음")

    st.markdown("#### 구조 조회 명령")
    st.code("PRAGMA table_info(records);", language="sql")
    st.caption(
        "열 이름, 자료형, 기본값, NOT NULL, 기본 키 여부를 확인하는 SQLite 명령"
    )
