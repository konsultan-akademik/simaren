import json
import os
import secrets
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Agroforestri Aren - Enterprise PM",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "agroforestri_aren_data.json"
DB_FILE = "agroforestri_aren.db"
FEATURE_TABLES = {
    "team": "sdm_records",
    "categories": "category_records",
    "tasks": "task_records",
    "chat": "chat_records",
    "announcements": "announcement_records",
    "documents": "document_records",
    "budgets": "cashflow_records",
    "logs": "activity_log_records",
}

DEFAULT_DATA = {
    "team": [
        {"id": "1", "name": "Dr. Uci Sulandari, M.Si", "role": "Project Manager / Ahli Lingkungan", "username": "uci.sulandari", "password": "password123"},
        {"id": "2", "name": "Intan Handayani, S.Hut", "role": "Pemegang Dana Operasional/Maker", "username": "intan.handayani", "password": "password123"},
        {"id": "3", "name": "Sugiyono, STP, M.Si", "role": "Fasilitator Safeguards", "username": "sugiyono", "password": "password123"},
        {"id": "4", "name": "Diah Puspita Hati, SP, MP.", "role": "Staf Administrasi", "username": "diah.puspita", "password": "password123"}
    ],
    "categories": [
        {"code": "KAT-01", "name": "Perencanaan & Lahan"},
        {"code": "KAT-02", "name": "Pengadaan & Pembibitan"},
        {"code": "KAT-03", "name": "Infrastruktur & Irigasi"},
        {"code": "KAT-04", "name": "Pelatihan & SDM"},
        {"code": "KAT-05", "name": "Panen & Pascapanen"}
    ],
    "tasks": [
        {
            "id": "task-1",
            "categoryCode": "KAT-01",
            "categoryName": "Perencanaan & Lahan",
            "title": "Survei Kelayakan Lahan & Uji Tanah Blok A",
            "assignee": "Dr. Uci Sulandari, M.Si",
            "deadline": "2026-10-10",
            "priority": "Tinggi",
            "status": "Selesai",
            "dependency": ""
        },
        {
            "id": "task-2",
            "categoryCode": "KAT-02",
            "categoryName": "Pengadaan & Pembibitan",
            "title": "Pengadaan Bibit Aren Varietas Unggul (1,000 Pohon)",
            "assignee": "Intan Handayani, S.Hut",
            "deadline": "2026-10-14",
            "priority": "Tinggi",
            "status": "Dalam Proses",
            "dependency": "task-1"
        },
        {
            "id": "task-3",
            "categoryCode": "KAT-03",
            "categoryName": "Infrastruktur & Irigasi",
            "title": "Pemasangan Pagar Keliling & Sistem Irigasi Tetes",
            "assignee": "Sugiyono, STP, M.Si",
            "deadline": "2026-10-12",
            "priority": "Sedang",
            "status": "Belum Dimulai",
            "dependency": "task-1"
        },
        {
            "id": "task-4",
            "categoryCode": "KAT-04",
            "categoryName": "Pelatihan & SDM",
            "title": "Pelatihan Teknik Penanaman Agroforestri Bagi Petani Lokal",
            "assignee": "Diah Puspita Hati, SP, MP.",
            "deadline": "2026-12-01",
            "priority": "Sedang",
            "status": "Belum Dimulai",
            "dependency": "task-2"
        }
    ],
    "chat": [
        {"id": "c1", "sender": "Dr. Uci Sulandari, M.Si", "message": "Selamat pagi tim. Mohon pembaruan progres uji tanah Blok A.", "time": "08:30"},
        {"id": "c2", "sender": "Sugiyono, STP, M.Si", "message": "Hasil tes pH tanah sudah keluar pak, rata-rata 6.2, sangat cocok untuk aren.", "time": "08:45"}
    ],
    "announcements": [
        {"id": "ann-1", "title": "Pemeriksaan Pembibitan Aren", "message": "Seluruh tim lapangan diharapkan hadir pada survei lokasi blok C besok pukul 08.00 WIB."},
        {"id": "ann-2", "title": "Laporan Pertumbuhan Bulanan", "message": "Unggah berkas log tanaman sebelum akhir minggu ini untuk penyesuaian anggaran pupuk."}
    ],
    "documents": [
        {
            "id": "doc-1",
            "title": "SOP Penanaman & Pemeliharaan Aren Agroforestri",
            "category": "SOP & Panduan",
            "summary": "Panduan standar operasional untuk pola tanam ganda aren dengan tanaman sela.",
            "url": "http://localhost:8501/SOP_Panduan",
            "date": "2026-10-10"
        },
        {
            "id": "doc-2",
            "title": "Template Laporan Mingguan Lapangan",
            "category": "Template Laporan",
            "summary": "Format baku untuk pencatatan progres fisik dan inventaris bibit.",
            "url": "http://localhost:8501/template-laporan",
            "date": "2026-10-12"
        }
    ],
    "budgets": [
        {"id": "b1", "type": "PEMASUKAN", "title": "Pencairan Dana Hibah Modal Awal Proyek", "category": "Modal / Investor", "amount": 250000000, "date": "2026-10-01"},
        {"id": "b2", "type": "PENGELUARAN", "title": "Uji Laboratorium Sampel Tanah", "category": "Operasional Lapangan", "amount": 8500000, "date": "2026-10-14"},
        {"id": "b3", "type": "PENGELUARAN", "title": "DP Pembelian Bibit Aren Unggul", "category": "Peralatan & Bibit", "amount": 45000000, "date": "2026-10-15"},
        {"id": "b4", "type": "PEMASUKAN", "title": "Penjualan Hasil Panen Sela Polyculture", "category": "Hasil Penjualan / Produk", "amount": 12500000, "date": "2026-10-16"}
    ],
    "logs": [
        {"id": "l1", "text": "Tugas 'Survei Kelayakan Lahan' ditandai Selesai", "time": "14/10/2026 10:30"},
        {"id": "l2", "text": "Transaksi Pemasukan dicatat: Penjualan Hasil Panen Sela", "time": "16/10/2026 09:15"}
    ]
}

