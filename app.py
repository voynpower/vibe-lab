# =====================================================================
# 성적 관리 웹 애플리케이션 (Flask + SQLite + Chart.js + 검색/필터/정렬)
# 실행 방법: python3 app.py
# 접속 주소: http://127.0.0.1:5000
# =====================================================================

import sqlite3
from flask import Flask, render_template_string, request, redirect, url_for, flash
from grades import DB_FILE, Student, GradeManager

app = Flask(__name__)
app.secret_key = "vibe-lab-grades-secret-key"

# 최초 실행 시 테이블 생성 및 CSV 마이그레이션 보장
_init_mgr = GradeManager(DB_FILE)
_init_mgr.close()


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>학생 성적 관리 대시보드</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg: #f8fafc;
            --card: #ffffff;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --danger: #dc2626;
            --danger-hover: #b91c1c;
            --success-bg: #dcfce7;
            --success-text: #15803d;
            --fail-bg: #fee2e2;
            --fail-text: #b91c1c;
            --text: #1e293b;
            --muted: #64748b;
            --border: #e2e8f0;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Pretendard", "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            padding: 2rem 1rem;
        }
        .container {
            max-width: 1180px;
            margin: 0 auto;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        header h1 {
            font-size: 1.6rem;
            font-weight: 700;
        }
        header span {
            font-size: 0.9rem;
            color: var(--muted);
            background: #e2e8f0;
            padding: 0.3rem 0.75rem;
            border-radius: 999px;
        }
        .flash {
            padding: 0.85rem 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1.25rem;
            font-weight: 500;
            background: #dbeafe;
            color: #1e40af;
            border: 1px solid #bfdbfe;
        }
        .flash.error {
            background: var(--fail-bg);
            color: var(--fail-text);
            border-color: #fecaca;
        }
        /* 상단 요약 카드 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
            margin-bottom: 1.25rem;
        }
        .stat-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.2rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .stat-card .label {
            font-size: 0.85rem;
            color: var(--muted);
            margin-bottom: 0.4rem;
        }
        .stat-card .value {
            font-size: 1.5rem;
            font-weight: 700;
        }
        .stat-card .sub {
            font-size: 0.8rem;
            color: var(--muted);
            margin-top: 0.35rem;
        }
        /* 차트 그리드 (3열) */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        @media (max-width: 980px) {
            .charts-grid { grid-template-columns: 1fr; }
        }
        .chart-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1rem 1.2rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            display: flex;
            flex-direction: column;
        }
        .chart-card h3 {
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chart-card h3 small {
            font-size: 0.78rem;
            font-weight: 500;
            color: var(--muted);
        }
        .chart-box {
            position: relative;
            height: 220px;
            width: 100%;
        }
        /* 메인 그리드 (좌측 입력폼 + 우측 테이블) */
        .main-grid {
            display: grid;
            grid-template-columns: 310px 1fr;
            gap: 1.5rem;
            align-items: start;
        }
        @media (max-width: 900px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .card h2 {
            font-size: 1.1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid var(--border);
        }
        .form-group {
            margin-bottom: 0.9rem;
        }
        .form-group label {
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 0.35rem;
        }
        .form-group input, .filter-input, .filter-select {
            width: 100%;
            padding: 0.55rem 0.75rem;
            border: 1px solid var(--border);
            border-radius: 0.45rem;
            font-size: 0.92rem;
            background: #fff;
        }
        .form-group input:focus, .filter-input:focus, .filter-select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
        }
        .btn-row {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .btn {
            cursor: pointer;
            border: none;
            border-radius: 0.45rem;
            padding: 0.6rem 1rem;
            font-size: 0.9rem;
            font-weight: 600;
            transition: background 0.15s, color 0.15s;
        }
        .btn-primary {
            flex: 1;
            background: var(--primary);
            color: #fff;
        }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-secondary {
            background: #e2e8f0;
            color: var(--text);
        }
        .btn-secondary:hover { background: #cbd5e1; }
        .btn-sm {
            padding: 0.3rem 0.6rem;
            font-size: 0.8rem;
        }
        .btn-danger {
            background: #fee2e2;
            color: var(--danger);
        }
        .btn-danger:hover {
            background: var(--danger);
            color: #fff;
        }
        /* 검색 & 필터 툴바 */
        .toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 0.6rem;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            background: #f8fafc;
            padding: 0.75rem;
            border-radius: 0.6rem;
            border: 1px solid var(--border);
        }
        .toolbar-left {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
            flex: 1;
        }
        .search-box {
            min-width: 180px;
            flex: 1;
            max-width: 240px;
        }
        .tab-group {
            display: inline-flex;
            background: #e2e8f0;
            padding: 0.2rem;
            border-radius: 0.5rem;
            gap: 0.15rem;
        }
        .tab-btn {
            border: none;
            background: transparent;
            padding: 0.35rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 600;
            border-radius: 0.35rem;
            cursor: pointer;
            color: #475569;
        }
        .tab-btn.active {
            background: #fff;
            color: var(--primary);
            box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        }
        .toolbar-right {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }
        .toolbar-right select {
            width: auto;
            padding: 0.42rem 0.65rem;
            font-size: 0.84rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }
        th, td {
            padding: 0.72rem 0.55rem;
            text-align: center;
            border-bottom: 1px solid var(--border);
        }
        th {
            background: #f1f5f9;
            font-weight: 600;
            color: #475569;
            cursor: pointer;
            user-select: none;
        }
        th:hover {
            background: #e2e8f0;
        }
        tbody tr {
            cursor: pointer;
            transition: background 0.12s;
        }
        tbody tr:hover {
            background: #eff6ff;
        }
        tbody tr.row-fail {
            background: #fff5f5;
        }
        tbody tr.row-fail:hover {
            background: #fee2e2;
        }
        tbody tr.row-selected {
            outline: 2px solid var(--primary);
            background: #eff6ff !important;
        }
        .badge {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .badge-pass {
            background: var(--success-bg);
            color: var(--success-text);
        }
        .badge-fail {
            background: var(--fail-bg);
            color: var(--fail-text);
        }
        .grade-pill {
            display: inline-block;
            width: 26px;
            height: 26px;
            line-height: 26px;
            border-radius: 50%;
            font-weight: 700;
            font-size: 0.85rem;
            background: #e2e8f0;
            color: #1e293b;
        }
        .grade-A { background: #dbeafe; color: #1d4ed8; }
        .grade-B { background: #dcfce7; color: #15803d; }
        .grade-C { background: #fef9c3; color: #a16207; }
        .grade-D { background: #ffedd5; color: #c2410c; }
        .grade-F { background: #fee2e2; color: #b91c1c; }
        .actions {
            display: flex;
            justify-content: center;
            gap: 0.35rem;
        }
        .filter-summary {
            font-size: 0.82rem;
            color: var(--muted);
            margin-bottom: 0.6rem;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>🎓 성적 관리 대시보드</h1>
        <span>SQLite DB: {{ db_file }}</span>
    </header>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <!-- 상단 통계 요약 카드 -->
    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">전체 학생 / 합격률</div>
            <div class="value">{{ stats.total }}명 <small style="font-size:1rem;color:var(--primary);">({{ stats.pass_rate }}%)</small></div>
            <div class="sub">통과(Pass): {{ stats.pass_count }}명 · 불합격(Fail): {{ stats.fail_count }}명</div>
        </div>
        {% for subj in stats.subjects %}
        <div class="stat-card">
            <div class="label">{{ subj.label }} 평균</div>
            <div class="value">{{ subj.avg }}점</div>
            <div class="sub">최고: {{ subj.max }}점 · 최저: {{ subj.min }}점</div>
        </div>
        {% endfor %}
    </div>

    <!-- 2번 Plan: 성적 분포 시각화 차트 (Chart.js) -->
    <div class="charts-grid">
        <div class="chart-card">
            <h3>🍩 등급 분포 (A~F) <small>전체 학생 비율</small></h3>
            <div class="chart-box">
                <canvas id="gradeDoughnutChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>📊 과목별 성적 통계 <small>평균 · 최고 · 최저</small></h3>
            <div class="chart-box">
                <canvas id="subjectBarChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>🎯 개인 vs 반 평균 비교 <small id="radarStudentLabel">학생 행을 클릭해보세요</small></h3>
            <div class="chart-box">
                <canvas id="studentRadarChart"></canvas>
            </div>
        </div>
    </div>

    <div class="main-grid">
        <!-- 좌측: 학생 추가 / 수정 폼 -->
        <div class="card" id="form-card">
            <h2 id="form-title">➕ 학생 추가 / 수정</h2>
            <form method="POST" action="{{ url_for('save_student') }}">
                <div class="form-group">
                    <label for="name">이름</label>
                    <input type="text" id="name" name="name" placeholder="예: 홍길동" required>
                </div>
                <div class="form-group">
                    <label for="korean">국어 점수 (0~100)</label>
                    <input type="number" id="korean" name="korean" min="0" max="100" placeholder="0 ~ 100" required>
                </div>
                <div class="form-group">
                    <label for="english">영어 점수 (0~100)</label>
                    <input type="number" id="english" name="english" min="0" max="100" placeholder="0 ~ 100" required>
                </div>
                <div class="form-group">
                    <label for="math">수학 점수 (0~100)</label>
                    <input type="number" id="math" name="math" min="0" max="100" placeholder="0 ~ 100" required>
                </div>
                <div class="btn-row">
                    <button type="submit" class="btn btn-primary" id="submit-btn">저장하기</button>
                    <button type="button" class="btn btn-secondary" onclick="resetForm()">초기화</button>
                </div>
            </form>
            <p style="font-size:0.8rem; color:var(--muted); margin-top:0.85rem; line-height:1.45;">
                💡 <b>Tip:</b><br>
                • 학생 행을 클릭하면 상단 <b>개인 레이더 차트</b>에 반 평균 대비 강약점이 표시됩니다.<br>
                • <b>[수정]</b> 버튼을 누르면 점수가 입력창에 자동으로 채워집니다.
            </p>
        </div>

        <!-- 우측: 검색/필터/정렬 + 전체 학생 성적 목록 -->
        <div class="card">
            <h2>📋 전체 학생 성적표</h2>

            <!-- 1번 Plan: 실시간 검색 및 조건별 필터/정렬 툴바 -->
            <div class="toolbar">
                <div class="toolbar-left">
                    <input type="text" id="searchInput" class="filter-input search-box"
                           placeholder="🔍 학생 이름 검색..." oninput="applyFilters()">
                    <div class="tab-group" id="statusTabs">
                        <button type="button" class="tab-btn active" data-status="ALL" onclick="setStatusFilter('ALL', this)">전체</button>
                        <button type="button" class="tab-btn" data-status="Pass" onclick="setStatusFilter('Pass', this)">Pass만</button>
                        <button type="button" class="tab-btn" data-status="Fail" onclick="setStatusFilter('Fail', this)">Fail만</button>
                    </div>
                </div>
                <div class="toolbar-right">
                    <select id="gradeFilter" class="filter-select" onchange="applyFilters()" title="등급 필터">
                        <option value="ALL">모든 등급 (A~F)</option>
                        <option value="A">A 등급 (90↑)</option>
                        <option value="B">B 등급 (80↑)</option>
                        <option value="C">C 등급 (70↑)</option>
                        <option value="D">D 등급 (60↑)</option>
                        <option value="F">F 등급 (60↓)</option>
                    </select>
                    <select id="sortSelect" class="filter-select" onchange="applyFilters()" title="정렬 기준">
                        <option value="avg_desc">정렬: 평균 높은순</option>
                        <option value="avg_asc">정렬: 평균 낮은순</option>
                        <option value="kor_desc">정렬: 국어 높은순</option>
                        <option value="eng_desc">정렬: 영어 높은순</option>
                        <option value="mat_desc">정렬: 수학 높은순</option>
                        <option value="name_asc">정렬: 이름 가나다순</option>
                    </select>
                </div>
            </div>

            <div class="filter-summary">
                <span id="visibleCountText">전체 {{ students|length }}명 표시 중</span>
                <a href="javascript:void(0)" onclick="resetFilters()" style="color:var(--primary);text-decoration:none;font-weight:600;">필터 초기화 ↺</a>
            </div>

            {% if students %}
            <table id="studentsTable">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th onclick="quickSort('name_asc')">이름 ↕</th>
                        <th onclick="quickSort('kor_desc')">국어 ↕</th>
                        <th onclick="quickSort('eng_desc')">영어 ↕</th>
                        <th onclick="quickSort('mat_desc')">수학 ↕</th>
                        <th onclick="quickSort('avg_desc')">평균 ↕</th>
                        <th>등급</th>
                        <th>판정</th>
                        <th>관리</th>
                    </tr>
                </thead>
                <tbody id="studentsTbody">
                    {% for s in students %}
                    <tr class="student-row {{ 'row-fail' if s.status != 'Pass' else '' }}"
                        data-name="{{ s.name }}"
                        data-korean="{{ s.korean }}"
                        data-english="{{ s.english }}"
                        data-math="{{ s.math }}"
                        data-average="{{ '%.4f'|format(s.average) }}"
                        data-grade="{{ s.grade }}"
                        data-status="{{ s.status }}"
                        onclick="selectStudentForRadar(this)">
                        <td class="rank-cell">{{ loop.index }}</td>
                        <td style="font-weight:600;">{{ s.name }}</td>
                        <td style="{{ 'color:#dc2626;font-weight:700;' if s.korean < 40 else '' }}">{{ s.korean }}</td>
                        <td style="{{ 'color:#dc2626;font-weight:700;' if s.english < 40 else '' }}">{{ s.english }}</td>
                        <td style="{{ 'color:#dc2626;font-weight:700;' if s.math < 40 else '' }}">{{ s.math }}</td>
                        <td style="font-weight:700;">{{ "%.2f"|format(s.average) }}</td>
                        <td><span class="grade-pill grade-{{ s.grade }}">{{ s.grade }}</span></td>
                        <td>
                            <span class="badge {{ 'badge-pass' if s.status == 'Pass' else 'badge-fail' }}">
                                {{ s.status }}
                            </span>
                        </td>
                        <td onclick="event.stopPropagation();">
                            <div class="actions">
                                <button type="button" class="btn btn-secondary btn-sm"
                                    data-name="{{ s.name }}"
                                    data-korean="{{ s.korean }}"
                                    data-english="{{ s.english }}"
                                    data-math="{{ s.math }}"
                                    onclick="fillFormFromBtn(this)">
                                    수정
                                </button>
                                <form method="POST" action="{{ url_for('delete_student', name=s.name) }}"
                                      data-name="{{ s.name }}"
                                      onsubmit="return confirm('정말 \\'' + this.dataset.name + '\\' 학생을 삭제하시겠습니까?');"
                                      style="display:inline;">
                                    <button type="submit" class="btn btn-danger btn-sm">삭제</button>
                                </form>
                            </div>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <p id="emptyFilterMsg" style="display:none; padding:2rem; text-align:center; color:var(--muted);">
                조건에 맞는 학생이 없습니다.
            </p>
            {% else %}
            <p style="padding:2rem; text-align:center; color:var(--muted);">등록된 학생이 없습니다.</p>
            {% endif %}
        </div>
    </div>
</div>

<script>
// 서버에서 전달된 차트용 데이터
const CHART_DATA = {{ chart_data|tojson }};
let currentStatusFilter = 'ALL';
let radarChartInstance = null;

// 1. 수정 폼 채우기 & 초기화
function fillFormFromBtn(btn) {
    const name = btn.dataset.name;
    const kor = btn.dataset.korean;
    const eng = btn.dataset.english;
    const mat = btn.dataset.math;

    const formCard = document.getElementById('form-card');
    document.getElementById('form-title').innerText = '✏️ 학생 점수 수정 (' + name + ')';
    const nameInput = document.getElementById('name');
    nameInput.value = name;
    nameInput.readOnly = true;
    nameInput.style.backgroundColor = '#f1f5f9';

    document.getElementById('korean').value = kor;
    document.getElementById('english').value = eng;
    document.getElementById('math').value = mat;
    document.getElementById('submit-btn').innerText = '수정 저장';

    formCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    formCard.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.4)';
    setTimeout(() => { formCard.style.boxShadow = ''; }, 1200);
    document.getElementById('korean').focus();
    document.getElementById('korean').select();
}

function resetForm() {
    document.getElementById('form-title').innerText = '➕ 학생 추가 / 수정';
    const nameInput = document.getElementById('name');
    nameInput.value = '';
    nameInput.readOnly = false;
    nameInput.style.backgroundColor = '';

    document.getElementById('korean').value = '';
    document.getElementById('english').value = '';
    document.getElementById('math').value = '';
    document.getElementById('submit-btn').innerText = '저장하기';
}

// 2. 실시간 검색, 상태/등급 필터링 및 정렬
function setStatusFilter(status, btnEl) {
    currentStatusFilter = status;
    document.querySelectorAll('#statusTabs .tab-btn').forEach(b => b.classList.remove('active'));
    btnEl.classList.add('active');
    applyFilters();
}

function quickSort(sortKey) {
    const select = document.getElementById('sortSelect');
    if (select.value === 'avg_desc' && sortKey === 'avg_desc') {
        select.value = 'avg_asc';
    } else {
        select.value = sortKey;
    }
    applyFilters();
}

function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('gradeFilter').value = 'ALL';
    document.getElementById('sortSelect').value = 'avg_desc';
    const allBtn = document.querySelector('#statusTabs .tab-btn[data-status="ALL"]');
    setStatusFilter('ALL', allBtn);
}

function applyFilters() {
    const tbody = document.getElementById('studentsTbody');
    if (!tbody) return;

    const query = document.getElementById('searchInput').value.trim().toLowerCase();
    const gradeFilter = document.getElementById('gradeFilter').value;
    const sortMode = document.getElementById('sortSelect').value;

    const rows = Array.from(tbody.querySelectorAll('tr.student-row'));

    // 정렬 수행
    rows.sort((a, b) => {
        if (sortMode === 'avg_desc') return parseFloat(b.dataset.average) - parseFloat(a.dataset.average);
        if (sortMode === 'avg_asc')  return parseFloat(a.dataset.average) - parseFloat(b.dataset.average);
        if (sortMode === 'kor_desc') return parseInt(b.dataset.korean) - parseInt(a.dataset.korean);
        if (sortMode === 'eng_desc') return parseInt(b.dataset.english) - parseInt(a.dataset.english);
        if (sortMode === 'mat_desc') return parseInt(b.dataset.math) - parseInt(a.dataset.math);
        if (sortMode === 'name_asc') return a.dataset.name.localeCompare(b.dataset.name, 'ko');
        return 0;
    });

    let visibleCount = 0;
    rows.forEach(row => {
        const name = row.dataset.name.toLowerCase();
        const grade = row.dataset.grade;
        const status = row.dataset.status;

        const matchName = !query || name.includes(query);
        const matchGrade = (gradeFilter === 'ALL') || (grade === gradeFilter);
        const matchStatus =
            (currentStatusFilter === 'ALL') ||
            (currentStatusFilter === 'Pass' && status === 'Pass') ||
            (currentStatusFilter === 'Fail' && status.startsWith('Fail'));

        if (matchName && matchGrade && matchStatus) {
            row.style.display = '';
            visibleCount++;
            row.querySelector('.rank-cell').innerText = visibleCount;
        } else {
            row.style.display = 'none';
        }
        tbody.appendChild(row);
    });

    document.getElementById('visibleCountText').innerText =
        `전체 ${rows.length}명 중 ${visibleCount}명 표시 중`;
    const emptyMsg = document.getElementById('emptyFilterMsg');
    if (emptyMsg) {
        emptyMsg.style.display = (visibleCount === 0) ? 'block' : 'none';
    }
}

// 3. Chart.js 차트 초기화 (등급 도넛 + 과목 막대 + 개인 레이더)
function initCharts() {
    if (typeof Chart === 'undefined') return;

    // (1) 등급 분포 도넛 차트
    const doughnutCtx = document.getElementById('gradeDoughnutChart');
    if (doughnutCtx) {
        new Chart(doughnutCtx, {
            type: 'doughnut',
            data: {
                labels: ['A 등급', 'B 등급', 'C 등급', 'D 등급', 'F 등급'],
                datasets: [{
                    data: CHART_DATA.grade_counts,
                    backgroundColor: ['#3b82f6', '#22c55e', '#eab308', '#f97316', '#ef4444'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 12, font: { size: 11 } } }
                }
            }
        });
    }

    // (2) 과목별 평균/최고/최저 막대 차트
    const barCtx = document.getElementById('subjectBarChart');
    if (barCtx) {
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: ['국어', '영어', '수학'],
                datasets: [
                    { label: '평균', data: CHART_DATA.subject_avgs, backgroundColor: '#2563eb', borderRadius: 4 },
                    { label: '최고점', data: CHART_DATA.subject_maxs, backgroundColor: '#10b981', borderRadius: 4 },
                    { label: '최저점', data: CHART_DATA.subject_mins, backgroundColor: '#f43f5e', borderRadius: 4 }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                },
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
                }
            }
        });
    }

    // (3) 개인 vs 반 평균 레이더 차트 (초기값: 1등 학생)
    const radarCtx = document.getElementById('studentRadarChart');
    if (radarCtx) {
        const firstStudent = CHART_DATA.first_student;
        radarChartInstance = new Chart(radarCtx, {
            type: 'radar',
            data: {
                labels: ['국어', '영어', '수학'],
                datasets: [
                    {
                        label: firstStudent ? firstStudent.name : '선택 학생',
                        data: firstStudent ? [firstStudent.kor, firstStudent.eng, firstStudent.mat] : [0, 0, 0],
                        backgroundColor: 'rgba(37, 99, 235, 0.2)',
                        borderColor: '#2563eb',
                        pointBackgroundColor: '#2563eb',
                        borderWidth: 2
                    },
                    {
                        label: '반 평균',
                        data: CHART_DATA.subject_avgs,
                        backgroundColor: 'rgba(100, 116, 139, 0.12)',
                        borderColor: '#64748b',
                        borderDash: [4, 4],
                        pointBackgroundColor: '#64748b',
                        borderWidth: 1.5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { stepSize: 25, display: false }
                    }
                },
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
                }
            }
        });
        if (firstStudent) {
            document.getElementById('radarStudentLabel').innerText = firstStudent.name + ' 학생 선택됨';
        }
    }
}

function selectStudentForRadar(rowEl) {
    document.querySelectorAll('tr.student-row').forEach(r => r.classList.remove('row-selected'));
    rowEl.classList.add('row-selected');

    const name = rowEl.dataset.name;
    const kor = parseInt(rowEl.dataset.korean);
    const eng = parseInt(rowEl.dataset.english);
    const mat = parseInt(rowEl.dataset.math);

    document.getElementById('radarStudentLabel').innerText = name + ' 학생 선택됨';
    if (radarChartInstance) {
        radarChartInstance.data.datasets[0].label = name;
        radarChartInstance.data.datasets[0].data = [kor, eng, mat];
        radarChartInstance.update();
    }
}

window.addEventListener('DOMContentLoaded', initCharts);
</script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. 평균 내림차순으로 전체 학생 조회
    cur.execute("""
        SELECT name, korean, english, math, (korean + english + math) / 3.0 AS avg
        FROM students
        ORDER BY avg DESC
    """)
    rows = cur.fetchall()
    students = [Student(r["name"], r["korean"], r["english"], r["math"]) for r in rows]

    # 2. 통계 계산 (SQL 집계 함수 활용)
    total = len(students)
    subjects_stat = []
    subject_avgs, subject_maxs, subject_mins = [], [], []

    for label, col in [("국어", "korean"), ("영어", "english"), ("수학", "math")]:
        if total > 0:
            cur.execute(f"SELECT AVG({col}), MAX({col}), MIN({col}) FROM students")
            avg_val, max_val, min_val = cur.fetchone()
            subjects_stat.append({
                "label": label,
                "avg": f"{avg_val:.2f}",
                "max": max_val,
                "min": min_val,
            })
            subject_avgs.append(round(avg_val, 2))
            subject_maxs.append(max_val)
            subject_mins.append(min_val)
        else:
            subjects_stat.append({"label": label, "avg": "0.00", "max": 0, "min": 0})
            subject_avgs.append(0)
            subject_maxs.append(0)
            subject_mins.append(0)

    pass_count = sum(1 for s in students if s.status == "Pass")
    fail_count = total - pass_count
    pass_rate = f"{(pass_count / total * 100):.1f}" if total > 0 else "0.0"

    # 등급 분포 집계 (A, B, C, D, F)
    grade_order = ["A", "B", "C", "D", "F"]
    grade_counts = [sum(1 for s in students if s.grade == g) for g in grade_order]

    first_student = None
    if students:
        s0 = students[0]
        first_student = {"name": s0.name, "kor": s0.korean, "eng": s0.english, "mat": s0.math}

    conn.close()

    stats = {
        "total": total,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "pass_rate": pass_rate,
        "subjects": subjects_stat,
    }
    chart_data = {
        "grade_counts": grade_counts,
        "subject_avgs": subject_avgs,
        "subject_maxs": subject_maxs,
        "subject_mins": subject_mins,
        "first_student": first_student,
    }
    return render_template_string(
        HTML_TEMPLATE,
        students=students,
        stats=stats,
        chart_data=chart_data,
        db_file=DB_FILE,
    )


@app.route("/students", methods=["POST"])
def save_student():
    name = request.form.get("name", "").strip()
    try:
        kor = int(request.form.get("korean", ""))
        eng = int(request.form.get("english", ""))
        mat = int(request.form.get("math", ""))
    except ValueError:
        flash("오류: 점수는 정수로 입력해야 합니다.", "error")
        return redirect(url_for("index"))

    if not name:
        flash("오류: 이름을 입력해 주세요.", "error")
        return redirect(url_for("index"))

    if not (0 <= kor <= 100 and 0 <= eng <= 100 and 0 <= mat <= 100):
        flash("오류: 모든 점수는 0에서 100 사이여야 합니다.", "error")
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM students WHERE name = ?", (name,))
    exists = cur.fetchone() is not None

    cur.execute(
        "INSERT OR REPLACE INTO students (name, korean, english, math) VALUES (?, ?, ?, ?)",
        (name, kor, eng, mat),
    )
    conn.commit()
    conn.close()

    action_msg = "수정" if exists else "추가"
    flash(f"'{name}' 학생 성적이 {action_msg}되었습니다.", "info")
    return redirect(url_for("index"))


@app.route("/students/<name>/delete", methods=["POST"])
def delete_student(name):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    flash(f"'{name}' 학생 정보가 삭제되었습니다.", "info")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("🚀 성적 관리 웹 서버 시작: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
