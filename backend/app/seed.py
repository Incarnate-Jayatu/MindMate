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


# ---- Part 7: strings, stacks, queues, linked lists ----
CONCEPTS += [
    ("strings", "Strings", ["arrays"]),
    ("stacks", "Stacks", ["arrays"]),
    ("queues", "Queues", ["stacks"]),
    ("linkedlist", "Linked Lists", ["arrays"]),
]

MISCONCEPTIONS += [
    ("str-off-by-one", "strings", "Counts characters from 1, or treats size() as the last valid index"),
    ("str-substr-args", "strings", "Thinks substr(start, length) takes an end position instead of a length"),
    ("str-char-arith", "strings", "Forgets that arithmetic on a char produces an int, not a char"),
    ("str-copy-shares", "strings", "Thinks copying a string shares the text, so editing the copy changes the original"),
    ("stack-fifo", "stacks", "Thinks a stack removes the oldest element first (like a queue)"),
    ("stack-pop-returns", "stacks", "Thinks pop() returns the removed value (in C++ it returns nothing)"),
    ("stack-top-removes", "stacks", "Thinks top() removes the element (it only reads it)"),
    ("queue-lifo", "queues", "Thinks a queue removes the newest element first (like a stack)"),
    ("queue-back-front", "queues", "Mixes up front() (next to leave) with back() (most recent arrival)"),
    ("queue-pop-returns", "queues", "Thinks pop() returns the removed value (in C++ it returns nothing)"),
    ("ll-next-direction", "linkedlist", "Mixes up which node a next pointer leads to"),
    ("ll-lose-head", "linkedlist", "Overwrites a pointer before saving it, losing the rest of the list"),
    ("ll-null-end", "linkedlist", "Forgets the list ends at nullptr, so miscounts or walks past the end"),
    ("ll-index-access", "linkedlist", "Thinks any node can be reached instantly like an array element"),
]

VERIFY = {}  # prompt -> C++ program whose output is the correct answer (checked by tools/verify_answers.py)
_INC = "#include <iostream>\n#include <string>\n#include <stack>\n#include <queue>\nusing namespace std;\n"
NODE_DEF = "struct Node { int v; Node* next; };"
NODE = NODE_DEF + "  "

def _v(c, d, prompt, opts, ans, code=None, defs=""):
    if code:
        VERIFY[prompt] = f"{_INC}{defs}\nint main() {{ {code} }}\n"
    return _q(c, d, prompt, opts, ans, shuffle=True)