def _connect_db():
    connection = sqlite3.connect(DB_FILE)
    for table_name in FEATURE_TABLES.values():
        connection.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
            position INTEGER NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (position)
            )
        """)
    # Retain the generic table for backward compatibility and future collections.
    connection.execute("""
        CREATE TABLE IF NOT EXISTS app_records (
            collection TEXT NOT NULL,
            position INTEGER NOT NULL,
            payload TEXT NOT NULL,
            PRIMARY KEY (collection, position)
        )
    """)
    return connection


def _write_db_data(connection, data):
    feature_collections = set(FEATURE_TABLES)
    for collection, table_name in FEATURE_TABLES.items():
        records = data.get(collection, [])
        if not isinstance(records, list):
            records = [records]
        connection.execute(f"DELETE FROM {table_name}")
        connection.executemany(
            f"INSERT INTO {table_name}(position, payload) VALUES (?, ?)",
            [
                (position, json.dumps(record, ensure_ascii=False))
                for position, record in enumerate(records)
            ]
        )

    # Unknown collections remain available through the legacy-compatible table.
    connection.execute("DELETE FROM app_records")
    for collection, records in data.items():
        if collection in feature_collections:
            continue
        if not isinstance(records, list):
            records = [records]
        connection.executemany(
            "INSERT INTO app_records(collection, position, payload) VALUES (?, ?, ?)",
            [
                (str(collection), position, json.dumps(record, ensure_ascii=False))
                for position, record in enumerate(records)
            ]
        )


def _read_db_data(connection):
    data = {}
    for collection, table_name in FEATURE_TABLES.items():
        rows = connection.execute(
            f"SELECT payload FROM {table_name} ORDER BY position"
        ).fetchall()
        if rows:
            data[collection] = [json.loads(payload) for (payload,) in rows]

    # Import collections from the former shared table when no feature table has
    # been populated yet. The next normal save writes them into their own tables.
    rows = connection.execute(
        "SELECT collection, payload FROM app_records ORDER BY collection, position"
    ).fetchall()
    for collection, payload in rows:
        if collection not in data:
            data.setdefault(collection, []).append(json.loads(payload))
    return data


def load_data():
    if "app_data" not in st.session_state:
        try:
            with _connect_db() as connection:
                data = _read_db_data(connection)
                if not data:
                    # Import existing JSON data once when initializing the database.
                    if os.path.exists(DATA_FILE):
                        try:
                            with open(DATA_FILE, "r", encoding="utf-8") as f:
                                data = json.load(f)
                        except (OSError, json.JSONDecodeError):
                            data = {}
                    if not data:
                        data = json.loads(json.dumps(DEFAULT_DATA))
                    _write_db_data(connection, data)
                st.session_state["app_data"] = data
        except (sqlite3.Error, json.JSONDecodeError) as e:
            st.error(f"Gagal membaca database: {e}")
            st.session_state["app_data"] = json.loads(json.dumps(DEFAULT_DATA))

    # Migration helper for team data credentials
    data = st.session_state["app_data"]
    for member in data.get("team", []):
        if "username" not in member:
            member["username"] = member.get("name", "").lower().replace(" ", ".").replace(",", "")
        if "password" not in member:
            member["password"] = "password123"
            
    return st.session_state["app_data"]

def save_data():
    if "app_data" in st.session_state:
        try:
            with _connect_db() as connection:
                _write_db_data(connection, st.session_state["app_data"])
        except (sqlite3.Error, TypeError, ValueError) as e:
            st.error(f"Gagal menyimpan data ke database: {e}")

def add_log(text):
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    data = load_data()
    data["logs"].insert(0, {"id": f"l-{int(datetime.now().timestamp())}", "text": text, "time": now_str})
    if len(data["logs"]) > 20:
        data["logs"].pop()
    save_data()

def format_rupiah(amount):
    try:
        val = int(amount)
        return f"Rp {val:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"

def is_task_overdue(task):
    deadline = task.get("deadline")
    if task.get("status") == "Selesai" or not isinstance(deadline, str) or not deadline.strip():
        return False
    try:
        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
        return deadline_date < datetime.now().date()
    except (TypeError, ValueError):
        return False

def get_sdm_permissions(role):
    role_text = str(role or "").lower()
    if "pemegang dana" in role_text:
        return {"read": True, "create": True, "update": True, "delete": True, "role_label": "Pemegang Dana Operasional (Full Control Financial & Task)"}
    if "project manager" in role_text or "koordinator" in role_text:
        return {"read": True, "create": True, "update": True, "delete": True, "role_label": "Project Manager (Full Oversight & Strategic)"}
    if "staf administrasi" in role_text:
        return {"read": True, "create": True, "update": True, "delete": False, "role_label": "Staf Administrasi (Input Data & Logging)"}
    if "fasilitator safeguard" in role_text or "safeguards" in role_text:
        return {"read": True, "create": False, "update": True, "delete": False, "role_label": "Fasilitator Safeguards (Review & Monitor)"}
    return {"read": True, "create": False, "update": False, "delete": False, "role_label": "Tamu / Pengamat"}

st.markdown("""
<style>
    /* Professional dark emerald agroforestry theme */
    .stApp {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(31, 115, 84, 0.20), transparent 36%),
            radial-gradient(ellipse at 90% 18%, rgba(15, 118, 110, 0.13), transparent 30%),
            #07130f;
        color: #dcebe2;
    }
    .main .block-container {
        padding-top: 1.75rem;
        padding-bottom: 2.5rem;
        max-width: 1500px;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b2119 0%, #102d21 55%, #0a1b15 100%);
        border-right: 1px solid rgba(97, 218, 158, 0.25);
        box-shadow: 8px 0 30px rgba(0, 0, 0, 0.18);
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #e4f6eb;
    }
    h1, h2, h3, h4, h5 {
        color: #b9f6d0;
        letter-spacing: -0.02em;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(18, 43, 32, 0.96), rgba(10, 27, 21, 0.96));
        border: 1px solid rgba(101, 220, 157, 0.24);
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(190, 255, 215, 0.04);
    }
    div[data-testid="stMetric"] label {
        color: #91b9a1;
    }
    .stButton > button,
    .stDownloadButton > button {
        background-color: #176b4b;
        color: #ffffff;
        border: 1px solid #42c987;
        border-radius: 8px;
        font-weight: 600;
        transition: background-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background-color: #21845b;
        color: #ffffff;
        border-color: #70e5a8;
        box-shadow: 0 0 16px rgba(66, 201, 135, 0.25);
        transform: translateY(-1px);
    }
    [data-baseweb="select"] > div,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input {
        background-color: #10251c;
        border-color: #315d46;
        border-radius: 8px;
        color: #e2f3e8;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(101, 220, 157, 0.22);
        border-radius: 10px;
        overflow: hidden;
    }
    [data-testid="stExpander"] {
        border: 1px solid rgba(101, 220, 157, 0.22);
        border-radius: 10px;
        background-color: rgba(13, 34, 25, 0.72);
    }
    .metric-card {
        background: linear-gradient(145deg, rgba(18, 43, 32, 0.97), rgba(9, 25, 19, 0.97));
        border: 1px solid rgba(101, 220, 157, 0.25);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(190, 255, 215, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(112, 229, 168, 0.55);
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3), 0 0 20px rgba(66, 201, 135, 0.10);
    }
    .metric-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: #8eaf9b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #c5f7d6;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #68dda0;
        font-weight: 600;
        margin-top: 2px;
    }
    .login-container {
        max-width: 480px;
        margin: 40px auto;
        padding: 30px;
        background: linear-gradient(145deg, rgba(16, 45, 33, 0.95), rgba(8, 24, 18, 0.95));
        border: 1px solid rgba(101, 220, 157, 0.35);
        border-radius: 16px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.5);
    }
    .role-badge {
        display: inline-block;
        padding: 4px 10px;
        background: rgba(66, 201, 135, 0.15);
        border: 1px solid rgba(66, 201, 135, 0.4);
        color: #8eeeb6;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 5px;
    }
    .overdue-alert {
        background-color: rgba(198, 91, 59, 0.15);
        border-left: 4px solid #e06c4c;
        padding: 12px 16px;
        border-radius: 8px;
        color: #f7a892;
        margin-bottom: 20px;
    }
    .chat-bubble-self {
        background-color: #39764d;
        color: #ffffff;
        padding: 8px 12px;
        border-radius: 12px 12px 0px 12px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    .chat-bubble-other {
        background-color: #10251c;
        border: 1px solid rgba(101, 220, 157, 0.22);
        color: #d9ebe0;
        padding: 8px 12px;
        border-radius: 12px 12px 12px 0px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .metric-value {
            font-size: 1.25rem;
        }
    }
    [data-testid="stCaptionContainer"], .stMarkdown p {
        color: #a9c2b2;
    }
    hr {
        border-color: rgba(101, 220, 157, 0.18);
    }
</style>
""", unsafe_allow_html=True)

app_data = load_data()

# Handle session state for user authentication
authenticated_member = None
member_id = st.session_state.get("rbac_member_id")
if member_id:
    authenticated_member = next(
        (member for member in app_data.get("team", []) if str(member.get("id")) == str(member_id)),
        None
    )
    if authenticated_member is None:
        st.session_state.pop("rbac_member_id", None)

default_permissions = {
    "read": True,
    "create": False,
    "update": False,
    "delete": False,
    "role_label": "Tamu / Pengamat"
}
user_permissions = get_sdm_permissions(authenticated_member.get("role")) if authenticated_member else default_permissions
authenticated_member = authenticated_member or {}

if not authenticated_member:
    st.markdown("<br/>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2.2, 1])
    
    with col_l2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="font-size: 2.2rem; margin-bottom: 5px;">🌲 Agroforestri Aren</h1>
                <p style="color: #8ebfa3; font-size: 0.95rem;">Portal Manajemen Proyek & Peran SDM FOLU-NC4</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("main_login_form"):
            st.markdown("### 🔑 Login Pengguna")
            st.caption("Pilih Peran SDM atau Akun Terdaftar untuk Masuk")
            
            # Select SDM / Team Member
            team_members = app_data.get("team", [])
            team_options = {f"{m['name']} — ({m['role']})": m for m in team_members}
            
            selected_option = st.selectbox(
                "Pilih Peran SDM / Nama Anggota",
                list(team_options.keys())
            )
            
            password_input = st.text_input("Password / Kata Sandi", type="password", placeholder="Masukkan password...")
            
            st.caption("💡 *Default Password untuk semua SDM:* `password123`")
            
            submit_login = st.form_submit_button("Masuk ke Sistem", use_container_width=True)
            
            if submit_login:
                chosen_member = team_options[selected_option]
                correct_pass = chosen_member.get("password", "password123")
                
                if secrets.compare_digest(password_input, correct_pass):
                    st.session_state["rbac_member_id"] = chosen_member.get("id")
                    add_log(f"User login: {chosen_member.get('name')} [{chosen_member.get('role')}]")
                    st.success(f"Selamat datang, {chosen_member.get('name')}!")
                    st.rerun()
                else:
                    st.error("❌ Password yang Anda masukkan salah. Coba lagi.")

        st.markdown("<br/>", unsafe_allow_html=True)
        with st.expander("ℹ️ Info Peran & Hak Akses SDM", expanded=False):
            st.markdown("""
            - **Project Manager**: Akses penuh supervisi, koordinasi, dan monitoring.
            - **Pemegang Dana Operasional**: Manajemen anggaran, pembuatan/penghapusan transaksi kas.
            - **Fasilitator Safeguards**: Peninjauan kegiatan, rekomendasi lingkungan dan dampak.
            - **Staf Administrasi**: Pengisian log, inventaris, serta pembaruan status tugas mingguan.
            """)
            
    st.stop()

with st.sidebar:
    st.markdown("### 🌲 Agroforestri Aren")
    st.caption("FOLU-NC4 Project Management")
    st.divider()

    # User Profile Info Badge
    st.markdown(f"**👤 Pengguna Aktif:**")
    st.markdown(f"**{authenticated_member.get('name')}**")
    st.markdown(f"<span class='role-badge'>{authenticated_member.get('role')}</span>", unsafe_allow_html=True)
    st.caption(f"Role Scope: {user_permissions.get('role_label')}")
    
    if st.button("🚪 Keluar (Logout)", key="rbac_logout", use_container_width=True):
        add_log(f"User logout: {authenticated_member.get('name')}")
        st.session_state.pop("rbac_member_id", None)
        st.rerun()

    st.divider()

    selected_tab = st.radio(
        "Navigasi Proyek",
        [
            "🛰️ Dashboard & Progres",
            "🧭 Manajemen Tugas",
            "📡 Kolaborasi & Chat",
            "🧠 Knowledge & Dokumen",
            "💰 Anggaran & SDM"
        ]
    )

    st.divider()
    
    # Calculate Overall Project Progress
    tasks = app_data.get("tasks", [])
    total_t = len(tasks)
    completed_t = len([t for t in tasks if t.get("status") == "Selesai"])
    overall_progress = int((completed_t / total_t) * 100) if total_t > 0 else 0

    st.markdown("**Total Progres Proyek**")
    st.progress(overall_progress / 100.0)
    st.caption(f"Capaian Fisik Lapangan: **{overall_progress}%** ({completed_t}/{total_t} Selesai)")

    st.divider()
    # Backup JSON Option
    backup_data = json.dumps(app_data, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Download Backup JSON",
        data=backup_data,
        file_name=f"Agroforestri_Aren_Backup_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True
    )
    st.caption("💡 *Backup ini dapat digunakan untuk pemulihan data atau migrasi ke sistem lain.*")
    st.caption(f"© {datetime.now().year} Agroforestri Aren. Hak cipta dilindungi.")
    

if selected_tab == "🛰️ Dashboard & Progres":
    st.title("🛰️ Dashboard & Progres Real-Time")
    st.caption(f"Agroforestri Aren - Enterprise Management | Selamat bertugas, {authenticated_member.get('name')}")

    # Overdue Deadline Alert Banner
    overdue_list = [t for t in app_data.get("tasks", []) if is_task_overdue(t)]
    if overdue_list:
        st.markdown(
            f"""
            <div class="overdue-alert">
                <strong>⚠️ Peringatan Overdue!</strong> Terdapat {len(overdue_list)} tugas yang telah melewati deadline:<br/>
                {" ".join([f"• <b>{t['title']}</b> (Deadline: {t['deadline']})<br/>" for t in overdue_list])}
            </div>
            """,
            unsafe_allow_html=True
        )

    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">TOTAL TUGAS</div>
                <div class="metric-value">{len(tasks)}</div>
                <div class="metric-sub">📋 Seluruh Modul</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">SELESAI</div>
                <div class="metric-value">{completed_t}</div>
                <div class="metric-sub">✅ {overall_progress}% Capaian</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    budgets = app_data.get("budgets", [])
    total_in = sum(b["amount"] for b in budgets if b.get("type") == "PEMASUKAN")
    total_out = sum(b["amount"] for b in budgets if b.get("type") == "PENGELUARAN")
    net_cash = total_in - total_out

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">NET CASH FLOW</div>
                <div class="metric-value">{format_rupiah(net_cash)}</div>
                <div class="metric-sub">💰 Saldo Operasional</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">ANGGOTA TIM</div>
                <div class="metric-value">{len(app_data.get('team', []))}</div>
                <div class="metric-sub">👥 Aktif Lapangan</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    # Charts Visualizations
    chart_col1, chart_col2 = st.columns([1, 1.5])

    with chart_col1:
        st.markdown("##### Status Tugas Proyek")
        not_started = len([t for t in tasks if t.get("status") == "Belum Dimulai"])
        in_progress = len([t for t in tasks if t.get("status") == "Dalam Proses"])

        fig1, ax1 = plt.subplots(figsize=(4, 3))
        fig1.patch.set_facecolor('#0a1b15')
        ax1.set_facecolor('#0a1b15')
        
        if total_t > 0:
            wedges, texts, autotexts = ax1.pie(
                [not_started, in_progress, completed_t],
                labels=["Belum", "Proses", "Selesai"],
                colors=["#94a3b8", "#0284c7", "#16a34a"],
                autopct="%1.0f%%",
                startangle=90,
                textprops=dict(color="#e2f3e8"),
                wedgeprops=dict(width=0.4, edgecolor='#0a1b15')
            )
        else:
            ax1.text(0.5, 0.5, "Belum ada tugas", ha="center", va="center", color="#e2f3e8")
        ax1.axis('equal')
        st.pyplot(fig1, use_container_width=True)

    with chart_col2:
        st.markdown("##### Ringkasan Cash Flow (Dalam Juta Rp)")
        fig2, ax2 = plt.subplots(figsize=(5, 2.5))
        fig2.patch.set_facecolor('#0a1b15')
        ax2.set_facecolor('#0a1b15')
        
        vals = [total_in / 1e6, total_out / 1e6, net_cash / 1e6]
        cats = ["Pemasukan", "Pengeluaran", "Net Cash"]
        colors_bar = ["#16a34a", "#dc2626", "#0284c7"]

        bars = ax2.bar(cats, vals, color=colors_bar, width=0.5)
        ax2.set_ylabel("Juta Rp", color="#e2f3e8")
        ax2.tick_params(colors='#e2f3e8')
        ax2.spines['bottom'].set_color('#315d46')
        ax2.spines['top'].set_color('#0a1b15')
        ax2.spines['right'].set_color('#0a1b15')
        ax2.spines['left'].set_color('#315d46')
        ax2.grid(axis='y', linestyle='--', alpha=0.3, color='#315d46')
        st.pyplot(fig2, use_container_width=True)

    # Priority Tasks & Logs
    b_col1, b_col2 = st.columns(2)

    with b_col1:
        st.markdown("##### 📌 Tugas Prioritas & Deadline Dekat")
        sorted_tasks = sorted(tasks, key=lambda x: x.get("deadline", ""))[:4]
        for t in sorted_tasks:
            status_color = "🟢" if t.get("status") == "Selesai" else ("🔵" if t.get("status") == "Dalam Proses" else "⚪")
            st.markdown(
                f"""
                <div style="background-color:#10251c; border:1px solid rgba(101, 220, 157, 0.2); padding:10px; border-radius:8px; margin-bottom:6px;">
                    {status_color} <b>[{t.get('categoryCode')}]</b> {t.get('title')}<br/>
                    <small style="color:#8ebfa3">PJ: {t.get('assignee')} | Deadline: {t.get('deadline')} | Priority: {t.get('priority')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

    with b_col2:
        st.markdown("##### 📜 Log Aktivitas Terakhir")
        for log in app_data.get("logs", [])[:5]:
            st.markdown(
                f"""
                <div style="border-bottom: 1px solid rgba(101, 220, 157, 0.15); padding: 6px 0;">
                    <span style="font-size:0.85rem; color:#dcebe2;">• {log.get('text')}</span><br/>
                    <small style="color:#719b83">{log.get('time')}</small>
                </div>
                """,
                unsafe_allow_html=True
            )

elif selected_tab == "🧭 Manajemen Tugas":
    st.title("🧭 Manajemen Tugas Proyek")
    st.caption("Kelola alur kerja, penanggung jawab, serta keterkaitan (dependency) antar kegiatan.")

    # Action Toolbar & Filters
    f_col1, f_col2, f_col3, f_col4 = st.columns([2, 1.5, 1.5, 1.5])

    with f_col1:
        search_kw = st.text_input("🔍 Cari Tugas", placeholder="Nama tugas atau PJ...")

    categories_list = ["Semua Kategori"] + [f"[{c['code']}] {c['name']}" for c in app_data.get("categories", [])]
    with f_col2:
        sel_cat = st.selectbox("Kategori Kegiatan", categories_list)

    with f_col3:
        sel_status = st.selectbox("Filter Status", ["Semua Status", "Belum Dimulai", "Dalam Proses", "Selesai"])

    with f_col4:
        sel_prio = st.selectbox("Filter Prioritas", ["Semua Prioritas", "Tinggi", "Sedang", "Rendah"])

    # Expandable Form for Adding/Editing Task according to User Permissions
    if user_permissions.get("create"):
        with st.expander("➕ Tambah Tugas Proyek Baru", expanded=False):
            with st.form("task_form", clear_on_submit=True):
                cat_opts = [f"[{c['code']}] {c['name']}" for c in app_data.get("categories", [])]
                t_cat = st.selectbox("Kategori Utama", cat_opts)
                t_title = st.text_input("Nama Tugas / Kegiatan")
                
                team_opts = [m["name"] for m in app_data.get("team", [])] or ["-"]
                t_assignee = st.selectbox("Penanggung Jawab (PJ)", team_opts, index=0)
                
                t_deadline = st.date_input("Deadline", datetime.now())
                
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    t_prio = st.selectbox("Prioritas", ["Tinggi", "Sedang", "Rendah"], index=1)
                with c_p2:
                    t_status = st.selectbox("Status Initial", ["Belum Dimulai", "Dalam Proses", "Selesai"])

                dep_opts = ["-- Tanpa Prasyarat --"] + [f"[{t['id']}] {t['title']}" for t in tasks]
                t_dep = st.selectbox("Prasyarat (Dependency)", dep_opts)

                submit_task = st.form_submit_button("Simpan Tugas Baru")

                if submit_task:
                    if not t_title.strip():
                        st.error("Nama tugas wajib diisi.")
                    else:
                        code = t_cat.split("]")[0].replace("[", "").strip()
                        name = t_cat.split("]")[1].strip()
                        dep_id = t_dep.split("]")[0].replace("[", "").strip() if t_dep != "-- Tanpa Prasyarat --" else ""

                        new_t = {
                            "id": f"task-{int(datetime.now().timestamp())}",
                            "categoryCode": code,
                            "categoryName": name,
                            "title": t_title.strip(),
                            "assignee": t_assignee,
                            "deadline": t_deadline.strftime("%Y-%m-%d"),
                            "priority": t_prio,
                            "status": t_status,
                            "dependency": dep_id
                        }
                        app_data.setdefault("tasks", []).append(new_t)
                        add_log(f"Tugas baru oleh {authenticated_member['name']}: [{code}] {t_title}")
                        st.success("Tugas berhasil disimpan!")
                        st.rerun()

    # Task Table Display
    filtered_tasks = []
    for t in tasks:
        if search_kw and not (search_kw.lower() in t.get("title", "").lower() or search_kw.lower() in t.get("assignee", "").lower()):
            continue
        if sel_cat != "Semua Kategori" and t.get("categoryCode") not in sel_cat:
            continue
        if sel_status != "Semua Status" and t.get("status") != sel_status:
            continue
        if sel_prio != "Semua Prioritas" and t.get("priority") != sel_prio:
            continue
        filtered_tasks.append(t)

    if filtered_tasks:
        df_tasks = pd.DataFrame(filtered_tasks)
        df_display = df_tasks[["categoryCode", "title", "assignee", "deadline", "priority", "status"]].copy()
        df_display.columns = ["Kode", "Nama Tugas", "Penanggung Jawab", "Deadline", "Prioritas", "Status"]
        df_display["Peringatan Deadline"] = [
            "⚠️ Deadline terlewati" if is_task_overdue(task) else "—"
            for task in filtered_tasks
        ]
        
        can_delete = user_permissions.get("delete")
        disabled_cols = ["Kode", "Peringatan Deadline"]
        if not user_permissions.get("update"):
            disabled_cols.extend(["Nama Tugas", "Penanggung Jawab", "Deadline", "Prioritas", "Status"])

        if can_delete:
            df_display["Hapus"] = False

        edited_display = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            disabled=disabled_cols,
            column_config={
                "Hapus": st.column_config.CheckboxColumn(
                    "Hapus",
                    help="Centang untuk menghapus tugas ini."
                )
            } if can_delete else {},
            key="task_table_editor"
        )

        editable_fields = {
            "Nama Tugas": "title",
            "Penanggung Jawab": "assignee",
            "Deadline": "deadline",
            "Prioritas": "priority",
            "Status": "status"
        }
        has_changes = False
        tasks_to_delete = set()
        
        for row_idx, task in enumerate(filtered_tasks):
            if can_delete and edited_display.iloc[row_idx].get("Hapus", False):
                tasks_to_delete.add(task.get("id"))
                continue
            if user_permissions.get("update"):
                for display_field, task_field in editable_fields.items():
                    value = edited_display.iloc[row_idx][display_field]
                    if value != task.get(task_field):
                        task[task_field] = value
                        has_changes = True
                        
        if tasks_to_delete:
            app_data["tasks"] = [
                task for task in app_data["tasks"]
                if task.get("id") not in tasks_to_delete
            ]
            add_log(f"{len(tasks_to_delete)} tugas dihapus oleh {authenticated_member['name']}.")
            has_changes = True
        if has_changes:
            save_data()
            st.rerun()
    else:
        st.info("Tidak ada tugas yang sesuai dengan kriteria filter.")

    if tasks:
        df_export = pd.DataFrame(tasks)
        csv_data = df_export.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📊 Download Laporan Tugas (.csv)",
            data=csv_data,
            file_name=f"Laporan_Tugas_Agroforestri_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

elif selected_tab == "📡 Kolaborasi & Chat":
    st.title("📡 Kolaborasi & Chat Virtual Proyek")
    st.caption("Ruang diskusi langsung tim lapangan dan pengumuman koordinasi.")

    col_chat, col_ann = st.columns([2, 1])

    with col_chat:
        st.markdown("##### 💬 Ruang Chat Diskusi")

        # Chat Messages Box
        chat_box = st.container(height=380)
        for msg in app_data.get("chat", []):
            is_me = msg.get('sender') == authenticated_member.get('name')
            bubble_class = "chat-bubble-self" if is_me else "chat-bubble-other"
            chat_box.markdown(
                f"""
                <div class="{bubble_class}">
                    <b>{msg.get('sender')}</b> <small style="color:#8ebfa3; float:right;">{msg.get('time')}</small><br/>
                    {msg.get('message')}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Send Form
        with st.form("send_chat_form", clear_on_submit=True):
            st.caption(f"Mengirim sebagai: **{authenticated_member.get('name')}**")
            msg_text = st.text_input("Pesan Diskusi", placeholder="Ketik koordinasi kegiatan...")
            send_btn = st.form_submit_button("Kirim Pesan ✉️")

            if send_btn and msg_text.strip():
                new_msg = {
                    "id": f"c-{int(datetime.now().timestamp())}",
                    "sender": authenticated_member.get('name'),
                    "message": msg_text.strip(),
                    "time": datetime.now().strftime("%H:%M")
                }
                app_data["chat"].append(new_msg)
                save_data()
                st.rerun()

    with col_ann:
        st.markdown("##### 📢 Pengumuman Penting")
        announcements = app_data.setdefault("announcements", [])
        for ann_index, ann in enumerate(announcements):
            st.warning(f"**{ann.get('title')}**\n\n{ann.get('message')}")
            ann_key = str(ann.get("id", ann_index))
            if user_permissions.get("update"):
                with st.expander(f"✏️ Kelola: {ann.get('title', 'Pengumuman')}"):
                    with st.form(f"edit_announcement_{ann_key}"):
                        updated_title = st.text_input("Judul Pengumuman", value=ann.get("title", ""))
                        updated_message = st.text_area("Isi Pengumuman", value=ann.get("message", ""))
                        update_announcement = st.form_submit_button("Simpan Perubahan")
                    if update_announcement:
                        title = (updated_title or "").strip()
                        message = (updated_message or "").strip()
                        if title and message:
                            ann["title"] = title
                            ann["message"] = message
                            save_data()
                            st.rerun()
                        else:
                            st.error("Judul dan isi pengumuman wajib diisi.")
                    if user_permissions.get("delete") and st.button("Hapus Pengumuman", key=f"delete_announcement_{ann_key}"):
                        announcements.pop(ann_index)
                        save_data()
                        st.rerun()

        if user_permissions.get("create"):
            with st.expander("➕ Tambah Pengumuman"):
                with st.form("add_announcement_form", clear_on_submit=True):
                    new_announcement_title = st.text_input("Judul Pengumuman Baru")
                    new_announcement_message = st.text_area("Isi Pengumuman Baru")
                    add_announcement = st.form_submit_button("Tambahkan Pengumuman")
                if add_announcement:
                    if new_announcement_title.strip() and new_announcement_message.strip():
                        announcements.append({
                            "id": f"ann-{int(datetime.now().timestamp())}-{secrets.token_hex(3)}",
                            "title": new_announcement_title.strip(),
                            "message": new_announcement_message.strip()
                        })
                        save_data()
                        st.rerun()
                    else:
                        st.error("Judul dan isi pengumuman wajib diisi.")

        st.markdown("##### 👥 Anggota Tim Proyek")
        for member in app_data.get("team", []):
            st.markdown(f"• **{member.get('name')}**  \n*{member.get('role')}*")

elif selected_tab == "🧠 Knowledge & Dokumen":
    st.title("🧠 Manajemen Pengetahuan & Dokumen")
    st.caption("Pusat pencarian SOP, template laporan, regulasi, dan referensi proyek agroforestri.")

    docs = app_data.get("documents", [])
    known_categories = ["SOP & Panduan", "Template Laporan", "Kontrak & Legal", "Peta & Survei"]
    categories = sorted(set(known_categories + [d.get("category", "Lainnya") for d in docs]))
    search_col, category_col = st.columns([2, 1])
    with search_col:
        search_doc = st.text_input("🔍 Cari Dokumen / SOP", placeholder="Judul, kategori, atau kata kunci ringkasan...")
    with category_col:
        selected_category = st.selectbox("Filter Kategori", ["Semua Kategori"] + categories)

    if user_permissions.get("create"):
        with st.expander("➕ Unggah / Tambah Dokumen Baru", expanded=False):
            with st.form("doc_form", clear_on_submit=True):
                doc_t = st.text_input("Judul Dokumen")
                doc_cat = st.selectbox("Kategori Dokumen", ["SOP & Panduan", "Template Laporan", "Kontrak & Legal", "Peta & Survei"])
                doc_sum = st.text_area("Ringkasan Ringkas Isi Dokumen")
                doc_url = st.text_input("URL Link File", value="https://")
                
                sub_doc = st.form_submit_button("Simpan Dokumen")
                if sub_doc and doc_t.strip():
                    new_doc = {
                        "id": f"doc-{int(datetime.now().timestamp())}",
                        "title": doc_t.strip(),
                        "category": doc_cat,
                        "summary": doc_sum.strip(),
                        "url": doc_url,
                        "date": datetime.now().strftime("%Y-%m-%d")
                    }
                    app_data.setdefault("documents", []).append(new_doc)
                    save_data()
                    add_log(f"Dokumen baru diunggah oleh {authenticated_member['name']}: {doc_t}")
                    st.success("Dokumen berhasil disimpan!")
                    st.rerun()

    # Document Cards Grid
    filtered_docs = [
        d for d in docs
        if (not search_doc.strip() or search_doc.strip().lower() in " ".join([
            str(d.get("title", "")), str(d.get("summary", "")), str(d.get("category", ""))
        ]).lower())
        and (selected_category == "Semua Kategori" or d.get("category") == selected_category)
    ]
    filtered_docs.sort(key=lambda d: str(d.get("date", "")), reverse=True)
    st.caption(f"Menampilkan {len(filtered_docs)} dari {len(docs)} dokumen")

    if not filtered_docs:
        st.info("Tidak ada dokumen yang cocok. Ubah kata kunci atau pilih kategori lain.")
    else:
        doc_cols = st.columns(3)
        for idx, d in enumerate(filtered_docs):
            with doc_cols[idx % 3]:
                st.markdown(
                    f"""
                    <div style="background:#10251c; border:1px solid rgba(101, 220, 157, 0.22); border-radius:12px; padding:16px; margin-bottom:12px;">
                        <span style="font-size:0.7rem; font-weight:700; background:rgba(66, 201, 135, 0.15); color:#8eeeb6; padding:2px 8px; border-radius:4px;">{d.get('category', 'Lainnya')}</span>
                        <h4 style="margin-top:8px; margin-bottom:4px; font-size:1rem; color:#b9f6d0;">{d.get('title', 'Tanpa judul')}</h4>
                        <p style="font-size:0.8rem; color:#a9c2b2;">{d.get('summary', '')}</p>
                        <small style="color:#68dda0;">Tanggal: {d.get('date', '-')}</small><br/><br/>
                        <a href="{d.get('url', '#')}" target="_blank" style="font-size:0.8rem; font-weight:600; color:#42c987; text-decoration:none;">🔗 Buka Dokumen</a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

elif selected_tab == "💰 Anggaran & SDM":
    st.title("💼 Pengelolaan Anggaran, Arus Kas & SDM")
    st.caption("Pencatatan realisasi cash flow pemasukan, pengeluaran, serta manajemen anggota tim.")

    budgets = app_data.get("budgets", [])
    total_in = sum(b["amount"] for b in budgets if b.get("type") == "PEMASUKAN")
    total_out = sum(b["amount"] for b in budgets if b.get("type") == "PENGELUARAN")
    net_bal = total_in - total_out

    # Summary Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("TOTAL PEMASUKAN", format_rupiah(total_in), "Inflow Modal/Hibah")
    c2.metric("TOTAL PENGELUARAN", format_rupiah(total_out), "- Outflow Operasional")
    c3.metric("NET CASH FLOW (SALDO)", format_rupiah(net_bal), "Saldo Kas Aktif")

    st.divider()

    col_b_table, col_b_form = st.columns([2, 1])

    with col_b_table:
        st.markdown("##### 📊 Jurnal Arus Kas (Financial Log)")
        if budgets:
            df_b = pd.DataFrame(budgets)
            df_b["Nominal (Rp)"] = df_b["amount"].apply(format_rupiah)
            df_b["Kode Transaksi"] = df_b.get("code", pd.Series(index=df_b.index, dtype="object")).fillna("-")
            df_display_b = df_b[["Kode Transaksi", "type", "category", "title", "Nominal (Rp)", "date"]].copy()
            df_display_b.columns = ["Kode Transaksi", "Tipe", "Kategori", "Deskripsi Pos Biaya", "Nominal", "Tanggal"]

            # Perbaikan dan penghapusan dikelola langsung dari tabel jurnal.
            if user_permissions.get("update"):
                editor_rows = []
                for budget_idx, budget in enumerate(budgets):
                    editor_rows.append({
                        "_id": str(budget.get("id", f"legacy-{budget_idx}")),
                        "Kode Transaksi": budget.get("code", "-"),
                        "Hapus": False,
                        "Tipe": budget.get("type", "PENGELUARAN"),
                        "Kategori": budget.get("category", ""),
                        "Deskripsi Pos Biaya": budget.get("title", ""),
                        "Nominal (Rp)": budget.get("amount", 0),
                        "Tanggal": budget.get("date", "")
                    })
                edited_budgets = st.data_editor(
                    pd.DataFrame(editor_rows),
                    use_container_width=True,
                    hide_index=True,
                    disabled=["_id", "Kode Transaksi", "Hapus"] if not user_permissions.get("delete") else ["_id", "Kode Transaksi"],
                    column_config={
                        "_id": None,
                        "Kode Transaksi": st.column_config.TextColumn("Kode Transaksi"),
                        "Tipe": st.column_config.SelectboxColumn("Tipe", options=["PEMASUKAN", "PENGELUARAN"], required=True),
                        "Kategori": st.column_config.TextColumn("Kategori", required=True),
                        "Deskripsi Pos Biaya": st.column_config.TextColumn("Deskripsi Pos Biaya", required=True),
                        "Nominal (Rp)": st.column_config.NumberColumn("Nominal (Rp)", min_value=1, step=500000, required=True),
                        "Tanggal": st.column_config.TextColumn("Tanggal (YYYY-MM-DD)", required=True)
                    },
                    key="cashflow_journal_editor"
                )

                if st.button("💾 Terapkan Perubahan Jurnal", key="save_cashflow_journal"):
                    original_by_id = {
                        str(budget.get("id", f"legacy-{idx}")): budget
                        for idx, budget in enumerate(budgets)
                    }
                    revised_budgets = []
                    invalid_rows = []
                    deleted_budgets = []
                    for _, row in edited_budgets.iterrows():
                        transaction_id = str(row["_id"])
                        original = original_by_id.get(transaction_id)
                        if original is None:
                            continue
                        if bool(row["Hapus"]) and user_permissions.get("delete"):
                            deleted_budgets.append(original)
                            continue
                        try:
                            amount = int(row["Nominal (Rp)"])
                            title = str(row["Deskripsi Pos Biaya"]).strip()
                            category = str(row["Kategori"]).strip()
                            transaction_type = str(row["Tipe"])
                            transaction_date = datetime.strptime(str(row["Tanggal"]), "%Y-%m-%d").strftime("%Y-%m-%d")
                            if amount <= 0 or not title or not category or transaction_type not in ["PEMASUKAN", "PENGELUARAN"]:
                                raise ValueError
                        except (TypeError, ValueError, OverflowError):
                            invalid_rows.append(original.get("title", "Transaksi"))
                            revised_budgets.append(original)
                            continue

                        revised = dict(original)
                        revised.update({
                            "type": transaction_type,
                            "category": category,
                            "title": title,
                            "amount": amount,
                            "date": transaction_date
                        })
                        if revised != original:
                            add_log(f"User {authenticated_member['name']} memperbaiki transaksi: {title}")
                        revised_budgets.append(revised)

                    for removed_budget in deleted_budgets:
                        evidence_path = removed_budget.get("evidence")
                        if evidence_path:
                            evidence_abs = os.path.abspath(evidence_path)
                            evidence_dir = os.path.abspath("bukti")
                            try:
                                if os.path.commonpath([evidence_abs, evidence_dir]) == evidence_dir and os.path.isfile(evidence_abs):
                                    os.remove(evidence_abs)
                            except ValueError:
                                pass
                        add_log(f"User {authenticated_member['name']} menghapus transaksi: {removed_budget.get('title')}")

                    if invalid_rows:
                        st.error("Perubahan tidak valid diabaikan: " + ", ".join(invalid_rows))
                    if revised_budgets != budgets:
                        app_data["budgets"] = revised_budgets
                        save_data()
                        st.success("Perubahan jurnal berhasil diterapkan.")
                        st.rerun()
                    elif not invalid_rows:
                        st.info("Tidak ada perubahan untuk diterapkan.")
            else:
                st.dataframe(df_display_b, use_container_width=True, hide_index=True)

            # Evidence images expander
            for budget_idx, budget in enumerate(budgets):
                with st.expander(f"🖼️ Bukti Transaksi: {budget.get('title', 'Transaksi')} ({budget.get('date', '-')})"):
                    evidence_path = budget.get("evidence")
                    if evidence_path and os.path.isfile(evidence_path):
                        st.image(evidence_path, caption="Bukti transaksi", use_container_width=True)
                    else:
                        st.caption("Tidak ada gambar bukti terlampir.")

            # Export Excel Cashflow
            csv_b = df_b.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Laporan Arus Kas (.csv)",
                data=csv_b,
                file_name=f"CashFlow_Agroforestri_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    with col_b_form:
        st.markdown("##### 📝 Catat Transaksi Cash Flow")
        if user_permissions.get("create"):
            b_type = st.radio("Tipe Transaksi", ["PEMASUKAN", "PENGELUARAN"], horizontal=True)

            if b_type == "PEMASUKAN":
                b_cat = st.selectbox("Kategori Pos", ["Modal / Investor", "Hibah / Bantuan", "Hasil Penjualan / Produk", "Pemasukan Lainnya"])
            else:
                b_cat = st.selectbox("Kategori Pos", ["Peralatan & Bibit", "Operasional Lapangan", "Tenaga Kerja", "Logistik & Transport", "Pengeluaran Lainnya"])

            b_evidence_file = st.file_uploader("Upload Foto/Gambar Bukti", type=["jpg", "jpeg", "png", "webp"])
            b_camera_photo = st.camera_input("Ambil Foto Bukti dengan Kamera", disabled=b_evidence_file is not None)

            with st.form("budget_entry_form", clear_on_submit=True):
                b_title = st.text_input("Deskripsi Transaksi", placeholder="Contoh: Pencairan Termin 1 Modal")
                b_amount = st.number_input("Nominal (Rp)", min_value=0, step=500000)
                b_date = st.date_input("Tanggal Transaksi", datetime.now())

                sub_b = st.form_submit_button("Simpan Transaksi")
                if sub_b:
                    if not b_title.strip() or b_amount <= 0:
                        st.error("Isi deskripsi dan nominal transaksi dengan benar.")
                    else:
                        type_code = "IN" if b_type == "PEMASUKAN" else "OUT"
                        category_code = "".join(
                            word[0].upper()
                            for word in b_cat.split()
                            if word.isalnum()
                        ) or "LAIN"
                        code_prefix = f"CF-{type_code}-{category_code}-"
                        last_sequence = max(
                            (
                                int(code.rsplit("-", 1)[-1])
                                for code in (
                                    str(budget.get("code", ""))
                                    for budget in app_data.get("budgets", [])
                                )
                                if code.startswith(code_prefix) and code.rsplit("-", 1)[-1].isdigit()
                            ),
                            default=0
                        )
                        new_b = {
                            "id": f"b-{int(datetime.now().timestamp())}",
                            "code": f"{code_prefix}{last_sequence + 1:04d}",
                            "type": b_type,
                            "category": b_cat,
                            "title": b_title.strip(),
                            "amount": b_amount,
                            "date": b_date.strftime("%Y-%m-%d")
                        }
                        evidence = b_camera_photo or b_evidence_file
                        try:
                            if evidence:
                                os.makedirs("bukti", exist_ok=True)
                                evidence_name = getattr(evidence, "name", "")
                                evidence_ext = os.path.splitext(evidence_name)[1].lower()
                                if evidence_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                                    evidence_ext = ".png" if b_camera_photo else ".jpg"
                                evidence_path = os.path.join(
                                    "bukti",
                                    f"{new_b['id']}-{datetime.now().strftime('%f')}{evidence_ext}"
                                )
                                with open(evidence_path, "wb") as evidence_file:
                                    evidence_file.write(evidence.getvalue())
                                new_b["evidence"] = evidence_path

                            app_data["budgets"].append(new_b)
                            add_log(f"Transaksi Cash Flow oleh {authenticated_member['name']} ({b_type}): {b_title} ({format_rupiah(b_amount)})")
                            st.success("Transaksi berhasil dicatat!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menyimpan transaksi atau foto bukti: {e}")
        else:
            st.info("Peran Anda tidak memiliki hak akses untuk menambahkan pencatatan transaksi keuangan baru.")

    st.divider()

    # Team SDM Section
    st.markdown("##### 👥 Manajemen Sumber Daya Manusia (SDM)")
    team_df = pd.DataFrame(app_data.get("team", []))
    if not team_df.empty:
        st.dataframe(team_df[["name", "role", "username"]], use_container_width=True, hide_index=True)

    team_members = app_data.get("team", [])
    if team_members and (user_permissions.get("update") or user_permissions.get("delete")):
        selected_team_idx = st.selectbox(
            "Pilih anggota tim untuk dikelola",
            range(len(team_members)),
            format_func=lambda idx: f"{team_members[idx].get('name', 'Tanpa nama')} ({team_members[idx].get('username', '-')})",
            key="manage_team_member"
        )
        selected_member = team_members[selected_team_idx]

        if user_permissions.get("update"):
            with st.expander("✏️ Perbaiki Data Anggota Tim", expanded=False):
                with st.form("edit_team_form"):
                    edit_name = st.text_input("Nama Lengkap & Gelar", value=selected_member.get("name", ""))
                    edit_role = st.text_input("Peran / Jabatan Proyek", value=selected_member.get("role", ""))
                    edit_user = st.text_input("Username Login", value=selected_member.get("username", ""))
                    edit_pass = st.text_input("Password Baru (kosongkan jika tidak diubah)", type="password")
                    submit_edit = st.form_submit_button("Simpan Perubahan")

                    if submit_edit:
                        edit_name_value = (edit_name or "").strip()
                        edit_role_value = (edit_role or "").strip()
                        edit_user_value = (edit_user or "").strip()
                        edit_pass_value = (edit_pass or "").strip()
                        if not edit_name_value or not edit_role_value or not edit_user_value:
                            st.error("Nama, peran, dan username wajib diisi.")
                        else:
                            selected_member["name"] = edit_name_value
                            selected_member["role"] = edit_role_value
                            selected_member["username"] = edit_user_value
                            if edit_pass_value:
                                selected_member["password"] = edit_pass_value
                            add_log(f"Data anggota tim diperbarui oleh {authenticated_member['name']}: {edit_name_value}")
                            st.success("Data anggota tim berhasil diperbarui!")
                            st.rerun()

        if user_permissions.get("delete"):
            confirm_team_delete = st.checkbox(
                f"Konfirmasi hapus anggota tim {selected_member.get('name', '')}",
                key=f"confirm_delete_team_{selected_member.get('id', selected_team_idx)}"
            )
            if st.button("🗑️ Hapus Anggota Tim", disabled=not confirm_team_delete):
                removed_member = team_members.pop(selected_team_idx)
                add_log(f"Anggota tim dihapus oleh {authenticated_member['name']}: {removed_member.get('name', '')}")
                st.success("Anggota tim berhasil dihapus!")
                st.rerun()

    if user_permissions.get("create"):
        with st.expander("➕ Tambah Anggota Tim SDM Baru", expanded=False):
            with st.form("add_team_form", clear_on_submit=True):
                m_name = st.text_input("Nama Lengkap & Gelar")
                m_role = st.text_input("Peran / Jabatan Proyek")
                m_user = st.text_input("Username Login")
                m_pass = st.text_input("Password Default", value="password123", type="password")
                sub_m = st.form_submit_button("Simpan Anggota Tim")

                if sub_m and m_name.strip() and m_role.strip():
                    new_m = {
                        "id": f"tm-{int(datetime.now().timestamp())}",
                        "name": m_name.strip(),
                        "role": m_role.strip(),
                        "username": m_user.strip() if m_user.strip() else m_name.lower().replace(" ", "."),
                        "password": m_pass.strip() if m_pass.strip() else "password123"
                    }
                    app_data["team"].append(new_m)
                    add_log(f"Anggota tim baru ditambahkan oleh {authenticated_member['name']}: {m_name}")
                    st.success("Anggota tim berhasil ditambahkan!")
                    st.rerun()
                    
st.divider()
st.caption("Sistem Informasi Manajemen Proyek Agroforestri Aren | Versi 3.0 | Pengembang: Tim Pengembang SIM Agroforestri Aren")
st.caption(f"© {datetime.now().year} Center of Systems. Hak cipta dilindungi.")