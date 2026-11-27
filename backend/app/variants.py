"""Template-based question variants. No AI or API key needed: answers are computed, never guessed."""
import random
from .models import Question
from .seed import NODE_DEF

def _prog(defs: str, body: str) -> str:
    return f"#include <iostream>\n#include <string>\n#include <stack>\n#include <queue>\nusing namespace std;\n{defs}\nint main() {{ {body} }}\n"

def _build(rng, concept, diff, prompt, correct, wrongs, extras):
    correct = str(correct)
    seen, opts = {correct}, [(correct, None)]
    for t, m in list(wrongs) + [(e, None) for e in extras]:
        t = str(t)
        if not t or t in seen:
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

# ---- strings ----
WORDS = ["planet", "garden", "orange", "bridge", "stored", "frozen"]

def strings_index(r):
    w, i = r.choice(WORDS), r.randint(1, 4)
    return (f'string s = "{w}";  cout << s[{i}];  Prints?', w[i],
            [(w[i - 1], "str-off-by-one"), (w[i + 1], None)], [w[0], w[-1]],
            _prog("", f'string s = "{w}"; cout << s[{i}];'))

def strings_substr(r):
    w, p, n = r.choice(WORDS), r.randint(0, 2), r.randint(2, 3)
    return (f'string s = "{w}";  cout << s.substr({p}, {n});  Prints?', w[p:p + n],
            [(w[p:n], "str-substr-args"), (w[p:n + 1], "str-substr-args"), (w[p + 1:p + 1 + n], "str-off-by-one")],
            [w[:n], w[p:p + n + 1], w[p + 1:p + n], w[-n:], w[p:p + 1]],
            _prog("", f'string s = "{w}"; cout << s.substr({p}, {n});'))

def strings_count(r):
    w = r.choice(["banana", "mississippi", "committee", "balloon", "coffee"])
    ch = r.choice(sorted(set(w)))
    c = w.count(ch)
    body = f"string s = \"{w}\"; int n = 0; for (int i = 0; i < s.size(); i++) if (s[i] == '{ch}') n++; cout << n;"
    return (f"string s = \"{w}\";  int n = 0;  for (int i = 0; i < s.size(); i++) if (s[i] == '{ch}') n++;  cout << n;  Prints?", c,
            [(c + 1, "str-off-by-one"), (c - 1, None), (len(w), None)], [c + 2, c + 3], _prog("", body))

# ---- stacks ----
def _pushes(name, v):
    return "  ".join(f"{name}.push({x});" for x in v)

def stack_top(r):
    v = r.sample(range(1, 10), r.randint(3, 4))
    return (f"stack<int> s;  {_pushes('s', v)}  cout << s.top();  Prints?", v[-1],
            [(v[0], "stack-fifo"), (v[1], None), (sum(v), None)], [v[-1] + 10, v[-1] + 11],
            _prog("", f"stack<int> s; {_pushes('s', v)} cout << s.top();"))

def stack_pop_top(r):
    v, m = r.sample(range(1, 10), 4), r.randint(1, 2)
    pops = "  ".join(["s.pop();"] * m)
    return (f"stack<int> s;  {_pushes('s', v)}  {pops}  cout << s.top();  Prints?", v[-1 - m],
            [(v[-1], "stack-fifo"), (v[-m], None), (v[m], None)], [v[0], sum(v)],
            _prog("", f"stack<int> s; {_pushes('s', v)} {pops} cout << s.top();"))

def stack_reverse(r):
    w = "".join(r.sample("abcdefghij", r.randint(3, 4)))
    rev = w[::-1]
    body = f'stack<char> s; for (char c : string("{w}")) s.push(c); while (!s.empty()) {{ cout << s.top(); s.pop(); }}'
    return (f'stack<char> s;  for (char c : string("{w}")) s.push(c);  while (!s.empty()) {{ cout << s.top(); s.pop(); }}  Prints?', rev,
            [(w, "stack-fifo"), (rev[0], None), (rev[1:] + rev[0], None)], [w[1:] + w[0], rev[0] + w], _prog("", body))