QUESTIONS += [
    # ---- strings ----
    _v("strings", 1, 'string s = "hello";  cout << s[1];  Prints?',
       [("A", "h", "str-off-by-one"), ("B", "e", None), ("C", "l", None), ("D", "o", None)], "B",
       'string s = "hello"; cout << s[1];'),
    _v("strings", 1, 'string s = "code";  cout << s.size();  Prints?',
       [("A", "3", "str-off-by-one"), ("B", "4", None), ("C", "5", None), ("D", "code", None)], "B",
       'string s = "code"; cout << s.size();'),
    _v("strings", 2, 'string s = "abcdef";  cout << s.substr(2, 3);  Prints?',
       [("A", "cde", None), ("B", "cd", "str-substr-args"), ("C", "c", "str-substr-args"), ("D", "bcd", "str-off-by-one")], "A",
       'string s = "abcdef"; cout << s.substr(2, 3);'),
    _v("strings", 2, "char c = 'a';  cout << c + 1;  Prints?",
       [("A", "b", "str-char-arith"), ("B", "98", None), ("C", "a1", "str-char-arith"), ("D", "Compile error", None)], "B",
       "char c = 'a'; cout << c + 1;"),
    _v("strings", 3, "string a = \"hi\";  string b = a;  b[0] = 'H';  cout << a << b;  Prints?",
       [("A", "HiHi", "str-copy-shares"), ("B", "hiHi", None), ("C", "hihi", None), ("D", "Hihi", None)], "B",
       "string a = \"hi\"; string b = a; b[0] = 'H'; cout << a << b;"),
    _v("strings", 3, 'string s = "abc";  for (int i = s.size() - 1; i >= 0; i--) cout << s[i];  Prints?',
       [("A", "cba", None), ("B", "cb", "loop-boundary"), ("C", "abc", None), ("D", "Undefined behavior", "str-off-by-one")], "A",
       'string s = "abc"; for (int i = s.size() - 1; i >= 0; i--) cout << s[i];'),
    # ---- stacks ----
    _v("stacks", 1, "stack<int> s;  s.push(1);  s.push(2);  s.push(3);  cout << s.top();  Prints?",
       [("A", "1", "stack-fifo"), ("B", "3", None), ("C", "2", None), ("D", "6", None)], "B",
       "stack<int> s; s.push(1); s.push(2); s.push(3); cout << s.top();"),
    _v("stacks", 1, "stack<int> s;  s.push(5);  s.push(7);  s.pop();  cout << s.top();  Prints?",
       [("A", "7", "stack-fifo"), ("B", "5", None), ("C", "12", None), ("D", "0", None)], "B",
       "stack<int> s; s.push(5); s.push(7); s.pop(); cout << s.top();"),
    _v("stacks", 2, "stack<int> s;  s.push(4);  int x = s.pop();  What happens?",
       [("A", "x is 4", "stack-pop-returns"), ("B", "Compile error", None), ("C", "x is 0", None), ("D", "Undefined behavior", None)], "B",
       "stack<int> s; s.push(4); int x = s.pop(); //EXPECT_COMPILE_ERROR"),
    _v("stacks", 2, 'stack<char> s;  for (char c : string("abc")) s.push(c);  while (!s.empty()) { cout << s.top(); s.pop(); }  Prints?',
       [("A", "abc", "stack-fifo"), ("B", "cba", None), ("C", "acb", None), ("D", "c", None)], "B",
       'stack<char> s; for (char c : string("abc")) s.push(c); while (!s.empty()) { cout << s.top(); s.pop(); }'),
    _v("stacks", 3, "stack<int> s;  s.push(1);  s.push(2);  cout << s.top();  cout << s.top();  Prints?",
       [("A", "21", "stack-top-removes"), ("B", "22", None), ("C", "12", "stack-fifo"), ("D", "11", None)], "B",
       "stack<int> s; s.push(1); s.push(2); cout << s.top(); cout << s.top();"),
    _v("stacks", 3, "stack<int> s;  s.push(2);  s.push(3);  s.push(4);  int b = s.top();  s.pop();  int a = s.top();  s.pop();  s.push(a * b);  cout << s.top() + s.size();  Prints?",
       [("A", "12", None), ("B", "13", None), ("C", "14", None), ("D", "24", None)], "C",
       "stack<int> s; s.push(2); s.push(3); s.push(4); int b = s.top(); s.pop(); int a = s.top(); s.pop(); s.push(a * b); cout << s.top() + s.size();"),
    # ---- queues ----
    _v("queues", 1, "queue<int> q;  q.push(1);  q.push(2);  q.push(3);  cout << q.front();  Prints?",
       [("A", "3", "queue-lifo"), ("B", "1", None), ("C", "2", None), ("D", "6", None)], "B",
       "queue<int> q; q.push(1); q.push(2); q.push(3); cout << q.front();"),
    _v("queues", 1, "queue<int> q;  q.push(1);  q.push(2);  q.push(3);  cout << q.back();  Prints?",
       [("A", "1", "queue-back-front"), ("B", "3", None), ("C", "2", None), ("D", "0", None)], "B",
       "queue<int> q; q.push(1); q.push(2); q.push(3); cout << q.back();"),
    _v("queues", 2, "queue<int> q;  q.push(5);  q.push(7);  q.pop();  cout << q.front();  Prints?",
       [("A", "5", "queue-lifo"), ("B", "7", None), ("C", "12", None), ("D", "0", None)], "B",
       "queue<int> q; q.push(5); q.push(7); q.pop(); cout << q.front();"),
    _v("queues", 2, "queue<int> q;  q.push(4);  int x = q.pop();  What happens?",
       [("A", "x is 4", "queue-pop-returns"), ("B", "Compile error", None), ("C", "x is 0", None), ("D", "Undefined behavior", None)], "B",
       "queue<int> q; q.push(4); int x = q.pop(); //EXPECT_COMPILE_ERROR"),
    _v("queues", 3, "queue<int> q;  for (int i = 1; i <= 3; i++) q.push(i);  while (q.size() > 1) q.pop();  cout << q.front();  Prints?",
       [("A", "1", "queue-lifo"), ("B", "3", None), ("C", "2", None), ("D", "0", None)], "B",
       "queue<int> q; for (int i = 1; i <= 3; i++) q.push(i); while (q.size() > 1) q.pop(); cout << q.front();"),
    _v("queues", 3, "queue<int> q;  q.push(1);  q.push(2);  q.push(3);  q.push(q.front());  q.pop();  cout << q.front() << q.back();  Prints?",
       [("A", "21", None), ("B", "11", None), ("C", "23", None), ("D", "12", "queue-back-front")], "A",
       "queue<int> q; q.push(1); q.push(2); q.push(3); q.push(q.front()); q.pop(); cout << q.front() << q.back();"),
    # ---- linked lists ----
    _v("linkedlist", 1, NODE + "Node* a = new Node{1, nullptr};  Node* b = new Node{2, a};  cout << b->next->v;  Prints?",
       [("A", "2", "ll-next-direction"), ("B", "1", None), ("C", "0", None), ("D", "Crash (null pointer)", "ll-null-end")], "B",
       "Node* a = new Node{1, nullptr}; Node* b = new Node{2, a}; cout << b->next->v;", NODE_DEF),
    _v("linkedlist", 1, NODE + "Node* h = new Node{1, new Node{2, new Node{3, nullptr}}};  int n = 0;  for (Node* p = h; p != nullptr; p = p->next) n++;  cout << n;  Prints?",
       [("A", "3", None), ("B", "2", "ll-null-end"), ("C", "4", "ll-null-end"), ("D", "1", None)], "A",
       "Node* h = new Node{1, new Node{2, new Node{3, nullptr}}}; int n = 0; for (Node* p = h; p != nullptr; p = p->next) n++; cout << n;", NODE_DEF),
    _v("linkedlist", 2, NODE + "Node* h = new Node{1, new Node{2, new Node{3, nullptr}}};  Node* p = h->next;  cout << p->v + p->next->v;  Prints?",
       [("A", "5", None), ("B", "3", "ll-next-direction"), ("C", "6", None), ("D", "4", None)], "A",
       "Node* h = new Node{1, new Node{2, new Node{3, nullptr}}}; Node* p = h->next; cout << p->v + p->next->v;", NODE_DEF),
    _v("linkedlist", 2, "In a singly linked list, how do you reach the 5th node starting from the head pointer?",
       [("A", "Follow next 4 times", None), ("B", "Jump straight to it, like a[4]", "ll-index-access"),
        ("C", "Follow next 5 times", None), ("D", "Start from the tail pointer", None)], "A"),
    _v("linkedlist", 3, NODE + "Node* h = new Node{2, nullptr};  Node* n = new Node{1, h};  h = n;  cout << h->v << h->next->v;  Prints?",
       [("A", "12", None), ("B", "21", "ll-next-direction"), ("C", "11", None), ("D", "Crash (null pointer)", "ll-null-end")], "A",
       "Node* h = new Node{2, nullptr}; Node* n = new Node{1, h}; h = n; cout << h->v << h->next->v;", NODE_DEF),
    _v("linkedlist", 3, NODE + "Node* c = new Node{1, new Node{2, nullptr}};  Node* nx = c->next;  c->next = nullptr;  cout << c->v << nx->v << (c->next == nullptr);  Prints?",
       [("A", "121", None), ("B", "211", "ll-next-direction"), ("C", "Crash (null pointer)", "ll-lose-head"), ("D", "120", None)], "A",
       "Node* c = new Node{1, new Node{2, nullptr}}; Node* nx = c->next; c->next = nullptr; cout << c->v << nx->v << (c->next == nullptr);", NODE_DEF),
]

def seed(db):
    """Idempotent: adds anything missing, so existing databases pick up new topics and questions."""
    have_c = {c.id for c in db.query(Concept)}
    db.add_all([Concept(id=i, name=n, prereqs=p) for i, n, p in CONCEPTS if i not in have_c])
    db.commit()
    have_m = {m.id for m in db.query(Misconception)}
    db.add_all([Misconception(id=i, concept_id=c, description=d) for i, c, d in MISCONCEPTIONS if i not in have_m])
    have_q = {q.prompt for q in db.query(Question)}
    db.add_all([Question(**q) for q in QUESTIONS if q["prompt"] not in have_q])
    db.commit()
