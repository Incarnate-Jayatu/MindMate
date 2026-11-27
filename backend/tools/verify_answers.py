"""Dev tool: compile and run the C++ behind each question and check the stored answer. Needs g++.
Usage (from the backend folder):  python tools/verify_answers.py
"""
import os, random, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import variants
from app.seed import QUESTIONS, VERIFY

def check(job):
    label, prog, expected = job
    with tempfile.TemporaryDirectory() as d:
        src, exe = os.path.join(d, "p.cpp"), os.path.join(d, "p")
        open(src, "w").write(prog)
        build = subprocess.run(["g++", "-std=c++17", "-o", exe, src], capture_output=True, text=True)
        if "EXPECT_COMPILE_ERROR" in prog:
            return None if build.returncode != 0 and expected == "Compile error" else f"{label}: expected a compile error"
        if build.returncode != 0:
            return f"{label}: does not compile: {build.stderr[:200]}"
        out = subprocess.run([exe], capture_output=True, text=True, timeout=5).stdout.strip()
        return None if out == expected else f"{label}: program printed {out!r}, stored answer {expected!r}"

def main(seeds=8):
    jobs = []
    for q in QUESTIONS:
        if q["prompt"] in VERIFY:
            correct = next(o["text"] for o in q["options"] if o["key"] == q["answer_key"])
            jobs.append((f"[bank] {q['prompt'][:60]}", VERIFY[q["prompt"]], correct))
    for (concept, diff) in variants.TEMPLATES:
        for sd in range(seeds):
            _, cpp, correct = variants.make(concept, diff, random.Random(sd))
            jobs.append((f"[variant {concept}/{diff}/seed {sd}]", cpp, correct))
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        problems = [p for p in ex.map(check, jobs) if p]
    print(f"checked {len(jobs)} programs, problems: {len(problems)}")
    for p in problems:
        print(" -", p)
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
