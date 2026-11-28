"""Template-based question variants. No AI or API key needed: answers are computed, never guessed."""
import random
from .models import Question
import math
from .seed import NODE_DEF, DN_DEF, BST_DEF

def _prog(defs: str, body: str) -> str:
    return f"#include <iostream>\n#include <string>\n#include <stack>\n#include <queue>\n#include <algorithm>\nusing namespace std;\n{defs}\nint main() {{ {body} }}\n"

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

# ---- searching ----
def search_linear(r):
    a = r.sample(range(1, 20), 5)
    if r.random() < 0.3:
        t, k = r.choice([x for x in range(1, 20) if x not in a]), -1
    else:
        k = r.randint(0, 4)
        t = a[k]
    code = f"int a[] = {_arr(a)};  int idx = -1;  for (int i = 0; i < 5; i++) if (a[i] == {t}) {{ idx = i; break; }}  cout << idx;"
    if k >= 0:
        wrongs, extras = [(k + 1, "search-bounds-off-by-one"), (t, None), (-1, "search-not-found")], [k + 2, k + 3, k + 4]
    else:
        wrongs, extras = [(0, "search-not-found"), (5, None), (t, None)], [1, 2, 3]
    return (NODE_PREFIX_NONE + code + "  Prints?", k, wrongs, extras, _prog("", code.replace("  ", " ")))

NODE_PREFIX_NONE = ""

def search_binary_steps(r):
    n = r.choice([7, 9])
    a = sorted(r.sample(range(1, 60), n))
    k = r.randint(0, n - 1)
    t = a[k]
    lo, hi, steps = 0, n - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        steps += 1
        if a[mid] == t:
            break
        if a[mid] < t:
            lo = mid + 1
        else:
            hi = mid - 1
    code = (f"int a[] = {_arr(a)};  int lo = 0, hi = {n - 1}, steps = 0;  while (lo <= hi) {{ int mid = (lo + hi) / 2; steps++; "
            f"if (a[mid] == {t}) break; if (a[mid] < {t}) lo = mid + 1; else hi = mid - 1; }}  cout << steps;")
    return (code + "  Prints?", steps,
            [(k + 1, "search-linear-thinking"), (steps + 1, None), (steps - 1 if steps > 1 else steps + 2, None), (n, "search-linear-thinking")],
            [steps + 3, steps + 4], _prog("", code.replace("  ", " ")))

def search_binary_unsorted(r):
    for _ in range(200):
        a = r.sample(range(1, 30), 5)
        t = r.choice(a)
        lo, hi, found = 0, 4, -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if a[mid] == t:
                found = mid
                break
            if a[mid] < t:
                lo = mid + 1
            else:
                hi = mid - 1
        if found != a.index(t):
            break
    true = a.index(t)
    code = (f"int a[] = {_arr(a)};  int lo = 0, hi = 4, found = -1;  while (lo <= hi) {{ int mid = (lo + hi) / 2; "
            f"if (a[mid] == {t}) {{ found = mid; break; }} if (a[mid] < {t}) lo = mid + 1; else hi = mid - 1; }}  cout << found;")
    return (code + "  Prints?", found,
            [(true, "search-binary-unsorted"), (true + 1, None), (4, None)], [0, 1, 2, 3], _prog("", code.replace("  ", " ")))

# ---- sorting ----
def sort_swap(r):
    x, y = r.sample(range(1, 10), 2)
    code = f"int a = {x}, b = {y};  a = b;  b = a;  cout << a << b;"
    return (code + "  Prints?", f"{y}{y}",
            [(f"{y}{x}", "sort-swap-overwrite"), (f"{x}{y}", None), (f"{x}{x}", None)], [f"{y}{y}0"],
            _prog("", code.replace("  ", " ")))

def _s(a):
    return "".join(map(str, a))

def sort_bubble_pass(r):
    for _ in range(200):
        a = r.sample(range(1, 10), 4)
        b = a[:]
        for j in range(3):
            if b[j] > b[j + 1]:
                b[j], b[j + 1] = b[j + 1], b[j]
        if b != sorted(a) and b != a:
            break
    sel = a[:]
    m = sel.index(min(sel))
    sel[0], sel[m] = sel[m], sel[0]
    code = f"int a[] = {_arr(a)};  for (int j = 0; j < 3; j++) if (a[j] > a[j + 1]) swap(a[j], a[j + 1]);  for (int x : a) cout << x;"
    return (code + "  Prints?", _s(b),
            [(_s(sorted(a)), "sort-one-pass"), (_s(a), None), (_s(sel), "sort-mixes-algorithms")],
            [_s(sorted(a, reverse=True)), _s(b[::-1])], _prog("", code.replace("  ", " ")))

