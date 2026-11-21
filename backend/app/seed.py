import random
from .models import Concept, Misconception, Question

CONCEPTS = [
    ("arrays", "Arrays", []),
    ("loops", "Loops", []),
    ("recursion", "Recursion", ["loops"]),
]

MISCONCEPTIONS = [
    ("arr-off-by-one", "arrays", "Believes valid indices run 1..n instead of 0..n-1"),
    ("arr-partial-init", "arrays", "Thinks uninitialized elements of a partially initialized array hold garbage"),
    ("arr-decay", "arrays", "Thinks an array parameter keeps its size inside the function"),
    ("loop-boundary", "loops", "Miscounts iterations when the condition uses < vs <="),
    ("loop-missing-update", "loops", "Forgets that the loop variable must change for the loop to end"),
    ("loop-stray-semicolon", "loops", "Does not realize a trailing ; makes the loop body empty"),
    ("rec-no-base", "recursion", "Overlooks the need for a base case"),
    ("rec-last-call-only", "recursion", "Thinks only the last recursive call contributes to the result"),
    ("rec-order", "recursion", "Confuses work done before vs after the recursive call"),
]

def _q(c, d, prompt, opts, ans, shuffle=False):
    if shuffle:  # deterministic shuffle so the right answer isn't always the same letter
        correct = next(t for k, t, m in opts if k == ans)
        body = [(t, m) for _, t, m in opts]
        random.Random(prompt).shuffle(body)
        opts = [("ABCD"[i], t, m) for i, (t, m) in enumerate(body)]
        ans = next(k for k, t, m in opts if t == correct)
    return dict(concept_id=c, difficulty=d, prompt=prompt, answer_key=ans,
                options=[{"key": k, "text": t, "misconception_id": m} for k, t, m in opts])

QUESTIONS = [
    _q("arrays", 1, "int a[5]; a[5] = 1;  What happens?",
       [("A", "Sets the last element", "arr-off-by-one"), ("B", "Undefined behavior (out of bounds)", None),
        ("C", "Guaranteed compile error", None), ("D", "Resizes the array", None)], "B"),
    _q("arrays", 2, "int a[5] = {1, 2};  cout << a[4];  Prints?",
       [("A", "Garbage value", "arr-partial-init"), ("B", "0", None), ("C", "2", None), ("D", "Runtime error", None)], "B"),
    _q("arrays", 3, "void f(int arr[]) { cout << sizeof(arr); }  What does it print for int a[5]?",
       [("A", "20 on any platform", "arr-decay"), ("B", "5", "arr-decay"), ("C", "The size of a pointer", None), ("D", "0", None)], "C"),
    _q("loops", 1, "for (int i = 0; i < 5; i++) { ... }  How many iterations?",
       [("A", "4", None), ("B", "5", None), ("C", "6", "loop-boundary"), ("D", "Infinite", None)], "B"),
    _q("loops", 2, "int i = 0; while (i < 3) { cout << i; }  What happens?",
       [("A", "Prints 012", "loop-missing-update"), ("B", "Prints 0 once", "loop-missing-update"),
        ("C", "Infinite loop printing 0", None), ("D", "Prints nothing", None)], "C"),
    _q("loops", 3, 'for (int i = 0; i < 3; i++);  cout << "x";  Prints?',
       [("A", "xxx", "loop-stray-semicolon"), ("B", "x", None), ("C", "Nothing", None), ("D", "Compile error", None)], "B"),
    _q("recursion", 1, "int f(int n) { return n * f(n - 1); }  What does f(3) do?",
       [("A", "Returns 6", "rec-no-base"), ("B", "Returns 0", "rec-no-base"),
        ("C", "Never terminates (stack overflow)", None), ("D", "Returns 3", None)], "C"),
    _q("recursion", 2, "int f(int n) { if (n == 0) return 0; return n + f(n - 1); }  f(3) = ?",
       [("A", "3", "rec-last-call-only"), ("B", "6", None), ("C", "0", "rec-last-call-only"), ("D", "9", None)], "B"),
    _q("recursion", 3, "void p(int n) { if (n == 0) return; p(n - 1); cout << n; }  p(3) prints?",
       [("A", "321", "rec-order"), ("B", "123", None), ("C", "3", "rec-order"), ("D", "012", "rec-order")], "B"),
]

_n = lambda *a: _q(*a, shuffle=True)

MISCONCEPTIONS += [
    ("arr-pass-by-value", "arrays", "Thinks arrays are copied when passed to a function"),
    ("loop-update-order", "loops", "Mixes up when the loop variable changes relative to the statements using it"),
    ("loop-nested-add", "loops", "Adds the counts of nested loops instead of multiplying them"),
    ("loop-continue-break", "loops", "Confuses continue (skip this round) with break (leave the loop)"),
    ("rec-base-is-result", "recursion", "Thinks the base-case value is the final answer of the whole call"),
]

