"""Code that runs before main, hooks other code or hides what it includes:
XZ's backdoor hooked sshd through an IFUNC resolver."""

from __future__ import annotations

import re
from typing import Iterator

from ..model import HIGH, REVIEW, Context, Finding
from .common import added, matching, regex

NATIVE = re.compile(r"\.(?:c|cc|cpp|cxx|h|hh|hpp|hxx|m|mm|s|S|asm|inc|ld|lds|"
                    r"rs|zig|go|swift|d|nim|v)\Z|(?:^|/)[^/]*\.(?:mk|cmake)\Z|"
                    r"(?:^|/)(?:Makefile|CMakeLists\.txt|meson\.build|"
                    r"build\.rs|Kbuild)\Z")
BEFORE_MAIN = regex(r"__attribute__\s*\(\(\s*(?:constructor|destructor|ifunc)",
                    r"\b__attribute__\s*\(\(.*\bsection\s*\(\s*\"\.(?:init|fini|"
                    r"preinit)_array", r"\.(?:init|fini|preinit)_array\b",
                    r"\.ctors\b|\.dtors\b", r"#\s*pragma\s+(?:init|fini)\b",
                    r"\.type\s+\w+\s*,\s*[@%]gnu_indirect_function",
                    r"\b#\[link_section\s*=\s*\"\.init_array",
                    r"\b_init\s*\(\s*void\s*\)\s*\{", r"\bctor\b\s*\(",
                    r"\bDT_INIT\b")
LOADER = regex(r"\bLD_(?:PRELOAD|AUDIT|LIBRARY_PATH|BIND_NOW|DEBUG)\b",
               r"/etc/ld\.so\.(?:preload|conf)", r"\bla_(?:symbind|objopen)",
               r"\bRTLD_NEXT\b", r"_GLOBAL_OFFSET_TABLE_", r"\.got(?:\.plt)?\b",
               r"\blink_map\b", r"\b_r_debug\b|\br_debug\b", r"\b_dl_\w+",
               r"\bdl_iterate_phdr\b", r"\b__libc_\w+", r"\bDYLD_INSERT_LIBRARIES")
DYNAMIC = regex(r"\bdlopen\s*\(", r"\bdlsym\s*\(", r"\bdlvsym\s*\(",
                r"\bLoadLibrary\w*\s*\(", r"\bGetProcAddress\s*\(")
EXECUTABLE_MEMORY = regex(r"\bmprotect\s*\(.*PROT_EXEC",
                          r"\bmmap\s*\(.*PROT_EXEC", r"PROT_WRITE\s*\|\s*PROT_EXEC",
                          r"PROT_EXEC\s*\|\s*PROT_WRITE", r"\bVirtualProtect\w*\(",
                          r"PAGE_EXECUTE_READWRITE", r"\bmemfd_create\s*\(",
                          r"\bfexecve\s*\(", r"\bexecveat\s*\(")
INTERPOSE = re.compile(
    r"^\s*#\s*define\s+(?:mem(?:cpy|cmp|set|move)|str(?:n?cmp|n?cpy|len)|"
    r"malloc|free|getenv|system|exec\w*|open|read|write|connect|socket|"
    r"RSA_\w+|EVP_\w+|SSL_\w+|crypt|getpw\w+|pam_\w+|setuid|getuid)\b"
    r"|^\s*(?:extern\s+)?[\w\s\*]+\b(?:RSA_public_decrypt|RSA_\w+|EVP_\w+|"
    r"SSL_\w+|crypt|getpwnam|pam_authenticate|getuid|geteuid|setuid|"
    r"__libc_start_main|_IO_\w+)\s*\([^;]*\)\s*\{")
INCLUDE_DATA = regex(r"\.incbin\b", r"#\s*embed\b", r"\binclude_bytes!\s*\(",
                     r"\binclude_str!\s*\(", r"@embedFile\s*\(",
                     r"#\s*include\s*[<\"][^>\"]+\.(?!h\b|hh\b|hpp\b|hxx\b|inc\b|"
                     r"def\b|ipp\b|tcc\b|inl\b)\w+[>\"]")
LINKER = regex(r"-Wl,[^\s]*--wrap=", r"-Wl,[^\s]*--defsym", r"-Wl,-(?:init|fini)",
               r"--wrap=", r"--defsym", r"-Wl,-z,execstack",
               r"-Wl,[^\s]*-rpath", r"\$ORIGIN", r"\bRPATH\b|\bRUNPATH\b",
               r"-Wl,--export-dynamic", r"-rdynamic")
SYSCALL = regex(r"\bsyscall\s*\(\s*\d", r"\bint\s+\$?0x80\b", r"\bsvc\s+#?0\b",
                r"\bsyscall\b\s*$", r"\bsysenter\b")
TRIGRAPH = re.compile(r"\?\?[=/'()!<>\-]")
LINE_DIRECTIVE = re.compile(r"^\s*#\s*line\s+\d+")


def native(ctx: Context) -> Iterator:
    for line in added(ctx):
        if NATIVE.search(line[0].path):
            yield line


def check(ctx: Context) -> Iterator[Finding]:
    yield from matching(native(ctx), BEFORE_MAIN, HIGH, "hooking-before-main",
                        "code that runs before main or picks an "
                        "implementation at load time, as XZ's IFUNC hook did")
    yield from matching(native(ctx), LOADER, HIGH, "hooking-loader",
                        "reaches into the dynamic loader or symbol tables")
    yield from matching(added(ctx, "build"), LOADER, HIGH, "hooking-loader",
                        "reaches into the dynamic loader")
    yield from matching(native(ctx), DYNAMIC, REVIEW, "hooking-dynamic-load",
                        "loads code or looks up symbols at run time")
    yield from matching(native(ctx), EXECUTABLE_MEMORY, HIGH,
                        "hooking-executable-memory",
                        "makes memory executable or runs code from memory")
    yield from matching(native(ctx), INTERPOSE, HIGH, "hooking-interpose",
                        "defines or redefines a library or crypto function")
    yield from matching(added(ctx), INCLUDE_DATA, HIGH, "hooking-include-data",
                        "compiles a data file into the program")
    yield from matching(added(ctx, "build"), LINKER, HIGH, "hooking-linker",
                        "a linker option that wraps symbols, adds load-time "
                        "code or changes where libraries load from")
    yield from matching(native(ctx), SYSCALL, REVIEW, "hooking-raw-syscall",
                        "a raw system call")
    yield from matching(native(ctx), TRIGRAPH, HIGH, "hooking-trigraph",
                        "a trigraph, which the compiler reads differently "
                        "from how it looks")
    yield from matching(native(ctx), LINE_DIRECTIVE, REVIEW,
                        "hooking-line-directive",
                        "a #line directive, which makes errors point "
                        "elsewhere")
    for change in ctx.changed():
        if change.path.endswith((".ld", ".lds")):
            yield Finding(HIGH, "hooking-linker-script", change.path, 0,
                          "a linker script changed: it decides what code "
                          "and data go where")
