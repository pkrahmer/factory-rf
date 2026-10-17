import ctypes, os, subprocess, sys
libc = ctypes.CDLL(None, use_errno=True)
CREATE, ADD, RESTRICT = 444, 445, 446
# All file-system access rights of ABI 3+ that concern writing (handled -> denied unless allowed).
WRITE = (1 << 1) | (1 << 4) | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 12) | (1 << 13) | (1 << 14)
class Attr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64), ("handled_access_net", ctypes.c_uint64), ("scoped", ctypes.c_uint64)]
class Beneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]
def restrict(allowed):
    attr = Attr(WRITE, 0, 0)
    fd = libc.syscall(CREATE, ctypes.byref(attr), ctypes.sizeof(attr), 0)
    assert fd >= 0, ctypes.get_errno()
    for path in allowed:
        pfd = os.open(path, os.O_PATH)
        b = Beneath(WRITE if os.path.isdir(path) else (1 << 1) | (1 << 14), pfd)
        assert libc.syscall(ADD, fd, 1, ctypes.byref(b), 0) == 0, (path, ctypes.get_errno())
        os.close(pfd)
    assert libc.prctl(38, 1, 0, 0, 0) == 0  # PR_SET_NO_NEW_PRIVS
    assert libc.syscall(RESTRICT, fd, 0) == 0, ctypes.get_errno()
base = sys.argv[1]
os.makedirs(f"{base}/src", exist_ok=True); os.makedirs(f"{base}/docs", exist_ok=True)
open(f"{base}/story.md", "w").write("x\n")
restrict([f"{base}/src", f"{base}/story.md"])
def attempt(label, cmd):
    r = subprocess.run(["sh", "-c", cmd], capture_output=True, text=True)
    print(f"{label:38} {'ALLOWED' if r.returncode == 0 else 'REFUSED'} {r.stderr.strip()[:60]}")
attempt("write src/new.py (allowed folder)", f"echo a > {base}/src/new.py")
attempt("append story.md (allowed file)", f"echo b >> {base}/story.md")
attempt("create docs/x.md (not allowed)", f"echo c > {base}/docs/x.md")
attempt("create file at the root", f"echo d > {base}/root.txt")
attempt("rename story.md (folder not allowed)", f"mv {base}/story.md {base}/moved.md")
attempt("a child process (python) writing docs/", f"python3 -c \"open('{base}/docs/y','w')\"")
attempt("delete the story file", f"rm {base}/story.md")
