# =====================================================================
# 성적 관리 프로그램 (SQLite 데이터베이스 버전)
# =====================================================================

import os
import sqlite3
import csv

DB_FILE = "students.db"
CSV_FILE = "students.csv"


class Student:
    """개별 학생의 정보와 성적을 관리하는 클래스"""
    def __init__(self, name, korean, english, math):
        self.name = name.strip()
        self.korean = int(korean)
        self.english = int(english)
        self.math = int(math)

    @property
    def average(self):
        """평균 점수 계산"""
        return (self.korean + self.english + self.math) / 3

    @property
    def grade(self):
        """평균 점수 기반 등급(A~F) 계산"""
        avg = self.average
        if avg >= 90:
            return "A"
        elif avg >= 80:
            return "B"
        elif avg >= 70:
            return "C"
        elif avg >= 60:
            return "D"
        else:
            return "F"

    @property
    def status(self):
        """과락(40점 미만 과목 존재) 또는 평균 60점 미만 여부 판정"""
        if self.korean < 40 or self.english < 40 or self.math < 40:
            return "Fail(과락)"
        if self.average < 60:
            return "Fail(평균미달)"
        return "Pass"

    def to_dict(self):
        return {
            "이름": self.name,
            "국어": self.korean,
            "영어": self.english,
            "수학": self.math,
            "평균": f"{self.average:.2f}",
            "등급": self.grade,
            "판정": self.status
        }


