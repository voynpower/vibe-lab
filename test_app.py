# =====================================================================
# 성적 관리 프로그램 & JSON REST API 자동화 단위 테스트 (pytest)
# 실행 방법: python3 -m pytest -v
# =====================================================================

import pytest
from grades import Student, GradeManager
from app import app


# ---------------------------------------------------------------------
# 1. Student 도메인 모델 단위 테스트 (등급 A~F 및 과락/통과 판정)
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "kor, eng, mat, expected_grade, expected_status",
    [
        (95, 90, 92, "A", "Pass"),            # 평균 92.33 -> A, Pass
        (85, 80, 88, "B", "Pass"),            # 평균 84.33 -> B, Pass
        (70, 75, 72, "C", "Pass"),            # 평균 72.33 -> C, Pass
        (60, 65, 62, "D", "Pass"),            # 평균 62.33 -> D, Pass
        (55, 58, 50, "F", "Fail(평균미달)"),   # 전 과목 40 이상이지만 평균 54.33 -> F, 평균미달
        (95, 95, 35, "C", "Fail(과락)"),       # 평균 75.00(C)이지만 수학 35점(<40) -> 과락
        (39, 100, 100, "C", "Fail(과락)"),     # 국어 39점(<40) -> 과락
    ],
)
def test_student_grade_and_status(kor, eng, mat, expected_grade, expected_status):
    s = Student("테스트학생", kor, eng, mat)
    assert s.grade == expected_grade
    assert s.status == expected_status


def test_student_to_dict():
    s = Student("  김하늘  ", 90, 80, 70)
    d = s.to_dict()
    assert d["이름"] == "김하늘"
    assert d["평균"] == "80.00"
    assert d["등급"] == "B"
    assert d["판정"] == "Pass"


# ---------------------------------------------------------------------
# 2. GradeManager SQLite DB 연동 테스트
# ---------------------------------------------------------------------

def test_grade_manager_sqlite_crud(tmp_path):
    db_file = str(tmp_path / "test_students.db")
    mgr = GradeManager(db_file=db_file)
    try:
        # 수동 데이터 추가 및 저장 검증
        mgr.students = [
            Student("홍길동", 90, 95, 100),
            Student("이순신", 35, 80, 85),
        ]
        mgr.save_data()

        reloaded = mgr.load_data()
        assert len(reloaded) == 2
        names = {s.name for s in reloaded}
        assert names == {"홍길동", "이순신"}
    finally:
        mgr.close()


# ---------------------------------------------------------------------
# 3. Flask JSON REST API & 웹 엔드포인트 통합 테스트
# ---------------------------------------------------------------------

@pytest.fixture
def client(tmp_path):
    """격리된 임시 SQLite DB를 사용하는 Flask 테스트 클라이언트"""
    test_db = str(tmp_path / "api_test.db")
    mgr = GradeManager(db_file=test_db)
    mgr.cursor.execute("DELETE FROM students")
    mgr.conn.commit()
    mgr.close()

    app.config["TESTING"] = True
    app.config["DB_FILE"] = test_db
    with app.test_client() as c:
        yield c


def test_api_crud_lifecycle(client):
    # 1) 초기 빈 목록 확인
    res = client.get("/api/students")
    assert res.status_code == 200
    assert res.get_json()["count"] == 0

    # 2) POST /api/students - 학생 2명 등록
    res1 = client.post(
        "/api/students",
        json={"name": "김하늘", "korean": 92, "english": 88, "math": 90},
    )
    assert res1.status_code == 201
    data1 = res1.get_json()
    assert data1["name"] == "김하늘"
    assert data1["grade"] == "A"
    assert data1["status"] == "Pass"

    res2 = client.post(
        "/api/students",
        json={"name": "후산보이", "korean": 30, "english": 85, "math": 95},
    )
    assert res2.status_code == 201
    data2 = res2.get_json()
    assert data2["grade"] == "C"
    assert data2["status"] == "Fail(과락)"

    # 3) GET /api/students - 전체 조회 및 필터 테스트
    all_res = client.get("/api/students")
    assert all_res.get_json()["count"] == 2

    pass_res = client.get("/api/students?status=Pass")
    assert pass_res.get_json()["count"] == 1
    assert pass_res.get_json()["students"][0]["name"] == "김하늘"

    fail_res = client.get("/api/students?status=Fail")
    assert fail_res.get_json()["count"] == 1
    assert fail_res.get_json()["students"][0]["name"] == "후산보이"

    # 4) PUT /api/students/<name> - 후산보이 국어 점수 30 -> 85로 수정 (Pass로 전환)
    put_res = client.put(
        "/api/students/후산보이",
        json={"korean": 85, "english": 85, "math": 95},
    )
    assert put_res.status_code == 200
    updated = put_res.get_json()
    assert updated["grade"] == "B"
    assert updated["status"] == "Pass"

    # 5) GET /api/statistics - 통계 검증
    stat_res = client.get("/api/statistics")
    assert stat_res.status_code == 200
    stats = stat_res.get_json()
    assert stats["total"] == 2
    assert stats["pass_count"] == 2
    assert stats["pass_rate"] == 100.0
    assert stats["grade_distribution"]["A"] == 1
    assert stats["grade_distribution"]["B"] == 1

    # 6) DELETE /api/students/<name> - 삭제 검증
    del_res = client.delete("/api/students/후산보이")
    assert del_res.status_code == 200

    get_deleted = client.get("/api/students/후산보이")
    assert get_deleted.status_code == 404


def test_api_validation_errors(client):
    # 점수 범위 초과 (150점)
    bad_score = client.post(
        "/api/students",
        json={"name": "오류학생", "korean": 150, "english": 80, "math": 80},
    )
    assert bad_score.status_code == 400

    # 이름 누락
    no_name = client.post(
        "/api/students",
        json={"name": "   ", "korean": 80, "english": 80, "math": 80},
    )
    assert no_name.status_code == 400

    # 존재하지 않는 학생 수정/삭제 시 404
    assert client.put("/api/students/없는학생", json={"korean": 80, "english": 80, "math": 80}).status_code == 404
    assert client.delete("/api/students/없는학생").status_code == 404


def test_web_dashboard_page_renders(client):
    client.post("/students", data={"name": "박구름", "korean": "80", "english": "85", "math": "90"})
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "박구름" in html
    assert "gradeDoughnutChart" in html
