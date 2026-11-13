"""Privilege and hardening: setuid, capabilities, auth files, credentials,
kernel configuration and the boot command line."""

from __future__ import annotations

import posixpath
import re
from typing import Iterator

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, FileChange, Finding
from .common import added, matching, regex

SETUID = regex(r"\bchmod\s+(?:[ugoa]*[+=][rwxt]*s|0?[2467][0-7]{3})\b",
               r"\bS_IS[UG]ID\b", r"\bsetcap\b", r"\bcap_[a-z_]+[+=]",
               r"\bCAP_(?:SYS_ADMIN|SETUID|SETGID|DAC_OVERRIDE|SYS_PTRACE|"
               r"SYS_MODULE|NET_ADMIN|SYS_RAWIO|BPF|PERFMON)\b",
               r"\bsetuid\s*\(\s*0\s*\)", r"\bsetgid\s*\(\s*0\s*\)",
               r"\bsetres[ug]id\s*\(\s*0", r"\bseteuid\s*\(\s*0\s*\)",
               r"--privileged\b", r"\bprivileged:\s*true",
               r"\ballowPrivilegeEscalation:\s*true", r"\bNOPASSWD\b",
               r"\bPermit(?:RootLogin|EmptyPasswords)\s+yes",
               r"\bpam_permit\.so\b", r"\bnullok\b")
ROOT_IDS = regex(r"\b(?:uid|gid)\s*[:=]\s*[\"']?0\b", r"\buid=0\b",
                 r"\buser\s+root\b|^\s*USER\s+root\b", flags=re.IGNORECASE)
AUTH_FILE = re.compile(r"(?:^|/)(?:sudoers(?:\.d/.*)?|doas\.conf|pam\.d/.*|"
                       r"authorized_keys\d?|sshd?_config(?:\.d/.*)?|shadow-?|"
                       r"passwd-?|group-?|gshadow-?|login\.defs|securetty|"
                       r"polkit-1/.*|\.ssh/.*|ssh_host_\w+_key(?:\.pub)?|"
                       r"\.k5login|\.rhosts|hosts\.equiv|limits\.conf|"
                       r"capability\.conf)\Z")
CREDENTIAL = re.compile(
    r"(?i)\b(?:pass(?:word|wd|phrase)?|pwd|secret|token|api[_-]?key|"
    r"access[_-]?key|private[_-]?key|auth|credential)s?\b[\w\"']*\s*[:=]+\s*"
    r"[\"']([^\"'\s$%{<]{4,})[\"']")
PLACEHOLDER = re.compile(r"(?i)^(?:x+|\*+|\.+|<.*>|\$\{.*\}|changeme|example|"
                         r"dummy|test|fake|placeholder|redacted|none|null|"
                         r"true|false)$")
KERNEL_CONFIG = re.compile(r"(?:^|/)(?:\.config|[^/]*defconfig|[^/]*\.config|"
                           r"config-[^/]+|kernel[^/]*\.conf(?:ig)?|Kconfig"
                           r"[^/]*|[^/]*\.fragment)\Z")
