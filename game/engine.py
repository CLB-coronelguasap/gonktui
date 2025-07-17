import requests
import random
import time


class GameEngine:
    """
    Handles game logic, state, and question management for the trivia game.
    """

    def __init__(self, categories=None):
        # Initialize game state
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.lives = 5
        self.categories = categories or []
        self.token = self.get_token()

    def get_token(self):
        """
        Requests a session token from the Open Trivia DB API.
        Ensures unique questions for each session.
        """
        print("[*] Requesting session token...")
        resp = requests.get("https://opentdb.com/api_token.php?command=request")
        data = resp.json()
        token = data.get("token")
        print(f"[*] Received token: {token}")
        return token

    def start_game(self):
        """
        Resets game state and loads questions.
        """
        self.lives = 5
        self.score = 0
        self.current_index = 0
        self.fetch_questions()

    def fetch_questions(self, amount=10):
        """
        Fetches questions from Open Trivia DB for each selected category.
        Respects API rate limits (5 seconds between requests).
        Shuffles all questions before starting the game.
        """
        all_questions = []
        if self.categories:
            for cat in self.categories:
                url = f"https://opentdb.com/api.php?amount={amount}&type=multiple&category={cat}&token={self.token}"
                response = requests.get(url)
                data = response.json()
                questions = data.get("results", [])
                all_questions.extend(questions)
                time.sleep(5)  # Respect API rate limit
        else:
            url = f"https://opentdb.com/api.php?amount={amount}&type=multiple&token={self.token}"
            response = requests.get(url)
            data = response.json()
            all_questions = data.get("results", [])
        random.shuffle(all_questions)
        self.questions = all_questions
        self.current_index = 0

    def update(self):
        """
        Ensures questions are loaded and fetches more if needed.
        """
        # Only fetch if there are no questions and lives remain
        if not self.questions and self.lives > 0:
            self.fetch_questions()
        # If out of questions but still have lives, fetch more
        elif self.current_index >= len(self.questions) and self.lives > 0:
            self.questions = []
            self.fetch_questions()
            self.current_index = 0

    def get_game_state(self):
        """
        Returns the current game state for rendering in the UI.
        """
        if self.lives <= 0:
            return {"finished": True, "score": self.score, "lives": self.lives}
        if not self.questions:
            return {"loading": True, "score": self.score, "lives": self.lives}
        if self.current_index < len(self.questions):
            q = self.questions[self.current_index]
            return {
                "question": q["question"],
                "choices": q["incorrect_answers"] + [q["correct_answer"]],
                "score": self.score,
                "index": self.current_index + 1,
                "total": len(self.questions),
                "lives": self.lives,
                "correct_answer": q["correct_answer"],
            }
        else:
            # Out of questions, but update() will fetch more
            return {"loading": True, "score": self.score, "lives": self.lives}

    def handle_input(self, user_input, correct_answer):
        """
        Processes user input, updates score and lives, and advances to the next question.
        """
        if self.lives <= 0 or self.current_index >= len(self.questions):
            return
        if user_input is None:
            self.lives -= 1
        else:
            if user_input.strip().lower() == correct_answer.strip().lower():
                self.score += 1
            else:
                self.lives -= 1
        self.current_index += 1
