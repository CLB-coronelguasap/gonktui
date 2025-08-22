import requests
import random
import time


class GameEngine:
    """
    Simple game logic and question management for the trivia game.
    """

    def __init__(self, categories=None):
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.lives = 5
        self.categories = categories or []
        self.token = self.get_token()

    def get_token(self):
        """Get a session token from the Open Trivia DB API."""
        resp = requests.get("https://opentdb.com/api_token.php?command=request")
        data = resp.json()
        return data.get("token")

    def fetch_questions(self, amount=10):
        """
        Fetch questions from Open Trivia DB for each selected category.
        Wait 5 seconds between requests to avoid rate limits.
        """
        all_questions = []
        if self.categories:
            for cat in self.categories:
                url = f"https://opentdb.com/api.php?amount={amount}&type=multiple&category={cat}&token={self.token}"
                response = requests.get(url)
                data = response.json()
                questions = data.get("results", [])
                all_questions.extend(questions)
                time.sleep(5)
        else:
            url = f"https://opentdb.com/api.php?amount={amount}&type=multiple&token={self.token}"
            response = requests.get(url)
            data = response.json()
            all_questions = data.get("results", [])
        random.shuffle(all_questions)
        self.questions = all_questions
        self.current_index = 0

    def get_game_state(self):
        """
        Return the current game state for the UI.
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
            return {"loading": True, "score": self.score, "lives": self.lives}

    def handle_input(self, user_input, correct_answer):
        """
        Update score and lives based on user input, then go to next question.
        """
        if self.lives <= 0 or self.current_index >= len(self.questions):
            return
        if user_input is None:
            self.lives -= 1
        elif user_input.strip().lower() == correct_answer.strip().lower():
            self.score += 1
        else:
            self.lives -= 1
        self.current_index += 1