# Options whose loss weakens the kernel.
HARDENING = {
    "STACKPROTECTOR", "STACKPROTECTOR_STRONG", "STRICT_KERNEL_RWX",
    "STRICT_MODULE_RWX", "RANDOMIZE_BASE", "RANDOMIZE_MEMORY",
    "RANDOMIZE_KSTACK_OFFSET", "RANDOMIZE_KSTACK_OFFSET_DEFAULT", "MODULE_SIG",
    "MODULE_SIG_FORCE", "MODULE_SIG_ALL", "SECURITY", "SECURITY_LOCKDOWN_LSM",
    "SECURITY_LOCKDOWN_LSM_EARLY", "LOCK_DOWN_KERNEL_FORCE_INTEGRITY",
    "LOCK_DOWN_KERNEL_FORCE_CONFIDENTIALITY", "SECURITY_LANDLOCK",
    "SECURITY_YAMA", "SECURITY_SELINUX", "SECURITY_APPARMOR", "SECURITY_IPE",
    "SECCOMP", "SECCOMP_FILTER", "HARDENED_USERCOPY", "FORTIFY_SOURCE",
    "INIT_ON_ALLOC_DEFAULT_ON", "INIT_ON_FREE_DEFAULT_ON", "INIT_STACK_ALL_ZERO",
    "SLAB_FREELIST_RANDOM", "SLAB_FREELIST_HARDENED", "SHUFFLE_PAGE_ALLOCATOR",
    "PAGE_TABLE_ISOLATION", "MITIGATION_PAGE_TABLE_ISOLATION", "RETPOLINE",
    "MITIGATION_RETPOLINE", "CPU_MITIGATIONS", "SPECULATION_MITIGATIONS",
    "BPF_UNPRIV_DEFAULT_OFF", "BPF_JIT_ALWAYS_ON", "VMAP_STACK",
    "SCHED_STACK_END_CHECK", "BUG_ON_DATA_CORRUPTION", "LIST_HARDENED",
    "STRICT_DEVMEM", "IO_STRICT_DEVMEM", "STATIC_USERMODEHELPER",
    "ZERO_CALL_USED_REGS", "UBSAN_BOUNDS", "RANDSTRUCT_FULL",
    "INTEGRITY", "IMA", "IMA_APPRAISE", "EVM", "DM_VERITY", "X86_UMIP",
    "LEGACY_VSYSCALL_NONE", "SECURITY_DMESG_RESTRICT", "PANIC_ON_OOPS",
    "HARDENED_USERCOPY_DEFAULT_ON", "STACKLEAK", "GCC_PLUGIN_STACKLEAK",
    "KFENCE", "DEBUG_WX", "MODULE_SIG_SHA512", "IOMMU_DEFAULT_DMA_STRICT",
    "INTEL_IOMMU_DEFAULT_ON", "SECURITY_PERF_EVENTS_RESTRICT", "AUDIT",
}
# Options whose gain weakens the kernel.
RISKY = {
    "DEVMEM", "DEVKMEM", "DEVPORT", "KEXEC", "KEXEC_FILE", "HIBERNATION",
    "PROC_KCORE", "LEGACY_PTYS", "BINFMT_MISC", "USELIB", "MODIFY_LDT_SYSCALL",
    "LEGACY_VSYSCALL_EMULATE", "LEGACY_VSYSCALL_XONLY", "X86_X32",
    "X86_X32_ABI", "USERFAULTFD", "COMPAT_BRK", "COMPAT_VDSO", "ACPI_CUSTOM_METHOD",
    "MAGIC_SYSRQ", "KGDB", "KDB", "PTDUMP_DEBUGFS", "SECURITY_SELINUX_DISABLE",
    "SECURITY_WRITABLE_HOOKS", "MODULE_FORCE_LOAD", "X86_IOPL_IOPERM",
    "CMDLINE_OVERRIDE", "CMDLINE_FORCE", "BPF_UNPRIV_DEFAULT_OFF_DISABLE",
    "DEBUG_FS_ALLOW_ALL", "PROC_VMCORE", "CRASH_DUMP", "INET_DIAG",
    "MODULE_UNLOAD_TAINT_TRACKING", "STAGING", "KPROBE_EVENTS_ON_NOTRACE",
    "FTRACE_SYSCALLS", "NOTIFIER_ERROR_INJECTION", "FAULT_INJECTION",
    "EFI_CUSTOM_SSDT_OVERLAYS", "ACPI_TABLE_UPGRADE", "MMIOTRACE",
}
CONFIG_LINE = re.compile(r"^\s*(?:#\s*)?CONFIG_(\w+)(?:=(\S+)|\s+is not set)")
BOOT_FILE = re.compile(r"(?:^|/)(?:[^/]*cmdline[^/]*|grub\.cfg|grub|"
                       r"loader/entries/[^/]+\.conf|loader\.conf|"
                       r"extlinux\.conf|syslinux\.cfg|isolinux\.cfg|"
                       r"refind\.conf|limine\.(?:cfg|conf)|cmdline\.txt|"
                       r"uki\.conf|kernel-command-line)\Z")
BOOT_WEAKENING = re.compile(
    r"(?<![\w.-])(?:init|rdinit)=|\brd\.break\b|(?<![\w.-])(?:single|emergency|"
    r"rescue)(?![\w=.-])|\bnokaslr\b|\bmitigations=off\b|\bnopti\b|"
    r"\bpti=off\b|\bnospectre_v[12]\b|\bspectre_v2(?:_user)?=off\b|"
    r"\bspec_store_bypass_disable=off\b|\bl1tf=off\b|\bmds=off\b|\btaa=off\b|"
    r"\bmmio_stale_data=off\b|\bretbleed=off\b|\bsrbds=off\b|\bgather_data_"
    r"sampling=off\b|\btsx=on\b|\bmodule\.sig_enforce=0\b|\blockdown=none\b|"
    r"\b(?:selinux|apparmor|enforcing)=0\b|\bsecurity=none\b|"
    r"\b(?:intel_|amd_)?iommu=off\b|\bsystemd\.debug[_-]shell\b|\brd\.shell\b|"
    r"\bno_hash_pointers\b|\bvsyscall=emulate\b|\binit_on_(?:alloc|free)=0\b|"
    r"\brandomize_kstack_offset=off\b|\bpage_poison=0\b|\bima_appraise=off\b|"
    r"\bipe\.enforce=0\b|\bkfence\.sample_interval=0\b|\bslab_merge\b|"
    r"\bsysrq_always_enabled\b|\bdebugfs=on\b|\bnosmap\b|\bnosmep\b|"
    r"\bnoexec=off\b|\bnoexec32=off\b|\bkpti=0\b|\bmodule_blacklist=|"
    r"\bsystemd\.unit=(?:emergency|rescue)")