def sort_comparisons(r):
    n = r.randint(4, 6)
    a = r.sample(range(1, 20), n)
    c = n * (n - 1) // 2
    code = (f"int a[] = {_arr(a)};  int c = 0;  for (int i = 0; i < {n - 1}; i++) for (int j = 0; j < {n - 1} - i; j++) "
            f"{{ c++; if (a[j] > a[j + 1]) swap(a[j], a[j + 1]); }}  cout << c;")
    return (code + "  Prints?", c,
            [(n, "sort-count-n"), (n * n, None), ((n - 1) * (n - 1), None)], [c + 1, c + 2, c + 4],
            _prog("", code.replace("  ", " ")))

# ---- binary search trees ----
class _Node:
    def __init__(self, v):
        self.v, self.l, self.r = v, None, None

def _ins(t, x):
    if t is None:
        return _Node(x)
    if x < t.v:
        t.l = _ins(t.l, x)
    else:
        t.r = _ins(t.r, x)
    return t

def _tree(vals):
    root = None
    for x in vals:
        root = _ins(root, x)
    return root

def _height(t):
    return -1 if t is None else 1 + max(_height(t.l), _height(t.r))

def _pre(t):
    return "" if t is None else str(t.v) + _pre(t.l) + _pre(t.r)

def bst_left_child(r):
    a = r.randint(8, 20)
    smalls = r.sample(range(1, a), 2)
    big = r.randint(a + 1, 30)
    rest = smalls + [big]
    r.shuffle(rest)
    order = [a] + rest
    t = _tree(order)
    left, right = t.l.v, t.r.v
    other = next(s for s in smalls if s != left)
    body = f"T* r = nullptr; for (int x : {_arr(order)}) r = ins(r, x); cout << r->l->v;"
    return (f"Insert {', '.join(map(str, order))} into an empty binary search tree (smaller values go left). What is the value of the left child of the root?",
            left, [(right, "bst-sides"), (other, "bst-insert-position"), (a, None)], [left + 1, left + 2], _prog(BST_DEF, body))

def bst_inorder(r):
    for _ in range(100):
        vals = r.sample(range(1, 10), 5)
        if vals != sorted(vals):
            break
    t = _tree(vals)
    body = f"T* r = nullptr; for (int x : {_arr(vals)}) r = ins(r, x); inord(r);"
    return (f"Insert {', '.join(map(str, vals))} into an empty binary search tree. What does an in-order traversal (left, node, right) print?",
            _s(sorted(vals)), [(_s(vals), "bst-inorder-order"), (_s(sorted(vals, reverse=True)), "bst-sides"), (_pre(t), None)],
            [_s(vals[::-1]), _s(sorted(vals)[1:] + sorted(vals)[:1]), _s(vals[1:] + vals[:1]), _s(sorted(vals[:2]) + sorted(vals[2:], reverse=True))],
            _prog(BST_DEF, body))

def bst_height(r):
    vals = r.sample(range(1, 30), 6)
    h = _height(_tree(vals))
    body = f"T* r = nullptr; for (int x : {_arr(vals)}) r = ins(r, x); cout << ht(r);"
    return (f"Insert {', '.join(map(str, vals))} into an empty binary search tree. What is its height (edges on the longest path from the root to a leaf)?",
            h, [(h + 1, "bst-height-off"), (h - 1 if h > 0 else h + 2, "bst-height-off"), (int(math.log2(6)), "bst-always-balanced")],
            [h + 2, 6], _prog(BST_DEF, body))

# ---- bit manipulation ----
def bits_ops(r):
    a, b = r.sample(range(1, 16), 2)
    op = r.choice(["&", "|", "^"])
    res = {"&": a & b, "|": a | b, "^": a ^ b}
    wrong = {"&": [(res["|"], "bit-and-or"), (res["^"], "bit-xor-meaning")],
             "|": [(res["&"], "bit-and-or"), (res["^"], "bit-xor-meaning")],
             "^": [(res["|"], "bit-xor-meaning"), (res["&"], "bit-and-or")]}[op]
    code = f"cout << ({a} {op} {b});"
    return (code + "  Prints?", res[op], wrong + [(a + b, None)], [res[op] + 1, res[op] + 2, res[op] + 4], _prog("", code))