# ---- queues ----
def queue_front(r):
    v = r.sample(range(1, 10), r.randint(3, 4))
    return (f"queue<int> q;  {_pushes('q', v)}  cout << q.front();  Prints?", v[0],
            [(v[-1], "queue-lifo"), (v[1], None), (sum(v), None)], [v[0] + 10, v[0] + 11],
            _prog("", f"queue<int> q; {_pushes('q', v)} cout << q.front();"))

def queue_pop_front(r):
    v, m = r.sample(range(1, 10), 4), r.randint(1, 2)
    pops = "  ".join(["q.pop();"] * m)
    return (f"queue<int> q;  {_pushes('q', v)}  {pops}  cout << q.front();  Prints?", v[m],
            [(v[0], "queue-lifo"), (v[-1], "queue-back-front"), (v[m + 1], None)], [sum(v), v[m] + 10],
            _prog("", f"queue<int> q; {_pushes('q', v)} {pops} cout << q.front();"))

def queue_rotate(r):
    n = r.randint(4, 5)
    k = r.randint(1, n - 1)
    body = f"queue<int> q; for (int i = 1; i <= {n}; i++) q.push(i); for (int i = 0; i < {k}; i++) {{ q.push(q.front()); q.pop(); }} cout << q.front();"
    return (f"queue<int> q;  for (int i = 1; i <= {n}; i++) q.push(i);  for (int i = 0; i < {k}; i++) {{ q.push(q.front()); q.pop(); }}  cout << q.front();  Prints?", k + 1,
            [(k, "queue-back-front"), (k + 2, None), (1, None), (n, None)], [k + 3, k + 7], _prog("", body))

# ---- linked lists ----
def _ll(vals):
    s = "nullptr"
    for x in reversed(vals):
        s = f"new Node{{{x}, {s}}}"
    return s

def ll_next(r):
    v = r.sample(range(1, 10), 3)
    return (NODE_DEF + f"  Node* h = {_ll(v)};  cout << h->next->v;  Prints?", v[1],
            [(v[0], "ll-next-direction"), (v[2], None), (sum(v), None)], [v[1] + 10, v[1] + 11],
            _prog(NODE_DEF, f"Node* h = {_ll(v)}; cout << h->next->v;"))

def ll_sum_k(r):
    v, k = r.sample(range(1, 10), 4), r.randint(2, 3)
    c = sum(v[:k])
    code = f"Node* h = {_ll(v)};  int s = 0;  Node* p = h;  for (int i = 0; i < {k}; i++) {{ s += p->v; p = p->next; }}  cout << s;"
    return (NODE_DEF + f"  {code}  Prints?", c,
            [(sum(v[1:k + 1]), "ll-next-direction"), (sum(v[:k - 1]), "loop-boundary"), (sum(v), None)], [c + 1, c + 2],
            _prog(NODE_DEF, code.replace("  ", " ")))

def ll_insert(r):
    a, b, x = r.sample(range(1, 10), 3)
    code = f"Node* h = {_ll([a, b])};  Node* n = new Node{{{x}, h->next}};  h->next = n;  for (Node* p = h; p != nullptr; p = p->next) cout << p->v;"
    return (NODE_DEF + f"  {code}  Prints?", f"{a}{x}{b}",
            [(f"{x}{a}{b}", "ll-next-direction"), (f"{a}{x}", "ll-lose-head"), (f"{a}{b}{x}", None)],
            [f"{b}{x}{a}", f"{x}{b}"], _prog(NODE_DEF, code.replace("  ", " ")))

TEMPLATES = {
    ("arrays", 1): arrays_index, ("arrays", 2): arrays_every_other, ("arrays", 3): arrays_pass,
    ("loops", 1): loops_count, ("loops", 2): loops_sum, ("loops", 3): loops_nested,
    ("recursion", 1): rec_factorial, ("recursion", 2): rec_sum, ("recursion", 3): rec_power,
    ("strings", 1): strings_index, ("strings", 2): strings_substr, ("strings", 3): strings_count,
    ("stacks", 1): stack_top, ("stacks", 2): stack_pop_top, ("stacks", 3): stack_reverse,
    ("queues", 1): queue_front, ("queues", 2): queue_pop_front, ("queues", 3): queue_rotate,
    ("linkedlist", 1): ll_next, ("linkedlist", 2): ll_sum_k, ("linkedlist", 3): ll_insert,
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
