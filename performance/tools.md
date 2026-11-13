# Profiling and benchmark tools

The tools the `vibes:profiler` agent uses to find where a project spends its
time, and to write microbenchmarks that `bin/bench` can compare.

## How to use this file

1. Find the guides the project needs (`bin/guides-for`, or the guide column
   of [`guides/map.tsv`](../guides/map.tsv)). For each one, read its
   `### <guide id>` section under
   [Languages, formats and tools](#languages-formats-and-tools), for
   example `sed -n '/^### languages\/Python$/,/^### /p' performance/tools.md`.
2. Read the [system-level](#system-level) sections too: always
   [Any native process](#any-native-process), and [Builds](#builds),
   [Boot](#boot) and [Services](#services) when the project has one.
3. Choose tools in this order:
   - **Built in or already installed first.** Check with `command -v`. Ask
     the user before installing anything, and prefer a project-local
     install, such as a development dependency, to a global one.
   - **Sampling before instrumenting.** A sampler barely changes the timings.
     A tracer or instrumenting profiler adds overhead to every call and
     skews small functions, so use it to explain a hot spot a sampler found.
   - **Never sudo.** If a tool needs root, a sysctl change or a code-signing
     entitlement, say what it would need and use the next row instead.
4. Use these tools to find hot spots and to build language-level
   microbenchmarks. Make every before-and-after comparison with `bin/bench`,
   the plugin's own interleaved A/B runner, which runs the two versions in
   turn so drift hits both. It reads samples as one number per line, or as
   hyperfine JSON (`--export-json`). A command that measures something
   other than its own run time prints `metric <name> <value>` lines (see
   [Boot](#boot)).

Platforms: "macOS" means macOS on Apple Silicon; "Linux" means any
distribution. Kind is one of: CPU sampling, tracing, memory, I/O and
syscalls, lock and off-CPU, benchmark harness, build timing, boot timing,
query plan. Every tool's documentation is linked under [Sources](#sources).

## System-level

### Any native process

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --warmup 3 --runs 20 --export-json run.json './app args'` | Mean, stddev, min and max; JSON with every run's time |
| `/usr/bin/time -l` | memory | macOS | Part of macOS | `/usr/bin/time -l ./app` | Wall, user and sys time, max RSS, peak memory footprint, instructions retired, cycles |
| GNU time | memory | Linux | GPL-3.0-or-later | `/usr/bin/time -v ./app` | Wall and CPU time, max RSS, page faults, context switches |
| `sample` | CPU sampling | macOS | Proprietary (free) | `sample <pid> 10 -file sample.txt` (or `sample app -wait` to catch it at start) | Text call tree with sample counts per thread |
| xctrace Time Profiler | CPU sampling | macOS (full Xcode, not just the CLT) | Proprietary (free) | `xctrace record --template 'Time Profiler' --output app.trace --launch -- ./app` | `.trace` bundle; `xctrace export app.trace --toc` lists its tables as XML |
| xctrace Allocations | memory | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Allocations' --output alloc.trace --launch -- ./app` | Allocations by call stack over time |
| `leaks`, `heap`, `vmmap` | memory | macOS | Proprietary (free) | `leaks --atExit -- ./app`; `heap <pid>`; `vmmap --summary <pid>` | Leaked blocks with stacks; heap by class; memory regions |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record --save-only -o profile.json.gz -- ./app` | Firefox Profiler profile; `samply load profile.json.gz` serves it locally |
| perf record | CPU sampling | Linux | GPL-2.0-only | `perf record -F 999 -g -- ./app` then `perf report --stdio` | Call-graph report from `perf.data` |
| perf record (DWARF) | CPU sampling | Linux | GPL-2.0-only | `perf record --call-graph dwarf -- ./app` | Full stacks for code built without frame pointers; large `perf.data` |
| perf stat | benchmark harness | Linux | GPL-2.0-only | `perf stat -r 10 -- ./app` | Cycles, instructions, IPC, cache and branch misses, mean ± stddev |
| inferno | CPU sampling | macOS, Linux | CDDL-1.0 | `perf script \| inferno-collapse-perf \| inferno-flamegraph > flame.svg` | Flame graph SVG |
| FlameGraph scripts | CPU sampling | macOS, Linux | CDDL-1.0 | `perf script \| ./stackcollapse-perf.pl \| ./flamegraph.pl > flame.svg`; macOS: `stackcollapse-sample.awk sample.txt` | Flame graph SVG |
| Valgrind Callgrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=callgrind ./app` then `callgrind_annotate callgrind.out.<pid>` | Exact instruction counts per function and line; 20-100x slower |
| Valgrind Cachegrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=cachegrind --cache-sim=yes ./app` then `cg_annotate cachegrind.out.<pid>` | Instructions and simulated cache misses per line |
| Valgrind Massif | memory | Linux | GPL-3.0-or-later | `valgrind --tool=massif ./app` then `ms_print massif.out.<pid>` | Heap size over time, with the stacks at the peak |
| Valgrind DHAT | memory | Linux | GPL-3.0-or-later | `valgrind --tool=dhat ./app` | `dhat.out.<pid>`, opened in `dh_view.html`: short-lived and unused allocations |
| heaptrack | memory | Linux | LGPL-2.1-or-later | `heaptrack ./app` then `heaptrack_print heaptrack.app.<pid>.*` | Allocation hot spots, peak, leaks, temporary allocations |
| strace (summary) | I/O and syscalls | Linux | LGPL-2.1-or-later | `strace -c -f -o strace.txt ./app` | Count, errors and time per syscall |
| strace (trace) | I/O and syscalls | Linux | LGPL-2.1-or-later | `strace -f -tt -T -e trace=%file,%network -o trace.txt ./app` | Each call with its timestamp and duration |
| ltrace | tracing | Linux (x86-64 best) | GPL-2.0-or-later | `ltrace -c -f ./app` | Library call counts and time |
| perf context switches | lock and off-CPU | Linux | GPL-2.0-only | `perf record -e context-switches -g -- ./app` | Stacks where threads blocked or were switched out |
| samply off-CPU | lock and off-CPU | macOS | MIT OR Apache-2.0 | `samply record -- ./app` | macOS samples include blocked threads, so waits on locks and I/O show as stacks |
| `fs_usage`, `dtruss`, DTrace | I/O and syscalls | macOS | Proprietary (free) | Not available: they need root (and DTrace needs SIP relaxed) | Use `/usr/bin/time -l` block I/O counts and samply's off-CPU stacks instead |

- **perf without sudo.** Read `/proc/sys/kernel/perf_event_paranoid`. At 1
  or lower you can profile your own processes, kernel stacks included. At
  2, the upstream default, only user space: add `--all-user` to `perf
  record`. At 3 or higher (a Debian and Ubuntu patch) perf and samply are
  blocked; don't change it, say what it would take, and fall back to
  Valgrind or the language's own profiler.
- **Off-CPU on Linux without root.** The bcc and bpftrace tools need root.
  Use `perf record -e context-switches -g`, or a language profiler's
  wall-clock mode (async-profiler `-e wall`, py-spy `--idle`, Go's block
  profile).
- **Symbols and frame pointers.** Profile an optimised build with debug
  info: `-O2 -g -fno-omit-frame-pointer` for C-family code. Apple's arm64
  ABI always keeps frame pointers.
- **macOS limits.** samply and `sample` can't profile system binaries or
  hardened apps (SIP); profile your own build. samply needs `samply setup`
  once, which self-signs it, before it can attach to a running pid.
  Valgrind doesn't run on Apple Silicon.

### Builds

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| hyperfine | build timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --prepare 'make clean' --export-json clean.json 'make -j8'`; no-op: `hyperfine 'make -j8'` | Clean, no-op and one-file-touched build times |
| GNU make `--trace` | build timing | macOS (GNU make 4+), Linux | GPL-3.0-or-later | `make --trace -j8 > trace.log` | Why each target was rebuilt, and its recipe; no times |
| GNU make `-d` | build timing | macOS, Linux | GPL-3.0-or-later | `make -d > debug.log` | Every decision make took; no times, very long |
| remake | build timing | Linux, macOS | GPL-3.0-or-later | `remake --profile -j8` | `callgrind.out.<pid>` per make run: time per target, read with `callgrind_annotate` |
| Ninja log | build timing | macOS, Linux | Apache-2.0 | `ninja -C build` then read `build/.ninja_log` | Start and end ms of every output, tab-separated |
| Ninja stats | build timing | macOS, Linux | Apache-2.0 | `ninja -C build -d stats` | Time ninja itself spent loading, parsing and stat-ing |
| ninjatracing | build timing | macOS, Linux | Apache-2.0 | `ninjatracing build/.ninja_log > trace.json` | Chrome trace; open in Perfetto UI or speedscope |
| clang `-ftime-trace` | build timing | macOS, Linux | Apache-2.0 WITH LLVM-exception | `clang -ftime-trace -c foo.c` (or add it to `CFLAGS`) | `foo.json` beside each object: time per header, template and pass |
| ClangBuildAnalyzer | build timing | macOS, Linux | Unlicense | `ClangBuildAnalyzer --all build cba.bin && ClangBuildAnalyzer --analyze cba.bin` | Slowest files, headers and templates across the build |
| GCC `-ftime-report` | build timing | macOS, Linux | GPL-3.0-or-later | `gcc -ftime-report -c foo.c` | Time per compiler pass, on stderr |
| ccache | build timing | macOS, Linux | GPL-3.0-or-later | `ccache --zero-stats`, build, then `ccache --show-stats` | Cache hit rate |
| `cargo build --timings` | build timing | macOS, Linux | MIT OR Apache-2.0 | `cargo build --release --timings` | `target/cargo-timings/cargo-timing.html`: time per crate and parallelism |
| Docker BuildKit | build timing | macOS, Linux | Apache-2.0 | `docker build --progress=plain --no-cache . 2>&1 \| tee build.log` | Each step with its `DONE <seconds>s` line, and `CACHED` steps |
| `docker buildx build` | build timing | macOS, Linux | Apache-2.0 | `docker buildx build --metadata-file meta.json .` | JSON with the build's ref, to find it in the build history |
| `docker buildx history` | build timing | macOS, Linux | Apache-2.0 | `docker buildx history ls` then `docker buildx history inspect <ref>` | Duration, cache use and steps of past builds |
| `docker buildx history trace` | build timing | macOS, Linux | Apache-2.0 | `docker buildx history trace <ref>` | The build's OpenTelemetry trace, in a temporary local Jaeger UI |
| Bazel | build timing | macOS, Linux | Apache-2.0 | `bazel build //... --profile=prof.json.gz` then `bazel analyze-profile prof.json.gz` | Phase times and critical path; the file is a Chrome trace |
| CMake configure | build timing | macOS, Linux | BSD-3-Clause | `cmake -S . -B build --profiling-format=google-trace --profiling-output=cmake.json` | Chrome trace of the configure step (CMake 3.18+) |
| Gradle | build timing | macOS, Linux | Apache-2.0 | `./gradlew build --profile` | HTML report in `build/reports/profile/` |

- Measure three builds: clean, no-op, and one source file touched. A slow
  no-op build is usually the build system, not the compiler.
- Don't use `gradle --scan`: it uploads the build to a remote service.
- macOS ships GNU make 3.81 as `/usr/bin/make`, which has no `--trace`; use
  `gmake` if installed.
- Docker Desktop on macOS builds inside a VM: compare builds on the same
  host only.

### Boot

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `systemd-analyze time` | boot timing | Linux (systemd) | LGPL-2.1-or-later | `systemd-analyze time` | Firmware, loader, kernel, initrd and userspace times |
| `systemd-analyze blame` | boot timing | Linux (systemd) | LGPL-2.1-or-later | `systemd-analyze blame` | Units sorted by start-up time |
| `systemd-analyze critical-chain` | boot timing | Linux (systemd) | LGPL-2.1-or-later | `systemd-analyze critical-chain` | The chain of units that held up boot |
| `systemd-analyze plot` | boot timing | Linux (systemd) | LGPL-2.1-or-later | `systemd-analyze plot > boot.svg` | SVG timeline of every unit |
| Kernel timestamps | boot timing | Linux | GPL-2.0-only | `dmesg`, or `journalctl -k -b -o short-monotonic` if `dmesg` is restricted | Seconds since boot on every kernel message |
| `initcall_debug` | boot timing | Linux | GPL-2.0-only | Add `initcall_debug printk.time=1` to the guest's kernel command line, then `dmesg \| grep initcall` | Time per kernel init call |
| systemd-bootchart | boot timing | Linux | LGPL-2.1-or-later | Kernel command line `init=/usr/lib/systemd/systemd-bootchart` (path varies) | SVG chart of CPU, I/O and processes during boot |
| QEMU, headless | boot timing | macOS (`-accel hvf`), Linux (`-accel kvm`) | GPL-2.0-only | `qemu-system-aarch64 -nographic -serial mon:stdio -no-reboot ...` | Guest serial console on stdout, ready to timestamp |
| hyperfine around QEMU | boot timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --runs 10 --export-json boot.json '<qemu command>'` with a guest that powers off when booted | Launch-to-power-off time per boot |

Time a headless boot to a marker line, and print it as a metric:

```sh
qemu-system-aarch64 -nographic -serial mon:stdio -no-reboot \
  -pidfile qemu.pid <machine, kernel and disk options> |
  perl -MTime::HiRes=time -ne '
    BEGIN { $t0 = time }
    if (/login:/) { printf "metric boot_ms %d\n", (time - $t0) * 1000; exit }'
kill "$(cat qemu.pid)" 2>/dev/null
```

- Print one `metric <name> <value>` line per measure, such as `boot_ms`,
  `kernel_ms` and `userspace_ms` (the last two from `systemd-analyze time`
  inside the guest).
- Use hardware acceleration (`hvf`, or `kvm` through the `kvm` group, not
  sudo). Emulating another architecture (TCG) is 10-50x slower: only
  compare runs that use the same accelerator.
- Discard the first boot of a new image: it does one-off work such as
  growing the file system and making SSH host keys.

### Services

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| oha | benchmark harness | macOS, Linux | MIT | `oha -z 30s -c 64 -q 500 --latency-correction --no-tui --output-format json http://127.0.0.1:8080/` | Requests/s and latency percentiles as JSON |
| vegeta | benchmark harness | macOS, Linux | MIT | `echo 'GET http://127.0.0.1:8080/' \| vegeta attack -rate=500 -duration=30s \| vegeta report` | Constant-rate p50, p90, p95, p99 and max; `-type=json` for JSON |
| k6 | benchmark harness | macOS, Linux | AGPL-3.0 | `k6 run --summary-trend-stats='avg,p(50),p(95),p(99)' load.js` | Scripted scenarios with thresholds and percentiles |
| wrk | benchmark harness | macOS, Linux | Apache-2.0 (modified) | `wrk -t4 -c64 -d30s --latency http://127.0.0.1:8080/` | Requests/s and a latency distribution |
| ab | benchmark harness | macOS (built in), Linux | Apache-2.0 | `ab -n 10000 -c 64 http://127.0.0.1:8080/` | Requests/s and a percentile table; HTTP/1.0, one thread |
| curl | benchmark harness | macOS, Linux | curl | `curl -s -o /dev/null -w '%{time_starttransfer}\n' http://127.0.0.1:8080/` | One request's time to first byte, one value per line |

- Report percentiles (p50, p99), never only the mean.
- wrk and ab wait for each reply before sending the next request, which
  hides queueing (coordinated omission). For latency, use a constant rate:
  vegeta, `oha -q` with `--latency-correction`, or a k6 arrival-rate
  scenario.
- Warm the service up first, and run the load generator on other cores or
  another machine.
- Only load-test a local or test instance, never production or a
  third-party host.
- For `bin/bench`, print one number per run, such as the p99 in ms.

## Languages, formats and tools

### languages/Assembly-GAS-ARM64

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record -- ./app` | Hot instructions within each routine |
| xctrace CPU Counters | CPU sampling | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'CPU Counters' --output cpu.trace --launch -- ./app` | Hardware counter samples |
| perf stat / annotate | CPU sampling | Linux (arm64) | GPL-2.0-only | `perf stat -e cycles,instructions -- ./app`; `perf record ./app && perf annotate --stdio` | IPC; samples per instruction |
| llvm-mca | tracing | macOS, Linux | Apache-2.0 WITH LLVM-exception | `llvm-mca -mtriple=aarch64 -mcpu=apple-m1 loop.s` | Static cycles per iteration, port pressure, bottleneck |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Whole-program time |

Samples: a small C harness calls the routine N times per run and prints ns
per call (`clock_gettime(CLOCK_MONOTONIC)`), one line per run.

Traps: Xcode's toolchain has no `llvm-mca`; it comes with Homebrew or
distribution LLVM. On Apple Silicon a run can
land on a performance or an efficiency core; take many runs.

### languages/Assembly-GAS-RISCV

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| perf stat | CPU sampling | Linux on RISC-V hardware | GPL-2.0-only | `perf stat -e cycles,instructions -- ./app` | Counters, where the board's SBI exposes them |
| llvm-mca | tracing | macOS, Linux | Apache-2.0 WITH LLVM-exception | `llvm-mca -mtriple=riscv64 -mcpu=sifive-u74 loop.s` | Static cycles per iteration for that core model |
| QEMU insn plugin | tracing | macOS, Linux | GPL-2.0-only | `qemu-riscv64 -plugin <path>/libinsn.so -d plugin ./app` | Instructions executed; not time |
| hyperfine | benchmark harness | Linux on RISC-V | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Whole-program time |

Samples: on hardware, ns per call as for ARM64; under QEMU, print the
instruction count as `metric insns <n>`.

Traps: time under QEMU emulation means nothing; compare instruction counts
or measure on real hardware.

### languages/Assembly-GAS-x86

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| perf stat / annotate | CPU sampling | Linux (x86-64) | GPL-2.0-only | `perf stat -e cycles,instructions,branch-misses -- ./app`; `perf annotate --stdio` | IPC; samples per instruction |
| samply | CPU sampling | Linux (x86-64) | MIT OR Apache-2.0 | `samply record -- ./app` | Hot instructions |
| Valgrind Cachegrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=cachegrind --cache-sim=yes ./app` | Instructions and cache misses per line |
| llvm-mca | tracing | macOS, Linux | Apache-2.0 WITH LLVM-exception | `llvm-mca -mtriple=x86_64 -mcpu=skylake loop.s` | Static cycles per iteration, port pressure |
| hyperfine | benchmark harness | Linux (x86-64) | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Whole-program time |

Samples: ns per call from a C harness, one line per run.

Traps: on Apple Silicon, x86-64 code runs under Rosetta 2; never time it
there. Pin the core on Linux with `taskset -c 2`.

### languages/Assembly-MASM-x86

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| llvm-mca | tracing | macOS, Linux | Apache-2.0 WITH LLVM-exception | Copy the loop body into `loop.s` with `.intel_syntax noprefix` at the top, then `llvm-mca -mtriple=x86_64 -mcpu=skylake loop.s` | Static cycles per iteration |
| samply, perf | CPU sampling | Linux (x86-64) | MIT OR Apache-2.0 | As for `languages/Assembly-GAS-x86`, if the project assembles with a MASM-compatible assembler such as UASM or JWasm | Hot instructions |

Samples: as for `languages/Assembly-GAS-x86`.

Traps: MASM itself runs only on Windows, which this agent doesn't use.
Without a MASM-compatible assembler, only static analysis is possible.

### languages/Assembly-NASM-x86

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| perf stat / annotate | CPU sampling | Linux (x86-64) | GPL-2.0-only | `perf stat -- ./app`; `perf record ./app && perf annotate --stdio` | IPC; samples per instruction |
| samply | CPU sampling | Linux (x86-64) | MIT OR Apache-2.0 | `samply record -- ./app` | Hot instructions |
| Valgrind Callgrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=callgrind ./app` | Exact instruction counts |
| llvm-mca | tracing | macOS, Linux | Apache-2.0 WITH LLVM-exception | Loop body in `loop.s` with `.intel_syntax noprefix`, then `llvm-mca -mtriple=x86_64 -mcpu=skylake loop.s` | Static cycles per iteration |
| hyperfine | benchmark harness | Linux (x86-64) | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Whole-program time |

Samples: ns per call from a C harness, one line per run.

Traps: assemble with `nasm -g -F dwarf` so perf can map samples to source
lines. Never time x86-64 code under Rosetta 2.

### languages/BASH

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| xtrace with `EPOCHREALTIME` | tracing | macOS, Linux (Bash 5+) | Part of Bash | `PS4='+ $EPOCHREALTIME ${BASH_SOURCE}:${LINENO} ' bash -x script.sh 2> trace.log` | Every command with a µs timestamp and its line |
| `time` keyword | benchmark harness | macOS, Linux | Part of Bash | `TIMEFORMAT=%R; time ./script.sh` | Wall seconds |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --warmup 2 --export-json run.json 'bash script.sh'` | Run times |
| strace | I/O and syscalls | Linux | LGPL-2.1-or-later | `strace -f -c -o strace.txt bash script.sh` | Fork, exec and I/O counts |

Find the slowest lines in an xtrace log:

```sh
awk '{ if (prev != "") print $2 - t, prev; t = $2; prev = $3 }' trace.log |
  sort -rn | head -20
```

Samples: hyperfine JSON.

Traps: macOS ships Bash 3.2 as `/bin/bash`, which has no `EPOCHREALTIME`;
use a newer Bash if one is installed. Forks dominate shell run time: count
subshells, `$(...)` and pipelines in loops. To trace into a file from
inside a script, set `BASH_XTRACEFD`.

### languages/SH

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `time` | benchmark harness | macOS, Linux | Part of the shell | `time sh script.sh` | Real, user and sys time |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'dash script.sh' 'bash --posix script.sh'` | Run times, and a comparison between shells |
| strace | I/O and syscalls | Linux | LGPL-2.1-or-later | `strace -f -c -o strace.txt sh script.sh` | Fork, exec and I/O counts |
| `sh -x` | tracing | macOS, Linux | Part of the shell | `sh -x script.sh 2> trace.log` | Commands in order; no timestamps |

Samples: hyperfine JSON.

Traps: POSIX sh has no clock variable, and putting `$(date ...)` in `PS4`
forks on every line, which swamps the timings (and macOS `date` has no
`%N`). Time whole scripts with hyperfine, or move the hot part into a
function and time that.

### languages/C

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record -- ./app` | Firefox Profiler profile |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- ./app` then `perf report --stdio` | Call graph |
| xctrace | CPU sampling | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Time Profiler' --launch -- ./app` | `.trace` bundle |
| gprof | tracing | Linux | GPL-3.0-or-later | Build with `-pg`, run `./app`, then `gprof ./app gmon.out` | Flat profile and call graph |
| Valgrind Callgrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=callgrind ./app` then `callgrind_annotate callgrind.out.<pid>` | Exact instruction counts per function |
| Valgrind Massif | memory | Linux | GPL-3.0-or-later | `valgrind --tool=massif ./app` then `ms_print massif.out.<pid>` | Heap size over time |
| heaptrack | memory | Linux | LGPL-2.1-or-later | `heaptrack ./app` | Allocation hot spots |
| `leaks` / Allocations | memory | macOS | Proprietary (free) | `leaks --atExit -- ./app` | Leaks with stacks |
| Tracy | tracing | macOS, Linux | BSD-3-Clause | Add `TracyCZone` macros, build with `-DTRACY_ENABLE` | Live timeline of zones, locks and allocations |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Run times |

Samples: a harness that times N calls with `clock_gettime(CLOCK_MONOTONIC)`
and prints ns per call, one line per run.

Traps: build what you ship, plus `-g -fno-omit-frame-pointer`; `-O0`
profiles mislead. Stop the compiler deleting benchmarked work: use the
result (sum it, or write it to a `volatile`). gprof isn't available on
macOS.

### languages/C++

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record -- ./app` | Firefox Profiler profile |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- ./app` then `perf report --stdio` | Call graph |
| xctrace | CPU sampling | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Time Profiler' --launch -- ./app` | `.trace` bundle |
| Valgrind Callgrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=callgrind ./app` then `callgrind_annotate callgrind.out.<pid>` | Exact instruction counts per function |
| Valgrind Massif | memory | Linux | GPL-3.0-or-later | `valgrind --tool=massif ./app` then `ms_print massif.out.<pid>` | Heap size over time |
| heaptrack | memory | Linux | LGPL-2.1-or-later | `heaptrack ./app` | Allocation hot spots, temporary allocations |
| Google Benchmark | benchmark harness | macOS, Linux | Apache-2.0 | `./bench --benchmark_repetitions=20 --benchmark_format=json --benchmark_out=gb.json` | Time per iteration for each repetition |
| nanobench | benchmark harness | macOS, Linux | MIT | `ankerl::nanobench::Bench().run("f", [&] { f(); });` | ns/op, error %, IPC on Linux |
| Catch2 `BENCHMARK` | benchmark harness | macOS, Linux | BSL-1.0 | `./tests "[!benchmark]"` | Mean and stddev with bootstrapped intervals |
| Tracy | tracing | macOS, Linux | BSD-3-Clause | Add `ZoneScoped;` to functions, build with `-DTRACY_ENABLE` | Live timeline of zones, locks and allocations |
| gperftools | CPU sampling | Linux | BSD-3-Clause | `CPUPROFILE=prof.out ./app` (linked with `-lprofiler`), then `pprof --text ./app prof.out` | Flat profile |

Samples: Google Benchmark JSON (one entry per repetition), reduced to one
`real_time` per line with `jq`, or a hand-written timing loop.

Traps: use `benchmark::DoNotOptimize` or nanobench's `doNotOptimizeAway`
so the work isn't deleted. Profile with `-O2 -g -fno-omit-frame-pointer`.
Template-heavy code: check build time with `-ftime-trace` (see
[Builds](#builds)).

### languages/ObjC

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| xctrace Time Profiler | CPU sampling | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Time Profiler' --launch -- ./app` | `.trace` bundle |
| `sample` | CPU sampling | macOS | Proprietary (free) | `sample <pid> 10 -file sample.txt` | Text call tree |
| samply | CPU sampling | macOS | MIT OR Apache-2.0 | `samply record -- ./app` | Firefox Profiler profile |
| `leaks`, `heap` | memory | macOS | Proprietary (free) | `leaks --atExit -- ./app`; `heap <pid>` | Leaks and heap by class |
| XCTest `measure` | benchmark harness | macOS | Proprietary (free) | `[self measureBlock:^{ ... }];` run by `xcodebuild test` | Average and relative stddev over 10 runs |
| perf | CPU sampling | Linux (GNUstep) | GPL-2.0-only | `perf record -g -- ./app` | Call graph |

Samples: a loop timing the code with `clock_gettime_nsec_np(CLOCK_UPTIME_RAW)`,
printing one value per line.

Traps: `objc_msgSend` and retain/release often top the profile; look at
their callers. Autorelease pools in tight loops hold memory until drained.

### languages/ObjC++

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| xctrace Time Profiler | CPU sampling | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Time Profiler' --launch -- ./app` | `.trace` bundle |
| `sample` | CPU sampling | macOS | Proprietary (free) | `sample <pid> 10 -file sample.txt` | Text call tree |
| samply | CPU sampling | macOS | MIT OR Apache-2.0 | `samply record -- ./app` | Firefox Profiler profile |
| `leaks`, `heap` | memory | macOS | Proprietary (free) | `leaks --atExit -- ./app` | Leaks with stacks |
| Google Benchmark | benchmark harness | macOS | Apache-2.0 | `./bench --benchmark_repetitions=20 --benchmark_format=json` | Time per repetition |

Samples: as for `languages/C++`.

Traps: as for `languages/ObjC` and `languages/C++`.

### languages/Clojure

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| JFR | CPU sampling | macOS, Linux | Part of the JDK | `clojure -J-XX:StartFlightRecording=duration=60s,filename=rec.jfr -M -m app.main` then `jfr view hot-methods rec.jfr` | Hot methods, allocation, GC |
| clj-async-profiler | CPU sampling | macOS, Linux | EPL-1.0 | `(require '[clj-async-profiler.core :as prof]) (prof/profile (f))` | Flame graph HTML |
| criterium | benchmark harness | macOS, Linux | EPL-1.0 | `(require '[criterium.core :as c]) (c/quick-bench (f))` | Mean, stddev and outliers after JIT warm-up |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'clojure -M -m app.main'` | Start-up plus run time |

Samples: a loop printing `(- (System/nanoTime) t0)` per call after a
warm-up, one per line.

Traps: JIT warm-up; set `*warn-on-reflection*` true, since reflection is a
common hot spot. Start-up time is mostly JVM and Clojure loading: measure it
separately.

### languages/COBOL

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `cobc -x -g -O2 prog.cob && samply record -- ./prog` | Profile of the generated C, by program and paragraph function |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- ./prog` | Call graph |
| gprof | tracing | Linux | GPL-3.0-or-later | `cobc -x -A -pg -Q -pg prog.cob && ./prog && gprof ./prog gmon.out` | Flat profile |
| strace | I/O and syscalls | Linux | LGPL-2.1-or-later | `strace -c -f ./prog` | File I/O counts, for indexed and sequential files |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json './prog'` | Run times |

Samples: hyperfine JSON over a batch run.

Traps: this assumes GnuCOBOL, which compiles through C. `FUNCTION
CURRENT-DATE` only resolves to hundredths of a second. File I/O and
`DISPLAY` usually dominate batch jobs.

### languages/CSharp

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| dotnet-trace | CPU sampling | macOS, Linux | MIT | `dotnet-trace collect --format Speedscope -- dotnet bin/Release/<tfm>/App.dll` | `.nettrace` and a speedscope JSON |
| dotnet-counters | tracing | macOS, Linux | MIT | `dotnet-counters monitor -p <pid>` | Live CPU, GC, allocation rate, thread pool, exceptions |
| dotnet-gcdump | memory | macOS, Linux | MIT | `dotnet-gcdump collect -p <pid>` | Heap snapshot by type |
| BenchmarkDotNet | benchmark harness | macOS, Linux | MIT | `dotnet run -c Release -- --filter '*' --exporters json` | Mean, error, stddev, allocations; JSON report |
| `Stopwatch` | benchmark harness | macOS, Linux | Part of .NET | `var sw = Stopwatch.StartNew(); ...; sw.Elapsed` | Elapsed ticks |
| perf | CPU sampling | Linux | GPL-2.0-only | `DOTNET_PerfMapEnabled=1 perf record -g -- dotnet App.dll` | perf call graph with JIT method names |

Samples: a `Stopwatch` loop printing `sw.Elapsed.TotalNanoseconds` per run,
or the per-measurement values from BenchmarkDotNet's full JSON export.

Traps: always measure Release builds. Tiered JIT means early calls are
slower; BenchmarkDotNet handles warm-up. Server and workstation GC behave
very differently.

### languages/FSharp

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| dotnet-trace | CPU sampling | macOS, Linux | MIT | `dotnet-trace collect --format Speedscope -- dotnet bin/Release/<tfm>/App.dll` | `.nettrace` and a speedscope JSON |
| dotnet-counters | tracing | macOS, Linux | MIT | `dotnet-counters monitor -p <pid>` | Live GC and CPU counters |
| dotnet-gcdump | memory | macOS, Linux | MIT | `dotnet-gcdump collect -p <pid>` | Heap snapshot by type |
| BenchmarkDotNet | benchmark harness | macOS, Linux | MIT | `dotnet run -c Release -- --filter '*' --exporters json` | Mean, stddev, allocations |
| `#time` in FSI | benchmark harness | macOS, Linux | Part of F# | `#time "on"` in `dotnet fsi` | Real and CPU time, GC counts per evaluation |

Samples: as for `languages/CSharp`.

Traps: FSI runs unoptimised by default; benchmark compiled Release code.
Watch for closures and boxing in hot paths, and `seq` where an array would
do.

### languages/VB.NET

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| dotnet-trace | CPU sampling | macOS, Linux | MIT | `dotnet-trace collect --format Speedscope -- dotnet bin/Release/<tfm>/App.dll` | `.nettrace` and a speedscope JSON |
| dotnet-counters | tracing | macOS, Linux | MIT | `dotnet-counters monitor -p <pid>` | Live GC and CPU counters |
| dotnet-gcdump | memory | macOS, Linux | MIT | `dotnet-gcdump collect -p <pid>` | Heap snapshot by type |
| BenchmarkDotNet | benchmark harness | macOS, Linux | MIT | `dotnet run -c Release -- --filter '*' --exporters json` | Mean, stddev, allocations |

Samples: as for `languages/CSharp`.

Traps: late binding (`Option Strict Off`) is slow; check it's on in hot
code. Always measure Release builds.

### languages/Dart

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| DevTools CPU profiler | CPU sampling | macOS, Linux | BSD-3-Clause | `dart run --observe bin/app.dart`, then open the printed DevTools URL | CPU flame chart, memory, allocation tracing |
| AOT build + samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `dart compile exe bin/app.dart -o app && samply record -- ./app` | Native profile of the shipped code |
| `Stopwatch` | benchmark harness | macOS, Linux | Part of Dart | `final sw = Stopwatch()..start(); ...; sw.elapsedMicroseconds` | Elapsed µs |
| benchmark_harness | benchmark harness | macOS, Linux | BSD-3-Clause | `class B extends BenchmarkBase { ... }` then `B().report()` | µs per run |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Run times |

Samples: a `Stopwatch` loop printing `elapsedMicroseconds` per run.

Traps: JIT (`dart run`) and AOT (`dart compile exe`) differ; measure the
mode you ship. For Flutter, profile in profile mode, never debug mode.

### languages/Elixir

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `mix profile.tprof` | tracing | macOS, Linux | Part of Elixir | `mix profile.tprof -e "App.run()" --type time` | Time per function (Elixir 1.17+, OTP 27+) |
| `mix profile.eprof` / `profile.fprof` | tracing | macOS, Linux | Part of Elixir | `mix profile.eprof -e "App.run()"` | Time per function; fprof adds call trees |
| `:timer.tc` | benchmark harness | macOS, Linux | Part of Erlang/OTP | `{us, _} = :timer.tc(fn -> App.run() end)` | µs |
| Benchee | benchmark harness | macOS, Linux | MIT | `Benchee.run(%{"a" => fn -> a() end, "b" => fn -> b() end})` | ips, average, deviation, median, p99, memory |
| perf | CPU sampling | Linux | GPL-2.0-only | `ERL_FLAGS="+JPperf true" perf record -g -- mix run bench.exs` | perf call graph with Elixir function names |
| `:msacc` | lock and off-CPU | macOS, Linux | Part of Erlang/OTP | `:msacc.start(1000); :msacc.print()` | Scheduler time by state: emulator, GC, port, sleep |

Samples: a loop printing `elem(:timer.tc(fun), 0)` per run, one per line.

Traps: tracing profilers (eprof, fprof) slow every call; profile one
process or a small run. Measure in `MIX_ENV=prod`. Watch for message
queues growing (`Process.info(pid, :message_queue_len)`).

### languages/Erlang

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| tprof | tracing | macOS, Linux | Part of Erlang/OTP | `tprof:profile(app, run, [], #{type => call_time}).` | Time per function (OTP 27+); `call_memory` for allocation |
| eprof | tracing | macOS, Linux | Part of Erlang/OTP | `eprof:profile(fun() -> app:run() end), eprof:analyze().` | Time per function |
| fprof | tracing | macOS, Linux | Part of Erlang/OTP | `fprof:apply(app, run, []), fprof:profile(), fprof:analyse().` | Call tree with own and accumulated time; slow |
| cprof | tracing | macOS, Linux | Part of Erlang/OTP | `cprof:start(), app:run(), cprof:pause(), cprof:analyse().` | Call counts, low overhead |
| `timer:tc` | benchmark harness | macOS, Linux | Part of Erlang/OTP | `{Us, _} = timer:tc(fun() -> app:run() end).` | µs |
| msacc | lock and off-CPU | macOS, Linux | Part of Erlang/OTP | `msacc:start(1000), msacc:print().` | Scheduler time by state |
| perf | CPU sampling | Linux | GPL-2.0-only | `erl +JPperf true ...` under `perf record -g` | perf call graph with Erlang function names |

Samples: a loop printing `element(1, timer:tc(F))` per run.

Traps: tracing profilers slow every call; prefer cprof or perf to find the
hot spot first. Long message queues and large binaries copied between
processes are common culprits.

### languages/Fortran

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `gfortran -O2 -g -fno-omit-frame-pointer app.f90 -o app && samply record -- ./app` | Firefox Profiler profile |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- ./app` | Call graph |
| gprof | tracing | Linux | GPL-3.0-or-later | `gfortran -pg ...`, run, then `gprof ./app gmon.out` | Flat profile and call graph |
| Valgrind Cachegrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=cachegrind --cache-sim=yes ./app` | Cache misses per line: shows bad array traversal order |
| `system_clock` | benchmark harness | macOS, Linux | Part of Fortran | `call system_clock(t0, rate)` before and after | Ticks, divided by `rate` |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json './app'` | Run times |

Samples: a loop printing `system_clock` deltas, one per line.

Traps: arrays are column-major, so the leftmost index must vary fastest
in the inner loop. `-Warray-temporaries` shows hidden copies. gprof isn't
available on macOS.

### languages/Go

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| pprof CPU | CPU sampling | macOS, Linux | Part of Go | `go test -run '^$' -bench . -cpuprofile cpu.out ./pkg` then `go tool pprof -top cpu.out` | Hot functions |
| pprof memory | memory | macOS, Linux | Part of Go | `go test -run '^$' -bench . -benchmem -memprofile mem.out ./pkg` then `go tool pprof -sample_index=alloc_space -top mem.out` | Allocation sites |
| pprof block / mutex | lock and off-CPU | macOS, Linux | Part of Go | `go test -run '^$' -bench . -blockprofile block.out -mutexprofile mutex.out ./pkg` | Where goroutines block and wait on locks |
| `go tool trace` | tracing | macOS, Linux | Part of Go | `go test -run '^$' -bench . -trace trace.out ./pkg` then `go tool trace trace.out` | Goroutine scheduling, GC and syscalls over time |
| `net/http/pprof` | CPU sampling | macOS, Linux | Part of Go | `go tool pprof -top 'http://127.0.0.1:6060/debug/pprof/profile?seconds=30'` | Profile of a running service |
| `testing.B` | benchmark harness | macOS, Linux | Part of Go | `go test -run '^$' -bench . -benchmem -count 10 ./pkg > new.txt` | ns/op, B/op, allocs/op |
| benchstat | benchmark harness | macOS, Linux | BSD-3-Clause | `benchstat old.txt new.txt` | Change with confidence interval |
| `GODEBUG=gctrace=1` | memory | macOS, Linux | Part of Go | `GODEBUG=gctrace=1 ./app` | One line per GC: heap sizes and pause times |

Samples: `go test -run '^$' -bench BenchmarkX -count 20 ./pkg | awk
'/^Benchmark/ { print $3 }'` prints ns/op, one per line.

Traps: write benchmarks with `b.Loop()` (Go 1.24+) so the compiler can't
drop the work. Use `-count` of 10 or more. Profiling a whole test run
mixes test set-up into the profile; profile a benchmark.

### languages/Groovy

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| JFR | CPU sampling | macOS, Linux | Part of the JDK | `JAVA_OPTS='-XX:StartFlightRecording=duration=60s,filename=rec.jfr' groovy app.groovy` then `jfr view hot-methods rec.jfr` | Hot methods, allocation, GC |
| async-profiler | CPU sampling | macOS, Linux | Apache-2.0 | `asprof -d 30 -f flame.html <pid>` | Flame graph HTML |
| JMH (Gradle plugin) | benchmark harness | macOS, Linux | GPL-2.0-only WITH Classpath-exception-2.0; Apache-2.0 | `./gradlew jmh` | Score and error per benchmark; JSON results |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'groovy app.groovy'` | Start-up plus run time |

Samples: JMH JSON reduced to one value per line with `jq -r
'.[0].primaryMetric.rawData[][]' jmh.json`.

Traps: dynamic dispatch is slow in hot loops; compare with `@CompileStatic`.
Scripts recompile on every start.

### languages/Haskell

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `+RTS -s` | memory | macOS, Linux | Part of GHC | `./app +RTS -s` (link with `-rtsopts`) | Allocation, GC time, max residency, productivity |
| Cost-centre profiling | tracing | macOS, Linux | Part of GHC | `cabal run --enable-profiling --ghc-options=-fprof-late app -- +RTS -p` | `app.prof`: time and allocation per cost centre |
| Heap profile by type | memory | macOS, Linux | Part of GHC | `./app +RTS -hT -l` (no profiling build needed) | `app.eventlog` with heap by closure type |
| eventlog2html | memory | macOS, Linux | BSD-3-Clause | `eventlog2html app.eventlog` | Interactive HTML heap chart |
| tasty-bench | benchmark harness | macOS, Linux | MIT | `cabal bench --benchmark-options='--csv bench.csv'` | Mean and stddev per benchmark |
| criterion | benchmark harness | macOS, Linux | BSD-2-Clause | `cabal bench` | Mean with confidence interval, HTML report |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- ./app` | Native profile; GHC's stack makes call graphs partial |

Samples: tasty-bench CSV reduced to one mean per run, run under `bin/bench`.

Traps: profiling builds optimise differently; `-fprof-late` keeps the
result closest to the real build. Laziness causes space leaks: check max
residency in `+RTS -s` first.

### languages/Java

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| JFR | CPU sampling | macOS, Linux | Part of the JDK | `java -XX:StartFlightRecording=duration=60s,filename=rec.jfr -jar app.jar` then `jfr view hot-methods rec.jfr` (JDK 21+) | Hot methods, allocation, GC, locks, I/O |
| JFR on a running JVM | CPU sampling | macOS, Linux | Part of the JDK | `jcmd <pid> JFR.start duration=60s filename=rec.jfr` | As above |
| async-profiler | CPU sampling | macOS, Linux | Apache-2.0 | `asprof -d 30 -e cpu -f flame.html <pid>` | Flame graph; `-e wall`, `-e alloc`, `-e lock` for other kinds |
| GC log | memory | macOS, Linux | Part of the JDK | `java -Xlog:gc*:file=gc.log -jar app.jar` | Every GC with pause times |
| JMH | benchmark harness | macOS, Linux | GPL-2.0-only WITH Classpath-exception-2.0 | `java -jar target/benchmarks.jar -f 3 -wi 5 -i 10 -rf json -rff jmh.json` | Score, error and every iteration's value |

Samples: `jq -r '.[0].primaryMetric.rawData[][]' jmh.json`, one value per
line.

Traps: JIT warm-up; JMH handles it, hand-written loops don't. Return
results or use `Blackhole` so work isn't eliminated. Prefer JFR or
async-profiler: samplers that wait for safepoints point at the wrong
code.

### languages/JavaScript

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `--cpu-prof` | CPU sampling | macOS, Linux | Part of Node.js | `node --cpu-prof --cpu-prof-dir=prof app.js` | `.cpuprofile`, opened in Chrome DevTools or speedscope |
| `--heap-prof` | memory | macOS, Linux | Part of Node.js | `node --heap-prof --heap-prof-dir=prof app.js` | `.heapprofile` of sampled allocations |
| `--prof` | CPU sampling | macOS, Linux | Part of Node.js | `node --prof app.js` then `node --prof-process isolate-*.log > prof.txt` | V8 tick profile, JS and C++ |
| `--inspect` | tracing | macOS, Linux | Part of Node.js | `node --inspect app.js`, then attach Chrome DevTools | Interactive CPU and heap profiling |
| `--trace-gc` | memory | macOS, Linux | Part of Node.js | `node --trace-gc app.js` | One line per GC with pause time |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- node --perf-basic-prof app.js` | perf call graph with JS function names |
| `perf_hooks` | benchmark harness | macOS, Linux | Part of Node.js | `const { performance } = require('node:perf_hooks'); performance.now()` | ms with µs resolution |
| 0x | CPU sampling | macOS, Linux | MIT | `0x app.js` | Flame graph HTML |
| mitata | benchmark harness | macOS, Linux | MIT | `bench('f', () => f()); await run();` | Time per iteration with percentiles |
| tinybench | benchmark harness | macOS, Linux | MIT | `const b = new Bench(); b.add('f', f); await b.run(); console.table(b.table());` | ops/s, mean, margin |
| `deno bench` | benchmark harness | macOS, Linux | Part of Deno | `deno bench --json` | Per-benchmark statistics as JSON |
| Chrome DevTools Performance | tracing | macOS, Linux | Part of Chrome | Record in the Performance panel | Browser main-thread flame chart |

Samples: a loop printing `performance.now()` deltas per call after a
warm-up, one per line.

Traps: JIT warm-up and deoptimisation (`--trace-deopt`); GC pauses land
in whichever test runs then. Benchmark the production bundle, not a dev
server.

### languages/TypeScript

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `--cpu-prof` | CPU sampling | macOS, Linux | Part of Node.js | `node --enable-source-maps --cpu-prof dist/app.js` | `.cpuprofile` of the compiled JS |
| `--heap-prof` | memory | macOS, Linux | Part of Node.js | `node --heap-prof dist/app.js` | `.heapprofile` |
| `perf_hooks` | benchmark harness | macOS, Linux | Part of Node.js | `performance.now()` | ms with µs resolution |
| mitata / tinybench | benchmark harness | macOS, Linux | MIT | As for `languages/JavaScript` | Time per iteration |
| `tsc --extendedDiagnostics` | build timing | macOS, Linux | Apache-2.0 | `tsc --noEmit --extendedDiagnostics` | Parse, bind, check and emit times; memory |
| `tsc --generateTrace` | build timing | macOS, Linux | Apache-2.0 | `tsc --noEmit --generateTrace trace`, then `analyze-trace trace` (@typescript/analyze-trace, MIT) | Slowest files and types to check |

Samples: as for `languages/JavaScript`, run on the compiled output.

Traps: profile compiled JS, not `ts-node` or `tsx`, which add compile time
to start-up. Slow type-checking is a build problem: use the `tsc` rows.

### languages/Julia

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `@time` / `@allocated` | benchmark harness | macOS, Linux | Part of Julia | `@time f(x)` | Time, allocations, GC and compile share |
| Profile | CPU sampling | macOS, Linux | Part of Julia | `using Profile; @profile f(x); Profile.print(format=:flat, sortedby=:count)` | Samples per line |
| Profile.Allocs | memory | macOS, Linux | Part of Julia | `Profile.Allocs.@profile sample_rate=0.1 f(x)` | Allocation sites and types |
| `--track-allocation` | memory | macOS, Linux | Part of Julia | `julia --track-allocation=user app.jl` | `.mem` files with bytes per line |
| BenchmarkTools | benchmark harness | macOS, Linux | MIT | `using BenchmarkTools; @benchmark f($x)` | Min, median, mean, allocations |
| PProf.jl | CPU sampling | macOS, Linux | MIT | `using PProf; @profile f(x); pprof()` | pprof web view and flame graph |

Samples: `b = @benchmark f($x); foreach(println, b.times)` prints every
sample in ns.

Traps: the first call compiles; time later calls. Interpolate globals
with `$` in BenchmarkTools. Type instability (`@code_warntype`) is the
usual cause of allocations in hot loops.

### languages/Kotlin

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| JFR | CPU sampling | macOS, Linux | Part of the JDK | `java -XX:StartFlightRecording=duration=60s,filename=rec.jfr -jar app.jar` then `jfr view hot-methods rec.jfr` | Hot methods, allocation, GC |
| async-profiler | CPU sampling | macOS, Linux | Apache-2.0 | `asprof -d 30 -f flame.html <pid>` | Flame graph HTML |
| kotlinx-benchmark | benchmark harness | macOS, Linux | Apache-2.0 | `./gradlew benchmark` | JMH results for JVM targets; JSON reports |
| `measureNanoTime` | benchmark harness | macOS, Linux | Part of Kotlin | `val ns = measureNanoTime { f() }` | ns |
| Gradle profile | build timing | macOS, Linux | Apache-2.0 | `./gradlew build --profile` | Build report in `build/reports/profile/` |

Samples: a loop printing `measureNanoTime { f() }` per call after a
warm-up, or JMH JSON via `jq`.

Traps: JIT warm-up; boxing in generic code and `Sequence` versus list
choices show up as allocation. Coroutines hide waits from CPU profilers:
use async-profiler `-e wall`.

### languages/Lua

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| LuaJIT profiler | CPU sampling | macOS, Linux | MIT | `luajit -jp myapp.lua` | Top functions by samples |
| LuaJIT `-jv` | tracing | macOS, Linux | MIT | `luajit -jv myapp.lua` | JIT traces and aborts (code that falls back to the interpreter) |
| `os.clock` | benchmark harness | macOS, Linux | Part of Lua | `local t = os.clock(); f(); print(os.clock() - t)` | CPU seconds |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record -- lua app.lua` | Interpreter C frames only, for PUC Lua |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'lua app.lua'` | Run times |

Samples: a loop printing `os.clock()` deltas, one per line.

Traps: PUC Lua and LuaJIT differ a lot; measure the one the project runs.
String concatenation in loops is quadratic: use `table.concat`.

### languages/OCaml

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record --call-graph dwarf -- ./app.exe` | Native call graph |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record -- ./app.exe` | Firefox Profiler profile |
| olly | memory | macOS, Linux | ISC | `olly gc-stats './app.exe'` | GC time and pause latency (OCaml 5) |
| olly trace | tracing | macOS, Linux | ISC | `olly trace --format=json trace.json './app.exe'` | Chrome trace of runtime events |
| landmarks | tracing | macOS, Linux | MIT | Annotate with `[@landmark]`, run with `OCAML_LANDMARKS=on` | Time and allocation per landmark |
| memtrace | memory | Linux | MIT | Call `Memtrace.trace_if_requested ()`, run with `MEMTRACE=trace.ctf` | Sampled allocations, viewed in memtrace-viewer |
| core_bench | benchmark harness | macOS, Linux | MIT | `Bench.make_command [ Bench.Test.create ~name:"f" f ] \|> Command_unix.run` | ns/run, minor and major words allocated |

Samples: a loop printing `Unix.gettimeofday` (or `Mtime`) deltas, one per
line.

Traps: profile native code (`.exe`), not bytecode. Frame-pointer call
graphs need an OCaml switch built with frame pointers; otherwise use
`--call-graph dwarf`. Boxed floats in polymorphic code allocate.

### languages/Perl

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Devel::NYTProf | tracing | macOS, Linux | Artistic-1.0-Perl OR GPL-1.0-or-later | `perl -d:NYTProf app.pl` then `nytprofhtml` | Time per line, block and sub, as HTML |
| Benchmark | benchmark harness | macOS, Linux | Part of Perl | `perl -MBenchmark=cmpthese -e 'cmpthese(-3, { a => sub { ... }, b => sub { ... } })'` | Rate per second and % difference |
| Time::HiRes | benchmark harness | macOS, Linux | Part of Perl | `use Time::HiRes qw(time); my $t = time; ...; print time - $t, "\n"` | Seconds with µs resolution |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'perl app.pl'` | Run times |

Samples: a loop printing `Time::HiRes` deltas, one per line.

Traps: regex backtracking is a common hot spot (`use re 'debug'` shows
it). NYTProf's overhead is high on tiny subs.

### languages/PHP

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Excimer | CPU sampling | macOS, Linux | Apache-2.0 | `$p = new ExcimerProfiler(); $p->setPeriod(0.001); $p->start(); ...; $p->stop(); echo $p->getLog()->formatCollapsed();` | Collapsed stacks for a flame graph |
| SPX | CPU sampling | macOS, Linux | GPL-3.0 | `SPX_ENABLED=1 php app.php` | Flat profile on stderr; web UI for full reports |
| Xdebug profiler | tracing | macOS, Linux | Xdebug-1.03 | `php -d xdebug.mode=profile -d xdebug.output_dir=prof app.php` | `cachegrind.out.*`, read with `callgrind_annotate` |
| PHPBench | benchmark harness | macOS, Linux | MIT | `vendor/bin/phpbench run --report=aggregate` | Mode, mean, rstdev, memory per subject |
| `hrtime` | benchmark harness | macOS, Linux | Part of PHP | `$t = hrtime(true); ...; echo hrtime(true) - $t, "\n";` | ns |
| `memory_get_peak_usage` | memory | macOS, Linux | Part of PHP | `echo memory_get_peak_usage(true), "\n";` | Peak bytes |

Samples: a loop printing `hrtime(true)` deltas, one per line.

Traps: Xdebug slows everything even when not profiling; disable it when
timing. Turn on OPcache for CLI benchmarks (`-d opcache.enable_cli=1`)
if production uses it.

### languages/PowerShell

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Measure-Command | benchmark harness | macOS, Linux | Part of PowerShell | `Measure-Command { ./script.ps1 }` | TimeSpan of the block |
| Profiler module | tracing | macOS, Linux | MIT | `Trace-Script -ScriptBlock { & ./script.ps1 }` | Time per line and function |
| Stopwatch | benchmark harness | macOS, Linux | Part of .NET | `$sw = [Diagnostics.Stopwatch]::StartNew(); ...; $sw.Elapsed` | Elapsed time |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'pwsh -NoProfile -File script.ps1'` | Run times, start-up included |

Samples: this prints one value per line.

```powershell
1..30 | ForEach-Object { (Measure-Command { ./script.ps1 }).TotalMilliseconds }
```

Traps: `pwsh` start-up is slow; time inside the session. Appending to an
array with `+=` copies it every time; use a `List`. Measure-Command
discards the block's output.

### languages/Python

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| cProfile | tracing | macOS, Linux | Part of Python | `python -m cProfile -o prof.out app.py` then `python -c "import pstats; pstats.Stats('prof.out').sort_stats('cumulative').print_stats(25)"` | Calls, own and cumulative time per function |
| profiling.sampling | CPU sampling | Linux (macOS needs root) | Part of Python (3.15+) | `python -m profiling.sampling run --flamegraph -o prof.html app.py` | Flame graph HTML; `--gecko` for Firefox Profiler |
| `-X importtime` | tracing | macOS, Linux | Part of Python | `python -X importtime -c 'import app' 2> imports.log` | Own and cumulative µs per import |
| tracemalloc | memory | macOS, Linux | Part of Python | `python -X tracemalloc=25 app.py`, with `tracemalloc.take_snapshot().statistics('lineno')` in the code | Top allocation sites by size |
| timeit | benchmark harness | macOS, Linux | Part of Python | `python -m timeit -s 'from app import f' 'f()'` | Best time per loop |
| `-X perf` | CPU sampling | Linux | Part of Python (3.12+) | `perf record -g -- python -X perf app.py` | perf call graph with Python function names |
| pyinstrument | CPU sampling | macOS, Linux | BSD-3-Clause | `pyinstrument app.py` | Call tree of wall time |
| Scalene | CPU sampling | macOS, Linux | Apache-2.0 | `scalene run app.py` then `scalene view --cli` | Python vs native time, memory and copying per line |
| memray | memory | macOS, Linux | Apache-2.0 | `memray run -o mem.bin app.py` then `memray flamegraph mem.bin` | Allocation flame graph HTML |
| py-spy | CPU sampling | Linux | MIT | `py-spy record -o prof.svg -- python app.py` | Flame graph; `--idle` adds off-CPU time |
| pyperf | benchmark harness | macOS, Linux | MIT | `python -m pyperf timeit -s 'from app import f' 'f()' -o bench.json` | Calibrated runs; JSON with every value |
| pytest-benchmark | benchmark harness | macOS, Linux | BSD-2-Clause | `pytest --benchmark-only --benchmark-json=bench.json` | Min, mean, stddev per test |

Samples: a loop calling the function and printing
`time.perf_counter_ns()` deltas, one per line.

Traps: py-spy, and `profiling.sampling`, read another process's memory,
which needs root on macOS: use cProfile or pyinstrument there.
cProfile's per-call overhead exaggerates small functions. Measure with
the interpreter version production uses.

### languages/R

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Rprof | CPU sampling | macOS, Linux | Part of R | `Rprof("prof.out", memory.profiling = TRUE); f(); Rprof(NULL); summaryRprof("prof.out")` | Self and total time per function |
| profvis | CPU sampling | macOS, Linux | GPL-3.0-only | `profvis::profvis(f())` | Interactive flame graph with memory |
| bench | benchmark harness | macOS, Linux | MIT | `bench::mark(f(), iterations = 50)` | Min, median, allocations, GC counts |
| `system.time` | benchmark harness | macOS, Linux | Part of R | `system.time(f())` | User, system, elapsed |
| `tracemem` | memory | macOS, Linux | Part of R | `tracemem(x)` | A message each time `x` is copied |

Samples: `cat(as.numeric(bench::mark(f())$time[[1]]), sep = "\n")` prints
every iteration in seconds.

Traps: growing vectors in a loop copies them each time; preallocate or
vectorise. GC runs land in whichever iteration triggered them; bench
reports them.

### languages/Ruby

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| stackprof | CPU sampling | macOS, Linux | MIT | `StackProf.run(mode: :wall, out: 'stackprof.dump', raw: true) { work }` then `stackprof stackprof.dump --text` | Hot methods; `--method` for one |
| vernier | CPU sampling | macOS, Linux | MIT | `vernier run -- ruby app.rb` | Firefox Profiler profile with GVL, GC and idle time |
| ruby-prof | tracing | macOS, Linux | BSD-2-Clause | `ruby-prof app.rb` | Flat and graph profiles |
| memory_profiler | memory | macOS, Linux | MIT | `MemoryProfiler.report { work }.pretty_print` | Allocated and retained objects by gem, file and line |
| Benchmark | benchmark harness | macOS, Linux | Part of Ruby (bundled gem) | `Benchmark.realtime { work }` | Seconds |
| benchmark-ips | benchmark harness | macOS, Linux | MIT | `Benchmark.ips { \|x\| x.report('a') { work }; x.compare! }` | Iterations/s with error, and a comparison |

Samples: a loop printing `Process.clock_gettime(Process::CLOCK_MONOTONIC,
:nanosecond)` deltas, one per line.

Traps: compare with YJIT on and off (`ruby --yjit`), whichever production
uses. stackprof's `:cpu` mode misses I/O waits; use `:wall`. Rails start-up
is a separate measure from request time.

### languages/Rust

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `cargo build --profile profiling && samply record -- ./target/profiling/app` | Firefox Profiler profile |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record --call-graph dwarf -- ./target/release/app` | Call graph |
| cargo-flamegraph | CPU sampling | Linux | MIT OR Apache-2.0 | `cargo flamegraph --bin app` | `flamegraph.svg` |
| criterion | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `cargo bench` | Estimates and HTML report; raw samples in `target/criterion/<id>/new/sample.json` |
| divan | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `cargo bench` | Fastest, slowest, median and mean, with allocation counts |
| dhat-rs | memory | macOS, Linux | MIT OR Apache-2.0 | Add `let _p = dhat::Profiler::new_heap();` behind a feature, then run | `dhat-heap.json`, opened in DHAT's viewer |
| gungraun | benchmark harness | Linux | MIT OR Apache-2.0 | `cargo bench` | Instruction and cache counts under Valgrind: steady across runs |
| heaptrack | memory | Linux | LGPL-2.1-or-later | `heaptrack ./target/release/app` | Allocation hot spots |

Samples: `jq -r '[.iters, .times] | transpose[] | .[1] / .[0]'
target/criterion/<id>/new/sample.json` prints ns per iteration, one per
line.

Traps: add a `[profile.profiling]` that inherits `release` with
`debug = true`, or set `RUSTFLAGS='-C force-frame-pointers=yes'`.
cargo-flamegraph uses DTrace on macOS, which needs sudo; use samply. Wrap
inputs and outputs in `std::hint::black_box`.

### languages/Scala

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| JFR | CPU sampling | macOS, Linux | Part of the JDK | `java -XX:StartFlightRecording=duration=60s,filename=rec.jfr -jar app.jar` then `jfr view hot-methods rec.jfr` | Hot methods, allocation, GC |
| async-profiler | CPU sampling | macOS, Linux | Apache-2.0 | `asprof -d 30 -f flame.html <pid>` | Flame graph HTML |
| sbt-jmh | benchmark harness | macOS, Linux | Apache-2.0 | `sbt "Jmh/run -i 10 -wi 5 -f 2 -rf json -rff jmh.json"` | JMH scores and raw data |

Samples: `jq -r '.[0].primaryMetric.rawData[][]' jmh.json`.

Traps: JIT warm-up. Boxing in generic collections, and implicit
conversions, allocate in hot paths.

### languages/Swift

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| xctrace Time Profiler | CPU sampling | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Time Profiler' --launch -- .build/release/app` | `.trace` bundle |
| xctrace Allocations | memory | macOS (full Xcode) | Proprietary (free) | `xctrace record --template 'Allocations' --launch -- .build/release/app` | Allocations by stack |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `samply record -- .build/release/app` | Firefox Profiler profile |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- .build/release/app` | Call graph |
| `ContinuousClock` | benchmark harness | macOS, Linux | Part of Swift | `let d = ContinuousClock().measure { f() }` | Duration |
| XCTest `measure` | benchmark harness | macOS, Linux | Part of Swift | `measure(metrics: [XCTClockMetric()]) { f() }` | Average and relative stddev |
| package-benchmark | benchmark harness | macOS, Linux | Apache-2.0 | `swift package benchmark` | Percentiles for time, mallocs and more |

Samples: a loop printing `ContinuousClock().measure { f() }` per run,
converted to ns, one per line.

Traps: always build with `-c release`; debug builds are many times
slower. Retain/release traffic and existential (`any`) types are common
hot spots.

### languages/Zig

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| samply | CPU sampling | macOS, Linux | MIT OR Apache-2.0 | `zig build -Doptimize=ReleaseFast && samply record -- ./zig-out/bin/app` | Firefox Profiler profile |
| perf | CPU sampling | Linux | GPL-2.0-only | `perf record -g -- ./zig-out/bin/app` | Call graph |
| Valgrind Callgrind | tracing | Linux | GPL-3.0-or-later | `valgrind --tool=callgrind ./zig-out/bin/app` | Exact instruction counts per function |
| poop | benchmark harness | Linux | MIT | `poop './old' './new'` | Wall time, cycles, instructions, cache misses, compared |
| `std.time.Timer` | benchmark harness | macOS, Linux | Part of Zig | `var t = try std.time.Timer.start(); f(); const ns = t.read();` | ns |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json './zig-out/bin/app'` | Run times |

Samples: a loop printing `Timer.read()` per call, one per line.

Traps: Debug builds are slow and full of safety checks; measure the mode
you ship (`ReleaseFast` or `ReleaseSafe`). Use `std.mem.doNotOptimizeAway`
in microbenchmarks. poop uses perf events, so it's subject to
`perf_event_paranoid`.

### web/HTML

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Lighthouse | benchmark harness | macOS, Linux (needs Chrome) | Apache-2.0 | `lighthouse http://127.0.0.1:8080/ --output=json --output-path=lh.json --chrome-flags='--headless=new'` | Core Web Vitals and audits as JSON |
| Chrome DevTools Performance | tracing | macOS, Linux | Part of Chrome | Record a page load in the Performance panel | Main-thread flame chart, layout, paint, network |
| Performance API | tracing | Any browser | Part of the browser | `performance.mark('a'); ...; performance.measure('a-b', 'a')`, read with `PerformanceObserver` | Named timings from real page loads |

Samples: run Lighthouse several times and print
`jq '.audits["largest-contentful-paint"].numericValue' lh.json` for each,
one per line.

Traps: Lighthouse lab results vary run to run; take five or more runs.
Throttling settings change everything; keep them fixed. Large images,
render-blocking scripts and layout shifts are the usual causes.

### web/CSS

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| DevTools selector stats | tracing | macOS, Linux | Part of Chrome | Performance panel, with CSS selector stats turned on | Time and match attempts per selector during style recalculation |
| DevTools Coverage | memory | macOS, Linux | Part of Chrome | Coverage panel, reload the page | Unused bytes per stylesheet |
| Lighthouse | benchmark harness | macOS, Linux (needs Chrome) | Apache-2.0 | `lighthouse <url> --output=json --output-path=lh.json --chrome-flags='--headless=new'` | Unused CSS and render-blocking stylesheet audits |

Samples: as for `web/HTML`.

Traps: CSS cost is mostly render-blocking load and style recalculation on
large DOMs; animating layout properties (`width`, `top`) rather than
`transform` and `opacity` causes layout on every frame.

### web/Sass-SCSS

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| hyperfine | build timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json run.json 'sass src/main.scss out/main.css'` | Compile time |
| Output size | build timing | macOS, Linux | Part of the OS | `sass --style=compressed src/main.scss out/main.css && wc -c out/main.css` | Bytes shipped |

Samples: hyperfine JSON.

Traps: runtime cost is the generated CSS's (see `web/CSS`). `@extend` and
nested loops can multiply output size; check the compiled file.

### data/GraphQL

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| OpenTelemetry GraphQL instrumentation | tracing | macOS, Linux (Node.js servers) | Apache-2.0 | Register `@opentelemetry/instrumentation-graphql`, export to a local collector | Spans for parse, validate, execute and each resolver |
| Language profiler | CPU sampling | macOS, Linux | Varies | The server language's section | Hot resolvers |
| oha | benchmark harness | macOS, Linux | MIT | `oha -z 30s -c 32 -m POST -H 'content-type: application/json' -d '{"query":"{ items { id } }"}' http://127.0.0.1:4000/graphql` | Latency percentiles per query |
| k6 | benchmark harness | macOS, Linux | AGPL-3.0 | `k6 run graphql.js` | Scripted query mixes with percentiles |
| Database statement stats | query plan | macOS, Linux | Varies | `data/PostGreSQL` or `data/MySQL` sections | Queries per request |

Samples: as for [Services](#services).

Traps: N+1 resolvers (one database query per item) are the usual cause;
count queries per request, and batch with a DataLoader. Deeply nested
queries need depth or cost limits.

### data/ProtocolBuffers

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Language harness | benchmark harness | macOS, Linux | Varies | Benchmark encode and decode of real messages with the language's harness | ns per message, allocations |
| protoc | memory | macOS, Linux | BSD-3-Clause | `protoc --encode=pkg.Msg msg.proto < msg.txtpb \| wc -c` | Encoded size in bytes |

Samples: from the language's harness.

Traps: benchmark with real message shapes and sizes. Reflection-based and
JSON paths are much slower than generated code. In C++, arenas cut
allocation cost.

### data/SQL

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| PostgreSQL `EXPLAIN ANALYZE` | query plan | macOS, Linux | Part of PostgreSQL | `EXPLAIN (ANALYZE, BUFFERS) SELECT ...;` | Actual time and rows per plan node |
| MySQL `EXPLAIN ANALYZE` | query plan | macOS, Linux | Part of MySQL | `EXPLAIN ANALYZE SELECT ...;` | Actual time and rows per iterator (8.0.18+) |
| MariaDB `ANALYZE` | query plan | macOS, Linux | Part of MariaDB | `ANALYZE FORMAT=JSON SELECT ...;` | Estimated and actual rows and time |
| SQLite `EXPLAIN QUERY PLAN` | query plan | macOS, Linux | Part of SQLite | `EXPLAIN QUERY PLAN SELECT ...;` | Scans and index searches |

Samples: run the query N times from a client and print each round-trip
time, one per line.

Traps: find which engine the project uses and read its section. A plan on
a tiny development database differs from production; test with
realistic row counts and fresh statistics.

### data/PostGreSQL

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `EXPLAIN ANALYZE` | query plan | macOS, Linux | Part of PostgreSQL | `EXPLAIN (ANALYZE, BUFFERS, SETTINGS) SELECT ...;` | Actual time, rows, loops and buffer hits per node |
| psql `\timing` | benchmark harness | macOS, Linux | Part of PostgreSQL | `\timing on` | Round-trip ms per statement |
| pg_stat_statements | tracing | macOS, Linux | Part of PostgreSQL | `SELECT query, calls, mean_exec_time, total_exec_time FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;` | Statements by total time |
| auto_explain | query plan | macOS, Linux | Part of PostgreSQL | `LOAD 'auto_explain'; SET auto_explain.log_min_duration = '100ms'; SET auto_explain.log_analyze = on;` | Plans of slow statements in the server log |
| `track_io_timing` | I/O and syscalls | macOS, Linux | Part of PostgreSQL | `SET track_io_timing = on;` then `EXPLAIN (ANALYZE, BUFFERS)` | Time spent reading and writing blocks |
| pgbench | benchmark harness | macOS, Linux | Part of PostgreSQL | `pgbench -n -c 8 -j 4 -T 60 -P 10 -f bench.sql app` | TPS and latency; `--log` writes every transaction's time |

Samples: `pgbench --log` per-transaction latencies, or a client loop
printing round-trip times.

Traps: `EXPLAIN ANALYZE` runs the statement; wrap writes in `BEGIN; ...
ROLLBACK;`. pg_stat_statements needs `shared_preload_libraries` and a
restart; `LOAD` and `track_io_timing` need superuser: ask first. Run
`ANALYZE` so the planner has current statistics.

### data/MySQL

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `EXPLAIN ANALYZE` | query plan | macOS, Linux | Part of MySQL | `EXPLAIN ANALYZE SELECT ...;` | Actual time, rows and loops per iterator (8.0.18+) |
| `EXPLAIN FORMAT=JSON` | query plan | macOS, Linux | Part of MySQL | `EXPLAIN FORMAT=JSON SELECT ...;` | Estimated cost, access type, index use |
| sys schema | tracing | macOS, Linux | Part of MySQL | `SELECT * FROM sys.statement_analysis LIMIT 20;` | Statements by total latency, from the Performance Schema |
| Slow query log | tracing | macOS, Linux | Part of MySQL | `SET GLOBAL slow_query_log = ON; SET GLOBAL long_query_time = 0.1;` then `mysqldumpslow <log>` | Slow statements, grouped |
| mysqlslap | benchmark harness | macOS, Linux | Part of MySQL | `mysqlslap --concurrency=8 --iterations=10 --create-schema=app --query=bench.sql` | Average, min and max seconds |
| sysbench | benchmark harness | Linux, macOS | GPL-2.0-or-later | `sysbench oltp_read_write --mysql-db=app --tables=4 --table-size=100000 prepare` then `run` | TPS and latency percentiles |
| MariaDB `ANALYZE` | query plan | macOS, Linux | Part of MariaDB | `ANALYZE FORMAT=JSON SELECT ...;` | Estimated and actual rows and time |

Samples: a client loop printing round-trip times, one per line.

Traps: `EXPLAIN ANALYZE` runs the query. `SET GLOBAL` needs an admin
privilege: ask first. MariaDB has no `EXPLAIN ANALYZE`; use `ANALYZE`.

### data/SQLite

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `EXPLAIN QUERY PLAN` | query plan | macOS, Linux | Part of SQLite | `EXPLAIN QUERY PLAN SELECT ...;` | `SCAN` versus `SEARCH ... USING INDEX` per table |
| `.eqp on` | query plan | macOS, Linux | Part of SQLite | `.eqp on` in the `sqlite3` shell | The plan printed before every statement |
| `.timer on` | benchmark harness | macOS, Linux | Part of SQLite | `.timer on` in the `sqlite3` shell | Real, user and sys time per statement |
| `.scanstats on` | query plan | macOS, Linux | Part of SQLite | `.scanstats on` (needs a build with `SQLITE_ENABLE_STMT_SCANSTATUS`) | Loops and rows per plan step |
| sqlite3_analyzer | memory | macOS, Linux | Part of SQLite | `sqlite3_analyzer app.db` | Space used by each table and index |

Samples: a client loop printing round-trip times, one per line.

Traps: run `ANALYZE` so the planner has statistics. Many small writes
outside a transaction each pay for a sync; batch them. Check the journal
mode (`PRAGMA journal_mode;`).

### data/XML

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `xmllint --timing` | benchmark harness | macOS, Linux | MIT | `xmllint --timing --noout doc.xml` (add `--repeat` to parse 100 times) | Parse and free times |
| `xsltproc --profile` | tracing | macOS, Linux | MIT | `xsltproc --profile style.xsl doc.xml > /dev/null` | Time per template, on stderr |
| `xsltproc --timing` | benchmark harness | macOS, Linux | MIT | `xsltproc --timing style.xsl doc.xml > /dev/null` | Parse, transform and save times |
| Language profiler | CPU sampling | macOS, Linux | Varies | The language's section | Parser and XPath hot spots |

Samples: hyperfine JSON around `xmllint` or `xsltproc`.

Traps: building a DOM for a large document costs memory and time; stream
it (SAX or a pull parser). XPath `//` searches the whole tree.

### build/CMake

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| Configure profile | build timing | macOS, Linux | BSD-3-Clause | `cmake -S . -B build --profiling-format=google-trace --profiling-output=cmake.json` | Chrome trace of configure time per command |
| Ninja log | build timing | macOS, Linux | Apache-2.0 | `cmake -G Ninja -S . -B build && cmake --build build`, then `ninjatracing build/.ninja_log > trace.json` | Time per output |
| hyperfine | build timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --prepare 'cmake --build build --target clean' 'cmake --build build -j8'` | Clean and no-op build times |
| clang `-ftime-trace` | build timing | macOS, Linux | Apache-2.0 WITH LLVM-exception | `cmake -S . -B build -DCMAKE_CXX_FLAGS=-ftime-trace` | Per-file compile traces |
| ccache | build timing | macOS, Linux | GPL-3.0-or-later | `-DCMAKE_CXX_COMPILER_LAUNCHER=ccache`, then `ccache --show-stats` | Hit rate |

Samples: hyperfine JSON.

Traps: the Ninja generator builds faster than Unix Makefiles and gives a
timing log. A configure step that re-runs on every build (globbing,
`execute_process`) makes no-op builds slow.

### build/Linker-GNU-ld

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `ld --stats` | build timing | Linux | GPL-3.0-or-later | `cc ... -Wl,--stats` | Link time and memory, on stderr |
| lld `--time-trace` | build timing | macOS, Linux | Apache-2.0 WITH LLVM-exception | `cc -fuse-ld=lld ... -Wl,--time-trace` | Chrome trace of the link, for comparison |
| hyperfine | build timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json link.json 'cc -o app *.o'` | Link time |
| Link map | memory | Linux | GPL-3.0-or-later | `cc ... -Wl,-Map=app.map` | Size and placement of every section and symbol |
| `LD_DEBUG=statistics` | boot timing | Linux (glibc) | LGPL-2.1-or-later | `LD_DEBUG=statistics ./app` | Time the dynamic linker spent relocating at start-up |

Samples: hyperfine JSON.

Traps: `--gc-sections` with `-ffunction-sections` shrinks the binary;
lazy versus immediate binding (`-z now`) moves cost between start-up and
first call. Static archive order changes what gets pulled in.

### build/Make

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| hyperfine | build timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --prepare 'make clean' --export-json clean.json 'make -j8'` | Clean build time; without `--prepare`, no-op time |
| `make --trace` | build timing | macOS (GNU make 4+), Linux | GPL-3.0-or-later | `make --trace -j8 > trace.log` | Why each target was rebuilt |
| remake | build timing | Linux, macOS | GPL-3.0-or-later | `remake --profile -j8` | `callgrind.out.<pid>`: time per target |
| `make -p` | build timing | macOS, Linux | GPL-3.0-or-later | `make -pn > db.txt` | The full rule database, to find expensive pattern rules |

Samples: hyperfine JSON.

Traps: macOS `/usr/bin/make` is GNU make 3.81, with no `--trace`.
`$(shell ...)` and `:=` with `$(wildcard ...)` run on every invocation,
which slows no-op builds. Recursive make hides parallelism.

### tools/Docker

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| BuildKit plain progress | build timing | macOS, Linux | Apache-2.0 | `docker build --progress=plain --no-cache . 2>&1 \| tee build.log` | Time per step |
| `docker buildx history` | build timing | macOS, Linux | Apache-2.0 | `docker buildx history ls`; `docker buildx history inspect <ref>` | Duration and cache use of past builds |
| Container start time | boot timing | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json start.json 'docker run --rm app:dev true'` | Start-to-exit time |
| `docker stats` | memory | macOS, Linux | Apache-2.0 | `docker stats --no-stream` | CPU %, memory, network and block I/O per container |
| Image size | memory | macOS, Linux | Apache-2.0 | `docker image ls app`; `docker image history app:dev` | Image size, and size per layer |

Samples: hyperfine JSON.

Traps: Docker Desktop on macOS runs a Linux VM, so bind-mount I/O is slow
and numbers don't match Linux hosts. `--platform linux/amd64` on Apple
Silicon is emulated; never time it. perf inside a container needs extra
capabilities: profile with the language's own tools there. Order layers so
dependency installs stay cached.

### tools/GitHub-Actions

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `gh run list` | build timing | macOS, Linux | MIT | `gh run list --workflow ci.yml --limit 20 --json databaseId,startedAt,updatedAt,conclusion` | Start and end of recent runs |
| `gh run view` | build timing | macOS, Linux | MIT | `gh run view <id> --json jobs` | Start and end of every job and step |

Samples: run durations in seconds, one per line, worked out from
`startedAt` and `updatedAt` with `jq`.

Traps: runner timings vary a lot; compare many runs. Separate queue time
from run time. Cache hits and misses change totals. Don't trigger runs
without asking: they use the user's minutes.

### tools/Nix

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| `NIX_SHOW_STATS` | tracing | macOS, Linux | LGPL-2.1-or-later | `NIX_SHOW_STATS=1 nix eval --no-eval-cache .#packages.<system>.default.drvPath` | Evaluation statistics as JSON on stderr: time, thunks, memory |
| Eval profiler | CPU sampling | macOS, Linux | LGPL-2.1-or-later | `nix-instantiate '<nixpkgs>' -A hello --eval-profiler flamegraph` (Nix 2.30+) | `nix.profile` collapsed stacks, for inferno or `flamegraph.pl` |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --export-json eval.json 'nix eval --no-eval-cache --raw .#x'` | Evaluation time |
| Rebuild time | build timing | macOS, Linux | LGPL-2.1-or-later | `hyperfine --runs 3 'nix build --rebuild .#default'` | Build time without substitutes |
| Closure size | memory | macOS, Linux | LGPL-2.1-or-later | `nix path-info -rSh .#default` | Size of the closure |

Samples: hyperfine JSON.

Traps: the flake evaluation cache hides evaluation time; use
`--no-eval-cache`. A build that downloads from a binary cache measures the
network.

### tools/OpenTofu

| Tool | Kind | Platforms | Licence | Command | Output |
| --- | --- | --- | --- | --- | --- |
| hyperfine | benchmark harness | macOS, Linux | MIT OR Apache-2.0 | `hyperfine --runs 5 'tofu plan -refresh=false -lock=false -input=false'` | Plan time without refreshing provider state |
| `TF_LOG` | tracing | macOS, Linux | MPL-2.0 | `TF_LOG=trace tofu plan 2> tofu.log` | Timestamped log, showing slow provider calls |
| OpenTelemetry traces | tracing | macOS, Linux | MPL-2.0 | `OTEL_TRACES_EXPORTER=otlp OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 tofu plan` (1.10+, experimental) | Spans per operation in a local OTLP backend such as Jaeger |

Samples: hyperfine JSON.

Traps: `plan` calls real cloud APIs with the user's credentials; ask
before running it, and never `apply`. API latency and rate limits
dominate; `-parallelism=n` changes how many calls run at once.

No runtime profile: `data/TOML`, `data/YAML`.

## Sources

System-level:

- [perf wiki](https://perfwiki.github.io/main/) and
  [perf security and `perf_event_paranoid`](https://www.kernel.org/doc/html/latest/admin-guide/perf-security.html)
- [samply](https://github.com/mstange/samply)
- `sample`, `xctrace`, `leaks`, `heap`, `vmmap`, `time` and `fs_usage`:
  their macOS man pages (`man xctrace` needs full Xcode)
- [GNU time](https://www.gnu.org/software/time/)
- [Valgrind user manual](https://valgrind.org/docs/manual/manual.html)
- [heaptrack](https://github.com/KDE/heaptrack)
- [strace](https://strace.io/)
- [ltrace](https://gitlab.com/cespedes/ltrace)
- [inferno](https://github.com/jonhoo/inferno)
- [FlameGraph](https://github.com/brendangregg/FlameGraph)
- [hyperfine](https://github.com/sharkdp/hyperfine)
- [speedscope](https://github.com/jlfwong/speedscope)
- [Perfetto](https://perfetto.dev/docs/)
- [GNU make manual](https://www.gnu.org/software/make/manual/make.html)
- [remake](https://remake.readthedocs.io/)
- [Ninja manual](https://ninja-build.org/manual.html)
- [ninjatracing](https://github.com/nico/ninjatracing)
- [Clang command-line reference](https://clang.llvm.org/docs/ClangCommandLineReference.html)
- [ClangBuildAnalyzer](https://github.com/aras-p/ClangBuildAnalyzer)
- [GCC developer options](https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html)
- [ccache](https://ccache.dev/documentation.html)
- [Cargo timings](https://doc.rust-lang.org/cargo/reference/timings.html)
- [Docker Build](https://docs.docker.com/build/),
  [`docker buildx build`](https://docs.docker.com/reference/cli/docker/buildx/build/)
  and [`docker buildx history`](https://docs.docker.com/reference/cli/docker/buildx/history/)
- [Bazel JSON trace profile](https://bazel.build/advanced/performance/json-trace-profile)
- [cmake(1)](https://cmake.org/cmake/help/latest/manual/cmake.1.html)
- [Gradle command-line interface](https://docs.gradle.org/current/userguide/command_line_interface.html)
- [systemd-analyze](https://www.freedesktop.org/software/systemd/man/latest/systemd-analyze.html)
- [Kernel parameters](https://www.kernel.org/doc/html/latest/admin-guide/kernel-parameters.html)
- [systemd-bootchart](https://github.com/systemd/systemd-bootchart)
- [QEMU invocation](https://www.qemu.org/docs/master/system/invocation.html)
- [oha](https://github.com/hatoo/oha)
- [vegeta](https://github.com/tsenart/vegeta)
- [k6](https://grafana.com/docs/k6/latest/)
- [wrk](https://github.com/wg/wrk)
- [ab](https://httpd.apache.org/docs/current/programs/ab.html)
- [curl `--write-out`](https://curl.se/docs/manpage.html)

Languages, formats and tools:

- [llvm-mca](https://llvm.org/docs/CommandGuide/llvm-mca.html)
- [QEMU TCG plugins](https://www.qemu.org/docs/master/about/emulation.html)
- [GNU Bash manual](https://www.gnu.org/software/bash/manual/bash.html)
- [gprof](https://sourceware.org/binutils/docs/gprof/)
- [Tracy](https://github.com/wolfpld/tracy)
- [Google Benchmark](https://github.com/google/benchmark)
- [nanobench](https://nanobench.ankerl.com/)
- [Catch2 benchmarks](https://github.com/catchorg/Catch2/blob/devel/docs/benchmarks.md)
- [gperftools](https://github.com/gperftools/gperftools)
- [XCTest performance tests](https://developer.apple.com/documentation/xctest/performance-tests)
- [JFR tool](https://docs.oracle.com/en/java/javase/21/docs/specs/man/jfr.html)
  and [java launcher](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html)
- [async-profiler](https://github.com/async-profiler/async-profiler)
- [JMH](https://github.com/openjdk/jmh)
- [JMH Gradle plugin](https://github.com/melix/jmh-gradle-plugin)
- [sbt-jmh](https://github.com/sbt/sbt-jmh)
- [kotlinx-benchmark](https://github.com/Kotlin/kotlinx-benchmark)
- [criterium](https://github.com/hugoduncan/criterium)
- [clj-async-profiler](https://github.com/clojure-goes-fast/clj-async-profiler)
- [GnuCOBOL](https://gnucobol.sourceforge.io/)
- [dotnet-trace](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-trace),
  [dotnet-counters](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-counters)
  and [dotnet-gcdump](https://learn.microsoft.com/en-us/dotnet/core/diagnostics/dotnet-gcdump)
- [BenchmarkDotNet](https://benchmarkdotnet.org/)
- [Dart DevTools CPU profiler](https://docs.flutter.dev/tools/devtools/cpu-profiler)
  and [`dart run`](https://dart.dev/tools/dart-run)
- [benchmark_harness](https://pub.dev/packages/benchmark_harness)
- [Erlang profiling guide](https://www.erlang.org/doc/system/profiling.html),
  [tprof](https://www.erlang.org/doc/apps/tools/tprof.html),
  [eprof](https://www.erlang.org/doc/apps/tools/eprof.html),
  [fprof](https://www.erlang.org/doc/apps/tools/fprof.html)
  and [BeamAsm and perf](https://www.erlang.org/doc/apps/erts/beamasm.html)
- [mix profile.tprof](https://hexdocs.pm/mix/Mix.Tasks.Profile.Tprof.html)
- [Benchee](https://github.com/bencheeorg/benchee)
- [GCC instrumentation options](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)
- [Go diagnostics](https://go.dev/doc/diagnostics),
  [runtime/pprof](https://pkg.go.dev/runtime/pprof),
  [testing](https://pkg.go.dev/testing)
  and [benchstat](https://pkg.go.dev/golang.org/x/perf/cmd/benchstat)
- [GHC profiling](https://downloads.haskell.org/ghc/latest/docs/users_guide/profiling.html)
  and [RTS options](https://downloads.haskell.org/ghc/latest/docs/users_guide/runtime_control.html)
- [eventlog2html](https://mpickering.github.io/eventlog2html/)
- [tasty-bench](https://github.com/Bodigrim/tasty-bench)
- [criterion (Haskell)](https://github.com/haskell/criterion)
- [Node.js CLI options](https://nodejs.org/api/cli.html)
  and [profiling Node.js](https://nodejs.org/en/learn/getting-started/profiling)
- [0x](https://github.com/davidmarkclements/0x)
- [mitata](https://github.com/evanwashere/mitata)
- [tinybench](https://github.com/tinylibs/tinybench)
- [deno bench](https://docs.deno.com/runtime/reference/cli/bench/)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance),
  [selector stats](https://developer.chrome.com/docs/devtools/performance/selector-stats)
  and [Coverage](https://developer.chrome.com/docs/devtools/coverage)
- [TypeScript performance wiki](https://github.com/microsoft/TypeScript/wiki/Performance)
- [Julia profiling](https://docs.julialang.org/en/v1/manual/profile/)
- [BenchmarkTools.jl](https://juliaci.github.io/BenchmarkTools.jl/stable/)
- [PProf.jl](https://github.com/JuliaPerf/PProf.jl)
- [LuaJIT profiler](https://luajit.org/ext_profiler.html)
  and [Lua 5.4 manual](https://www.lua.org/manual/5.4/manual.html)
- [OCaml profiling](https://ocaml.org/docs/profiling)
- [runtime_events_tools (olly)](https://github.com/tarides/runtime_events_tools)
- [landmarks](https://github.com/LexiFi/landmarks)
- [memtrace](https://github.com/janestreet/memtrace)
- [core_bench](https://github.com/janestreet/core_bench)
- [Devel::NYTProf](https://metacpan.org/pod/Devel::NYTProf)
  and [Benchmark (Perl)](https://perldoc.perl.org/Benchmark)
- [Excimer](https://github.com/wikimedia/php-excimer)
- [SPX](https://github.com/NoiseByNorthwest/php-spx)
- [Xdebug profiler](https://xdebug.org/docs/profiler)
- [PHPBench](https://phpbench.readthedocs.io/)
- [Measure-Command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/measure-command)
- [Profiler (PowerShell)](https://github.com/nohwnd/Profiler)
- [Python profilers](https://docs.python.org/3/library/profile.html),
  [profiling.sampling](https://docs.python.org/3.15/library/profiling.sampling.html),
  [tracemalloc](https://docs.python.org/3/library/tracemalloc.html),
  [command-line options](https://docs.python.org/3/using/cmdline.html)
  and [perf support](https://docs.python.org/3/howto/perf_profiling.html)
- [pyinstrument](https://pyinstrument.readthedocs.io/)
- [Scalene](https://github.com/plasma-umass/scalene)
- [memray](https://bloomberg.github.io/memray/)
- [py-spy](https://github.com/benfred/py-spy)
- [pyperf](https://pyperf.readthedocs.io/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [Rprof](https://stat.ethz.ch/R-manual/R-devel/library/utils/html/Rprof.html)
- [profvis](https://profvis.r-lib.org/)
- [bench (R)](https://bench.r-lib.org/)
- [stackprof](https://github.com/tmm1/stackprof)
- [vernier](https://github.com/jhawthorn/vernier)
- [ruby-prof](https://github.com/ruby-prof/ruby-prof)
- [memory_profiler](https://github.com/SamSaffron/memory_profiler)
- [benchmark (Ruby)](https://github.com/ruby/benchmark)
- [benchmark-ips](https://github.com/evanphx/benchmark-ips)
- [The Rust Performance Book: profiling](https://nnethercote.github.io/perf-book/profiling.html)
- [cargo-flamegraph](https://github.com/flamegraph-rs/flamegraph)
- [criterion.rs](https://bheisler.github.io/criterion.rs/book/)
- [divan](https://github.com/nvzqz/divan)
- [dhat-rs](https://docs.rs/dhat)
- [Gungraun](https://gungraun.github.io/gungraun/)
- [package-benchmark](https://github.com/ordo-one/benchmark)
- [poop](https://github.com/andrewrk/poop)
- [Zig documentation](https://ziglang.org/documentation/master/)
- [Lighthouse](https://github.com/GoogleChrome/lighthouse)
- [Performance API](https://developer.mozilla.org/en-US/docs/Web/API/Performance_API)
- [Dart Sass CLI](https://sass-lang.com/documentation/cli/dart-sass/)
- [OpenTelemetry GraphQL instrumentation](https://github.com/open-telemetry/opentelemetry-js-contrib/tree/main/packages/instrumentation-graphql)
- [DataLoader](https://github.com/graphql/dataloader)
- [Protocol Buffers](https://protobuf.dev/)
- PostgreSQL: [EXPLAIN](https://www.postgresql.org/docs/current/sql-explain.html),
  [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html),
  [auto_explain](https://www.postgresql.org/docs/current/auto-explain.html)
  and [pgbench](https://www.postgresql.org/docs/current/pgbench.html)
- MySQL: [EXPLAIN](https://dev.mysql.com/doc/refman/8.4/en/explain.html),
  [Performance Schema](https://dev.mysql.com/doc/refman/8.4/en/performance-schema.html),
  [slow query log](https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html)
  and [mysqlslap](https://dev.mysql.com/doc/refman/8.4/en/mysqlslap.html)
- [MariaDB ANALYZE](https://mariadb.com/kb/en/analyze-statement/)
- [sysbench](https://github.com/akopytov/sysbench)
- SQLite: [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html),
  [command-line shell](https://www.sqlite.org/cli.html)
  and [sqlite3_analyzer](https://www.sqlite.org/sqlanalyze.html)
- [xmllint](https://gnome.pages.gitlab.gnome.org/libxml2/xmllint.html)
  and [xsltproc](https://gnome.pages.gitlab.gnome.org/libxslt/xsltproc.html)
- [GNU ld options](https://sourceware.org/binutils/docs/ld/Options.html)
- [lld](https://lld.llvm.org/)
- [`gh run view`](https://cli.github.com/manual/gh_run_view)
  and [`gh run list`](https://cli.github.com/manual/gh_run_list)
- [Nix eval profiler](https://nix.dev/manual/nix/latest/advanced-topics/eval-profiler)
  and [Nix environment variables](https://nix.dev/manual/nix/latest/command-ref/env-common)
- [OpenTofu tracing](https://opentofu.org/docs/internals/tracing/)
  and [debugging](https://opentofu.org/docs/internals/debugging/)