QUESTIONS += [
    _n("arrays", 1, "int a[4] = {10, 20, 30, 40};  cout << a[1];  Prints?",
       [("A", "10", "arr-off-by-one"), ("B", "20", None), ("C", "30", None), ("D", "40", None)], "B"),
    _n("arrays", 1, "int a[3];  How many elements, and what is the last valid index?",
       [("A", "3 elements, last index 3", "arr-off-by-one"), ("B", "3 elements, last index 2", None),
        ("C", "2 elements, last index 2", None), ("D", "4 elements, last index 3", None)], "B"),
    _n("arrays", 2, "int a[5] = {0};  a[2] = 7;  cout << a[0] + a[2];  Prints?",
       [("A", "0", None), ("B", "7", None), ("C", "Garbage value", "arr-partial-init"), ("D", "9", None)], "B"),
    _n("arrays", 2, "int a[] = {5, 6, 7};  cout << sizeof(a) / sizeof(a[0]);  Prints?",
       [("A", "3", None), ("B", "12", None), ("C", "1", None), ("D", "Compile error", None)], "A"),
    _n("arrays", 3, "void f(int a[]) { a[0] = 99; }  int x[2] = {1, 2};  f(x);  cout << x[0];  Prints?",
       [("A", "1 (the array was copied)", "arr-pass-by-value"), ("B", "99", None),
        ("C", "Compile error", None), ("D", "2", None)], "B"),
    _n("arrays", 3, "int a[3] = {1, 2, 3};  int *p = a;  cout << *(p + 2);  Prints?",
       [("A", "2", "arr-off-by-one"), ("B", "3", None), ("C", "An address", None), ("D", "Undefined behavior", None)], "B"),

    _n("loops", 1, "for (int i = 1; i <= 3; i++) cout << i;  Prints?",
       [("A", "12", "loop-boundary"), ("B", "123", None), ("C", "0123", None), ("D", "1234", "loop-boundary")], "B"),
    _n("loops", 1, "int s = 0;  for (int i = 0; i < 4; i++) s += i;  cout << s;  Prints?",
       [("A", "10", "loop-boundary"), ("B", "6", None), ("C", "4", None), ("D", "3", None)], "B"),
    _n("loops", 2, "for (int i = 5; i > 0; i -= 2) cout << i;  Prints?",
       [("A", "53", "loop-boundary"), ("B", "531", None), ("C", "5310", "loop-boundary"), ("D", "Infinite loop", None)], "B"),
    _n("loops", 2, "int i = 0;  while (i < 3) { i++; cout << i; }  Prints?",
       [("A", "012", "loop-update-order"), ("B", "123", None), ("C", "Infinite loop", "loop-missing-update"), ("D", "3", None)], "B"),
    _n("loops", 3, "int c = 0;  for (int i = 0; i < 3; i++) for (int j = 0; j < 2; j++) c++;  cout << c;  Prints?",
       [("A", "5", "loop-nested-add"), ("B", "6", None), ("C", "3", None), ("D", "2", None)], "B"),
    _n("loops", 3, "for (int i = 0; i < 5; i++) { if (i == 2) continue; cout << i; }  Prints?",
       [("A", "01", "loop-continue-break"), ("B", "0134", None), ("C", "01234", None), ("D", "034", None)], "B"),

    _n("recursion", 1, "int f(int n) { if (n <= 1) return 1; return n * f(n - 1); }  f(4) = ?",
       [("A", "4", "rec-last-call-only"), ("B", "24", None), ("C", "10", None), ("D", "1", "rec-base-is-result")], "B"),
    _n("recursion", 1, "void f(int n) { if (n == 0) return; cout << n; f(n - 1); }  f(3) prints?",
       [("A", "123", "rec-order"), ("B", "321", None), ("C", "3", None), ("D", "210", None)], "B"),
    _n("recursion", 2, "int f(int n) { if (n == 0) return 1; return 2 * f(n - 1); }  f(3) = ?",
       [("A", "6", None), ("B", "8", None), ("C", "1", "rec-base-is-result"), ("D", "4", None)], "B"),
    _n("recursion", 2, "int f(int n) { if (n <= 0) return 0; return n % 10 + f(n / 10); }  f(123) = ?",
       [("A", "3", "rec-last-call-only"), ("B", "6", None), ("C", "123", None), ("D", "0", "rec-base-is-result")], "B"),
    _n("recursion", 3, "int fib(int n) { if (n <= 1) return n; return fib(n - 1) + fib(n - 2); }  fib(5) = ?",
       [("A", "8", None), ("B", "5", None), ("C", "3", None), ("D", "10", None)], "B"),
    _n("recursion", 3, "void g(int n) { if (n == 0) return; cout << n; g(n - 1); cout << n; }  g(2) prints?",
       [("A", "21", "rec-order"), ("B", "2112", None), ("C", "12", "rec-order"), ("D", "1221", "rec-order")], "B"),
]

def seed(db):
    """Idempotent: adds anything missing, so existing databases pick up new questions."""
    if not db.query(Concept).count():
        db.add_all([Concept(id=i, name=n, prereqs=p) for i, n, p in CONCEPTS])
        db.commit()
    have_m = {m.id for m in db.query(Misconception)}
    db.add_all([Misconception(id=i, concept_id=c, description=d) for i, c, d in MISCONCEPTIONS if i not in have_m])
    have_q = {q.prompt for q in db.query(Question)}
    db.add_all([Question(**q) for q in QUESTIONS if q["prompt"] not in have_q])
    db.commit()
