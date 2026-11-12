import grades

def main():
    manager = grades.GradeManager()
    print("Database verification passed! Loaded students count:", len(manager.students))
    for s in manager.students:
        print(f" - {s.name}: 국어={s.korean}, 영어={s.english}, 수학={s.math}, 평균={s.average:.2f}")
    manager.close()

if __name__ == "__main__":
    main()