def bits_shift(r):
    x, k, op = r.randint(2, 40), r.randint(1, 3), r.choice(["<<", ">>"])
    c = x << k if op == "<<" else x >> k
    opposite = x >> k if op == "<<" else x << k
    code = f"cout << ({x} {op} {k});"
    return (code + "  Prints?", c, [(opposite, "bit-shift-direction"), (x * k if op == "<<" else x // k, None)],
            [c + 1, c + 2, c * 2 + 1], _prog("", code))

def bits_testbit(r):
    n, p = r.randint(5, 60), r.randint(0, 3)
    c = (n >> p) & 1
    code = f"int n = {n};  cout << ((n >> {p}) & 1);"
    return (code + "  Prints?", c,
            [((n >> (p + 1)) & 1, "bit-position-from-1"), (n >> p, None), (n & 1, None), (n & (1 << p), None)], [2, 3, 5, 7],
            _prog("", code.replace("  ", " ")))

# ---- doubly linked lists ----
def dll_back(r):
    v = r.sample(range(1, 10), 3)
    code = (f"DNode* a = new DNode{{{v[0]}, nullptr, nullptr}};  DNode* b = new DNode{{{v[1]}, a, nullptr}};  "
            f"DNode* c = new DNode{{{v[2]}, b, nullptr}};  a->next = b;  b->next = c;  cout << c->prev->v;")
    return (DN_DEF + "  " + code + "  Prints?", v[1], [(v[2], "dll-direction"), (v[0], None), (sum(v), None)],
            [v[1] + 10, v[1] + 11], _prog(DN_DEF, code.replace("  ", " ")))

def dll_walk_back(r):
    v = r.sample(range(1, 10), 3)
    rev = _s(v[::-1])
    code = (f"DNode* a = new DNode{{{v[0]}, nullptr, nullptr}};  DNode* b = new DNode{{{v[1]}, a, nullptr}};  "
            f"DNode* c = new DNode{{{v[2]}, b, nullptr}};  a->next = b;  b->next = c;  "
            f"for (DNode* p = c; p != nullptr; p = p->prev) cout << p->v;")
    return (DN_DEF + "  " + code + "  Prints?", rev,
            [(_s(v), "dll-direction"), (rev[:-1], "dll-null-ends"), (rev[0], "dll-forgot-prev")], [rev[1:], _s(v[1:])],
            _prog(DN_DEF, code.replace("  ", " ")))

def dll_insert(r):
    a, c, x = r.sample(range(1, 10), 3)
    code = (f"DNode* a = new DNode{{{a}, nullptr, nullptr}};  DNode* c = new DNode{{{c}, a, nullptr}};  a->next = c;  "
            f"DNode* b = new DNode{{{x}, a, c}};  a->next = b;  c->prev = b;  cout << a->next->v << c->prev->v;")
    return (DN_DEF + "  " + code + "  Prints?", f"{x}{x}",
            [(f"{x}{a}", "dll-forgot-prev"), (f"{a}{x}", None), (f"{x}{c}", None)], [f"{c}{x}", f"{a}{c}"],
            _prog(DN_DEF, code.replace("  ", " ")))

TEMPLATES = {
    ("arrays", 1): arrays_index, ("arrays", 2): arrays_every_other, ("arrays", 3): arrays_pass,
    ("loops", 1): loops_count, ("loops", 2): loops_sum, ("loops", 3): loops_nested,
    ("recursion", 1): rec_factorial, ("recursion", 2): rec_sum, ("recursion", 3): rec_power,
    ("strings", 1): strings_index, ("strings", 2): strings_substr, ("strings", 3): strings_count,
    ("stacks", 1): stack_top, ("stacks", 2): stack_pop_top, ("stacks", 3): stack_reverse,
    ("queues", 1): queue_front, ("queues", 2): queue_pop_front, ("queues", 3): queue_rotate,
    ("linkedlist", 1): ll_next, ("linkedlist", 2): ll_sum_k, ("linkedlist", 3): ll_insert,
    ("searching", 1): search_linear, ("searching", 2): search_binary_steps, ("searching", 3): search_binary_unsorted,
    ("sorting", 1): sort_swap, ("sorting", 2): sort_bubble_pass, ("sorting", 3): sort_comparisons,
    ("bst", 1): bst_left_child, ("bst", 2): bst_inorder, ("bst", 3): bst_height,
    ("bits", 1): bits_ops, ("bits", 2): bits_shift, ("bits", 3): bits_testbit,
    ("dll", 1): dll_back, ("dll", 2): dll_walk_back, ("dll", 3): dll_insert,
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
