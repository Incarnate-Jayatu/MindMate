ALPHA = 0.3  # weight of the latest attempt
VERIFY_MIN = 3  # distinct questions answered correctly before "mastered"

def status(score: float, attempts: int, distinct_correct: int = 0) -> str:
    if attempts == 0:
        return "unseen"
    if score >= 0.75 and distinct_correct >= VERIFY_MIN:
        return "mastered"
    if score < 0.4:
        return "weak"
    return "learning"

def update(m, correct: bool, distinct_correct: int = 0) -> None:
    m.score = round((1 - ALPHA) * m.score + ALPHA * (1.0 if correct else 0.0), 4)
    m.attempts += 1
    m.status = status(m.score, m.attempts, distinct_correct)