def check(ctx: Context) -> Iterator[Finding]:
    yield from matching(added(ctx), SETUID, HIGH, "privilege-escalation",
                        "grants or keeps elevated privilege")
    yield from matching(added(ctx), ROOT_IDS, REVIEW, "privilege-root-id",
                        "runs as, or creates, uid or gid 0")
    for change in ctx.files:
        if AUTH_FILE.search(change.path):
            yield Finding(HIGH, "privilege-auth-file", change.path, 0,
                          "controls who can log in or gain privilege")
    for change, number, text in added(ctx):
        match = CREDENTIAL.search(text)
        if match and not PLACEHOLDER.match(match.group(1)):
            yield Finding(HIGH, "privilege-credential", change.path, number,
                          f"a hard-coded credential or default password: "
                          f"{excerpt(text, 50)}")
    for change in ctx.changed():
        if KERNEL_CONFIG.search(change.path) and not change.binary:
            yield from _kernel_config(change)
        if BOOT_FILE.search(change.path) or KERNEL_CONFIG.search(change.path):
            yield from _boot(change)


def _kernel_config(change: FileChange) -> Iterator[Finding]:
    def options(lines) -> dict:
        found = {}
        for _, text in lines:
            match = CONFIG_LINE.match(text)
            if match:
                found[match.group(1)] = match.group(2) or "n"
        return found

    before = options(enumerate(change.old_text().split("\n"), start=1))
    after_lines = list(enumerate(change.new_text().split("\n"), start=1))
    after = options(after_lines)
    line_of = {}
    for number, text in after_lines:
        match = CONFIG_LINE.match(text)
        if match:
            line_of[match.group(1)] = number
    any_change = False
    for name in sorted(set(before) | set(after)):
        old, new = before.get(name, "n"), after.get(name, "n")
        if old == new:
            continue
        any_change = True
        number = line_of.get(name, 0)
        if name in HARDENING and old in ("y", "m") and new not in ("y", "m"):
            yield Finding(HIGH, "privilege-kernel-hardening", change.path,
                          number, f"turns off the kernel hardening option "
                          f"CONFIG_{name}")
        elif name in RISKY and new in ("y", "m") and old not in ("y", "m"):
            yield Finding(HIGH, "privilege-kernel-risky", change.path, number,
                          f"turns on CONFIG_{name}, which weakens the kernel")
        elif name in ("CMDLINE", "CMDLINE_BOOL", "INITRAMFS_SOURCE",
                      "SYSTEM_TRUSTED_KEYS", "MODULE_SIG_KEY",
                      "SYSTEM_BLACKLIST_HASH_LIST", "LSM", "DEFAULT_SECURITY",
                      "STATIC_USERMODEHELPER_PATH", "DEFAULT_INIT"):
            yield Finding(HIGH, "privilege-kernel-trust", change.path, number,
                          f"changes CONFIG_{name}, which decides what the "
                          f"kernel trusts or runs first")
    if any_change:
        yield Finding(REVIEW, "privilege-kernel-config", change.path, 0,
                      "the kernel configuration changed")


def _boot(change: FileChange) -> Iterator[Finding]:
    old = change.old_text()
    for number, text in change.added():
        for match in BOOT_WEAKENING.finditer(text):
            if match.group() not in old:
                yield Finding(HIGH, "privilege-boot-cmdline", change.path,
                              number, f"a boot option that weakens the "
                              f"system or gives a shell: "
                              f"{excerpt(match.group())}")
    if posixpath.basename(change.path) != ".config" and change.added() and \
            BOOT_FILE.search(change.path):
        yield Finding(REVIEW, "privilege-boot-config", change.path, 0,
                      "the boot configuration changed")
