"""Template-based question variants. No AI or API key needed: answers are computed, never guessed."""
import random
from .models import Question

def _prog(defs: str, body: str) -> str:
    return f"#include <iostream>\nusing namespace std;\n{defs}\nint main() {{ {body} }}\n"

def _build(rng, concept, diff, prompt, correct, wrongs, extras):
    correct = str(correct)
    seen, opts = {correct}, [(correct, None)]
    for t, m in list(wrongs) + [(e, None) for e in extras]:
        t = str(t)
        if t in seen:
            continue
        seen.add(t)
        opts.append((t, m))
        if len(opts) == 4:
            break
    rng.shuffle(opts)
    options = [{"key": "ABCD"[i], "text": t, "misconception_id": m} for i, (t, m) in enumerate(opts)]
    ans = next(o["key"] for o in options if o["text"] == correct)
    return dict(concept_id=concept, difficulty=diff, prompt=prompt, options=options, answer_key=ans)

def _arr(a):
    return "{" + ", ".join(map(str, a)) + "}"

# Each template returns (prompt, correct, [(wrong, misconception_id)], [extra wrongs], cpp_program)

def arrays_index(r):
    a, i = r.sample(range(10, 100), 5), r.randint(1, 3)
    return (f"int a[] = {_arr(a)};  cout << a[{i}];  Prints?", a[i],
            [(a[i - 1], "arr-off-by-one"), (a[i + 1], "arr-off-by-one")], [a[0], a[4]],
            _prog("", f"int a[] = {_arr(a)}; cout << a[{i}];"))

def arrays_every_other(r):
    a = r.sample(range(1, 30), 5)
    c = a[0] + a[2] + a[4]
    return (f"int a[] = {_arr(a)};  int s = 0;  for (int i = 0; i < 5; i += 2) s += a[i];  cout << s;  Prints?", c,
            [(a[1] + a[3], "arr-off-by-one"), (sum(a), None), (a[0] + a[2], "loop-boundary")], [c + 2, c + 5, c + 9],
            _prog("", f"int a[] = {_arr(a)}; int s = 0; for (int i = 0; i < 5; i += 2) s += a[i]; cout << s;"))

def arrays_pass(r):
    x = r.sample(range(2, 20), 3)
    c = 2 * x[1]
    fn = "void f(int a[], int n) { for (int i = 0; i < n; i++) a[i] *= 2; }"
    return (f"{fn}  int x[3] = {_arr(x)};  f(x, 3);  cout << x[1];  Prints?", c,
            [(x[1], "arr-pass-by-value"), (2 * x[0], "arr-off-by-one"), (2 * x[2], "arr-off-by-one")], [c + 1, c + 4, c + 9],
            _prog(fn, f"int x[3] = {_arr(x)}; f(x, 3); cout << x[1];"))

def loops_count(r):
    a = r.randint(0, 2)
    b = a + r.randint(3, 8)
    n = b - a
    return (f"int count = 0;  for (int i = {a}; i < {b}; i++) count++;  cout << count;  Prints?", n,
            [(n + 1, "loop-boundary"), (n - 1, "loop-boundary")], [b, n + 2, n + 3],
            _prog("", f"int count = 0; for (int i = {a}; i < {b}; i++) count++; cout << count;"))

def loops_sum(r):
    n = r.randint(3, 6)
    c = n * (n + 1) // 2
    return (f"int s = 0;  for (int i = 1; i <= {n}; i++) s += i;  cout << s;  Prints?", c,
            [((n - 1) * n // 2, "loop-boundary"), ((n + 1) * (n + 2) // 2, "loop-boundary"), (n * n, None)], [c + 2, c + 7],
            _prog("", f"int s = 0; for (int i = 1; i <= {n}; i++) s += i; cout << s;"))

def loops_nested(r):
    R, C = r.randint(2, 4), r.randint(2, 5)
    c = R * C
    return (f"int c = 0;  for (int i = 0; i < {R}; i++) for (int j = 0; j < {C}; j++) c++;  cout << c;  Prints?", c,
            [(R + C, "loop-nested-add"), (R * (C - 1), "loop-boundary"), ((R + 1) * C, "loop-boundary")], [c + 2, c + 5, c + 7],
            _prog("", f"int c = 0; for (int i = 0; i < {R}; i++) for (int j = 0; j < {C}; j++) c++; cout << c;"))

def rec_factorial(r):
    n = r.randint(3, 5)
    f = 1
    for k in range(2, n + 1):
        f *= k
    fn = "int f(int n) { if (n <= 1) return 1; return n * f(n - 1); }"
    return (f"{fn}  f({n}) = ?", f,
            [(n, "rec-last-call-only"), (1, "rec-base-is-result"), (n * (n - 1), None)], [f + 2, f + 9, f + 20],
            _prog(fn, f"cout << f({n});"))

def rec_sum(r):
    n = r.randint(3, 6)
    c = n * (n + 1) // 2
    fn = "int f(int n) { if (n == 0) return 0; return n + f(n - 1); }"
    return (f"{fn}  f({n}) = ?", c,
            [(n, "rec-last-call-only"), (0, "rec-base-is-result"), (n * (n - 1) // 2, None)], [c + 1, c + 3, c + 8],
            _prog(fn, f"cout << f({n});"))

def rec_power(r):
    k, n = r.randint(2, 3), r.randint(2, 4)
    c = k ** n
    fn = f"int f(int n) {{ if (n == 0) return 1; return {k} * f(n - 1); }}"
    return (f"{fn}  f({n}) = ?", c,
            [(k * n, "rec-last-call-only"), (1, "rec-base-is-result"), (k ** (n + 1), None)], [c + 1, c + 3, c + 7],
            _prog(fn, f"cout << f({n});"))

TEMPLATES = {
    ("arrays", 1): arrays_index, ("arrays", 2): arrays_every_other, ("arrays", 3): arrays_pass,
    ("loops", 1): loops_count, ("loops", 2): loops_sum, ("loops", 3): loops_nested,
    ("recursion", 1): rec_factorial, ("recursion", 2): rec_sum, ("recursion", 3): rec_power,
}

def make(concept_id, difficulty, rng):
    """Returns (question dict, C++ program, correct answer text) or None."""
    fn = TEMPLATES.get((concept_id, difficulty))
    if fn is None:
        return None
    prompt, correct, wrongs, extras, cpp = fn(rng)
    return _build(rng, concept_id, difficulty, prompt, correct, wrongs, extras), cpp, str(correct)

def generate(db, concept_id, difficulty, tries=30):
    """Creates and saves a brand-new question (never a duplicate prompt). Returns the Question or None."""
    rng = random.Random()
    for _ in range(tries):
        made = make(concept_id, difficulty, rng)
        if not made:
            return None
        v = made[0]
        if not db.query(Question).filter_by(prompt=v["prompt"]).first():
            q = Question(**v)
            db.add(q)
            db.commit()
            db.refresh(q)
            return q
    return None
