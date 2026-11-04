import random

def get_user_guess(max_num):
    """사용자로부터 1~max_num 사이의 유효한 정수를 입력받는 함수"""
    while True:
        user_input = input(f"1부터 {max_num} 사이의 숫자를 입력하세요: ")
        try:
            guess = int(user_input)
            if 1 <= guess <= max_num:
                return guess
            else:
                print(f"1과 {max_num} 사이의 숫자를 입력해주세요.")
        except ValueError:
            print("올바른 숫자가 아닙니다. 정수를 입력해주세요.")

def play_game():
    """숫자 맞히기 게임 메인 로직 (난이도 선택 및 10회 제한)"""
    print("=== 숫자 맞히기 게임 ===")
    print("난이도를 선택하세요:")
    print("1. 쉬움 (1 ~ 50)")
    print("2. 보통 (1 ~ 100)")
    print("3. 어려움 (1 ~ 500)")
    
    while True:
        choice = input("선택 (1/2/3): ")
        if choice == '1':
            max_num = 50
            break
        elif choice == '2':
            max_num = 100
            break
        elif choice == '3':
            max_num = 500
            break
        else:
            print("1, 2, 3 중에 하나를 입력해주세요.")

    target_number = random.randint(1, max_num)
    max_attempts = 10
    attempts = 0
    
    print(f"\n1부터 {max_num} 사이의 숫자가 정해졌습니다. 기회는 총 {max_attempts}번입니다!\n")
    
    while attempts < max_attempts:
        guess = get_user_guess(max_num)
        attempts += 1
        
        if guess < target_number:
            print(f"더 큰 수입니다! (남은 기회: {max_attempts - attempts}번)\n")
        elif guess > target_number:
            print(f"더 작은 수입니다! (남은 기회: {max_attempts - attempts}번)\n")
        else:
            print(f"정답입니다! 총 {attempts}번 만에 맞히셨습니다.")
            return

    print(f"\n아쉽습니다! 기회를 모두 소모하셨습니다. 정답은 {target_number}였습니다.")

if __name__ == "__main__":
    play_game()