class GradeManager:
    """SQLite DB 기반 성적 관리 매니저 클래스"""
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self.init_db()
        self.students = self.load_data()

    def init_db(self):
        """students 테이블 생성"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                name TEXT PRIMARY KEY,
                korean INTEGER NOT NULL,
                english INTEGER NOT NULL,
                math INTEGER NOT NULL
            )
        """)
        self.conn.commit()

    def migrate_from_csv(self):
        """기존 CSV 데이터를 DB로 마이그레이션"""
        self.cursor.execute("SELECT COUNT(*) FROM students")
        if self.cursor.fetchone()[0] == 0 and os.path.exists(CSV_FILE):
            try:
                with open(CSV_FILE, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = row.get("이름") or row.get("name")
                        kor = row.get("국어") or row.get("korean")
                        eng = row.get("영어") or row.get("english")
                        mat = row.get("수학") or row.get("math")
                        if name and kor is not None and eng is not None and mat is not None:
                            self.cursor.execute(
                                "INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?)",
                                (name.strip(), int(kor), int(eng), int(mat))
                            )
                self.conn.commit()
                print("CSV 데이터를 SQLite DB로 마이그레이션 완료!")
            except Exception as e:
                print(f"마이그레이션 오류: {e}")

    def load_data(self):
        """DB에서 학생 목록 로드"""
        self.migrate_from_csv()
        students = []
        self.cursor.execute("SELECT name, korean, english, math FROM students")
        for row in self.cursor.fetchall():
            students.append(Student(*row))
        return students

    def save_data(self):
        """메모리 데이터를 DB에 동기화"""
        try:
            self.cursor.execute("DELETE FROM students")
            for s in self.students:
                self.cursor.execute(
                    "INSERT INTO students VALUES (?, ?, ?, ?)",
                    (s.name, s.korean, s.english, s.math)
                )
            self.conn.commit()
            print("데이터베이스에 저장되었습니다.")
        except Exception as e:
            print(f"저장 오류: {e}")

    def get_valid_score(self, subject):
        """유효한 점수(0~100) 입력받기"""
        while True:
            val = input(f"{subject} 점수 입력 (0~100): ").strip()
            try:
                score = int(val)
                if 0 <= score <= 100:
                    return score
                print("오류: 0~100 사이의 정수를 입력하세요.")
            except ValueError:
                print("오류: 올바른 정수 형식이 아닙니다.")
    def add_student(self):
        """학생 추가"""
        print("\n--- 학생 추가 ---")
        name = input("이름 입력: ").strip()
        if not name:
            print("오류: 이름은 비워둘 수 없습니다.")
            return

        kor = self.get_valid_score("국어")
        eng = self.get_valid_score("영어")
        mat = self.get_valid_score("수학")

        self.students = [s for s in self.students if s.name != name]
        self.students.append(Student(name, kor, eng, mat))

        self.cursor.execute(
            "INSERT OR REPLACE INTO students VALUES (?, ?, ?, ?)",
            (name, kor, eng, mat)
        )
        self.conn.commit()
        print(f"'{name}' 학생 추가 완료.")

    def modify_student(self):
        """학생 수정"""
        print("\n--- 학생 정보 수정 ---")
        if not self.students:
            print("등록된 학생이 없습니다.")
            return

        name = input("수정할 학생 이름 입력: ").strip()
        target = [s for s in self.students if s.name == name]
        if not target:
            print(f"오류: '{name}' 학생을 찾을 수 없습니다.")
            return

        s = target[0]
        print(f"현재 -> 국어:{s.korean}, 영어:{s.english}, 수학:{s.math}")
        kor = self.get_valid_score("국어")
        eng = self.get_valid_score("영어")
        mat = self.get_valid_score("수학")

        s.korean, s.english, s.math = kor, eng, mat
        self.cursor.execute(
            "UPDATE students SET korean=?, english=?, math=? WHERE name=?",
            (kor, eng, mat, name)
        )
        self.conn.commit()
        print(f"'{name}' 학생 수정 완료.")

    def delete_student(self):
        """학생 삭제"""
        print("\n--- 학생 정보 삭제 ---")
        if not self.students:
            print("등록된 학생이 없습니다.")
            return

        name = input("삭제할 학생 이름 입력: ").strip()
        target = [s for s in self.students if s.name == name]
        if not target:
            print(f"오류: '{name}' 학생을 찾을 수 없습니다.")
            return

        if input(f"'{name}' 학생을 삭제하시겠습니까? (y/n): ").strip().lower() == 'y':
            self.students.remove(target[0])
            self.cursor.execute("DELETE FROM students WHERE name=?", (name,))
            self.conn.commit()
            print("삭제 완료.")
        else:
            print("취소되었습니다.")

    def print_students(self):
        """전체 목록 출력 (SQL ORDER BY 평균 내림차순 + 등급/판정 표시)"""
        print("\n--- 전체 학생 목록 ---")
        self.cursor.execute("""
            SELECT name, korean, english, math, (korean + english + math) / 3.0 AS avg
            FROM students
            ORDER BY avg DESC
        """)
        rows = self.cursor.fetchall()
        if not rows:
            print("등록된 학생이 없습니다.")
            return

        print(f"{'이름':<10} | {'국어':<6} | {'영어':<6} | {'수학':<6} | {'평균':<6} | {'등급':<4} | {'판정'}")
        print("-" * 68)
        for name, kor, eng, mat, avg in rows:
            student = Student(name, kor, eng, mat)
            print(f"{student.name:<10} | {student.korean:<6} | {student.english:<6} | {student.math:<6} | {avg:<6.2f} | {student.grade:<4} | {student.status}")

    def print_statistics(self):
        """과목별 통계 및 합격/과락 현황 출력 (SQL 집계 함수 활용)"""
        print("\n--- 과목별 통계 ---")
        self.cursor.execute("SELECT COUNT(*) FROM students")
        total_count = self.cursor.fetchone()[0]
        if total_count == 0:
            print("등록된 학생이 없습니다.")
            return

        subjects = [("국어", "korean"), ("영어", "english"), ("수학", "math")]
        print(f"{'과목':<6} | {'평균':<6} | {'최고점':<6} | {'최저점':<6}")
        print("-" * 34)
        for label, col in subjects:
            self.cursor.execute(f"SELECT AVG({col}), MAX({col}), MIN({col}) FROM students")
            avg_val, max_val, min_val = self.cursor.fetchone()
            print(f"{label:<6} | {avg_val:<6.2f} | {max_val:<6} | {min_val:<6}")

        self.cursor.execute("""
            SELECT COUNT(*) FROM students
            WHERE korean >= 40 AND english >= 40 AND math >= 40
              AND (korean + english + math) / 3.0 >= 60
        """)
        pass_count = self.cursor.fetchone()[0]
        fail_count = total_count - pass_count
        pass_rate = (pass_count / total_count) * 100
        print("-" * 34)
        print(f"전체: {total_count}명 | 통과(Pass): {pass_count}명 | 불합격(Fail): {fail_count}명 (합격률: {pass_rate:.1f}%)")

    def close(self):
        if self.conn:
            self.conn.close()

    def run(self):
        try:
            while True:
                print("\n=== 성적 관리 프로그램 (SQLite DB) ===")
                print("1) 전체 목록")
                print("2) 학생 추가")
                print("3) 학생 수정")
                print("4) 학생 삭제")
                print("5) 과목별 통계")
                print("6) 저장 후 종료")
                
                choice = input("선택 (1-6): ").strip()
                if choice == "1":
                    self.print_students()
                elif choice == "2":
                    self.add_student()
                elif choice == "3":
                    self.modify_student()
                elif choice == "4":
                    self.delete_student()
                elif choice == "5":
                    self.print_statistics()
                elif choice == "6":
                    self.save_data()
                    print("종료합니다.")
                    break
                else:
                    print("오류: 1~6 사이의 숫자를 입력하세요.")
        finally:
            self.close()


if __name__ == "__main__":
    manager = GradeManager()
    manager.run()

