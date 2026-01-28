import random
from typing import Set, Tuple, List

HANGMAN_PICS = [
    """
     +---+
     |   |
         |
         |
         |
         |
    =========
    """,
    """
     +---+
     |   |
     O   |
         |
         |
         |
    =========
    """,
    """
     +---+
     |   |
     O   |
     |   |
         |
         |
    =========
    """,
    """
     +---+
     |   |
     O   |
    /|   |
         |
         |
    =========
    """,
    """
     +---+
     |   |
     O   |
    /|\\  |
         |
         |
    =========
    """,
    """
     +---+
     |   |
     O   |
    /|\\  |
    /    |
         |
    =========
    """,
    """
     +---+
     |   |
     O   |
    /|\\  |
    / \\  |
         |
    =========
    """,
]

def choose_word(words: List[str]) -> str:
    """Pick a random word from the list."""
    return random.choice(words).lower()

def reveal_progress(secret: str, guessed: Set[str]) -> str:
    """Return the masked word like 'p _ t h o n' based on guessed letters."""
    return " ".join([c if c in guessed else "_" for c in secret])

def process_guess(secret: str, guess: str, guessed: Set[str]) -> Tuple[bool, str]:
    """
    Apply a single-letter guess.
    Returns (is_correct, message).
    """
    if guess in guessed:
        return False, f"You already guessed '{guess}'."
    guessed.add(guess)
    if guess in secret:
        return True, f"Nice! '{guess}' is in the word."
    return False, f"Oops! '{guess}' is not in the word."

def is_won(secret: str, guessed: Set[str]) -> bool:
    """All letters revealed?"""
    return all(c in guessed for c in secret)

def draw_stage(wrong_guesses: int) -> str:
    """ASCII art based on wrong guess count."""
    wrong_guesses = max(0, min(wrong_guesses, len(HANGMAN_PICS) - 1))
    return HANGMAN_PICS[wrong_guesses]
