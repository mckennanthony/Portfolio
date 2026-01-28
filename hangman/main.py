from typing import Set
from words import WORDS
from hangman import choose_word, reveal_progress, process_guess, is_won, draw_stage

MAX_WRONG = 6  # number of wrong guesses allowed (matches last ASCII stage)

def get_letter(prompt: str) -> str:
    """Ask user for a single A–Z letter, lowercased."""
    while True:
        raw = input(prompt).strip().lower()
        if len(raw) != 1 or not raw.isalpha():
            print("Please enter a single letter (A–Z).")
            continue
        return raw

def play_one_round() -> None:
    secret = choose_word(WORDS)
    guessed: Set[str] = set()
    wrong = 0

    print("\n=== Hangman ===")
    print("Guess the word, one letter at a time.")
    print(f"(You can miss up to {MAX_WRONG} times.)")

    while True:
        print(draw_stage(wrong))
        print("Word:  ", reveal_progress(secret, guessed))
        print("Used:  ", " ".join(sorted(guessed)) or "—")
        print(f"Wrong: {wrong}/{MAX_WRONG}")

        guess = get_letter("Your guess: ")

        correct, msg = process_guess(secret, guess, guessed)
        print(msg)

        if not correct:
            wrong += 1

        # Check end conditions
        if is_won(secret, guessed):
            print("\n🎉 You win! The word was:", secret)
            print(draw_stage(wrong))
            break

        if wrong > MAX_WRONG:
            # Safety guard (shouldn’t trigger if MAX_WRONG matches stages)
            print("\nOut of guesses! The word was:", secret)
            break

        if wrong == MAX_WRONG:
            print(draw_stage(wrong))
            print("\n💀 Game over! The word was:", secret)
            break

def main():
    while True:
        play_one_round()
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing! Bye 👋")
            return

if __name__ == "__main__":
    main()
