# Embedded Systems Architecture

How to structure firmware and other embedded software on microcontrollers
and small processors, on bare metal or on a real-time operating system
(RTOS) such as FreeRTOS or Zephyr. Read the
[rules for all software](README.md) first: a core of logic with thin edges,
dependencies pointing inward, and one owner for each piece of state. This
guide builds on them.

Embedded software runs on one board, often for years without a restart,
with kilobytes of memory, nobody watching, and deadlines set by the physical
world. It can't stop with an error message: when something goes wrong, it
must put the hardware in a safe state and recover by itself. Its natural
shape is the device's behaviour as state machines at the core, a driver for
each device, and a thin layer over the chip's registers, with every resource
sized when it's built.

The [OS components guide](os-components.md) covers kernels and drivers on
full operating systems. Its rules for
[execution contexts](os-components.md#execution-contexts) and
[ownership](os-components.md#ownership-and-resources) apply here too. Where
the code builds on an RTOS or a vendor's framework, follow its driver model.

## Scale the structure to the task

- **A small device with one job,** such as a sensor that sends a reading: a
  loop in `main`, a few drivers, and the logic in plain functions.
- **A device with several jobs at once, deadlines, updates in the field or
  safety requirements:** everything in this guide.

At every size, keep the logic free of registers and vendor headers, so it
builds and runs its tests on the development machine.

## The layers

```text
              board support: pins, clocks and wiring
                    │ builds and connects
                    ▼
application ─▶ services ─▶ drivers ─▶ hardware abstraction ─▶ registers
     │             │          │
     └─────────────┴──────────┴─────▶ OS abstraction ─▶ RTOS, or none
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Application | The device's behaviour: state machines and rules | Services, driver interfaces, the OS abstraction | Registers, vendor headers, the RTOS's own API |
| Services | Shared functions such as storage, a protocol or power management | Driver interfaces, the OS abstraction | Registers, the application |
| Driver | One device, such as a sensor or a flash chip | Hardware abstraction interfaces, the OS abstraction | Other drivers, a particular board |
| Hardware abstraction | The chip's peripherals: pins, UART, SPI, I2C, timers, ADC and DMA | Vendor headers, registers | Drivers, the application |
| Board support | Which pins and peripherals this board uses, and starting it up | Hardware abstraction, drivers | Application logic |
| OS abstraction | Tasks, queues, timers and locks | The RTOS, or nothing on bare metal | Anything above it |

### Application

The application is the device's behaviour, written against the interfaces
below it, so the same logic runs on a new chip, a new board, and the
development machine under test.

### Drivers

A driver handles one device, such as a temperature sensor on an I2C bus.

- **It uses the bus through the hardware abstraction's interface,** so the
  same driver works on any bus instance and any chip.
- **Its state is a struct the caller provides,** not a global, so a board
  can have two of the same sensor.
- **It returns errors,** such as a timeout or a bad checksum, and never
  hangs. Every wait for hardware has a timeout.

### Hardware abstraction and board support

The hardware abstraction layer (HAL) is a thin set of interfaces over the
chip's peripherals, implemented for each chip family, usually on the
vendor's library. It holds no device logic, and register access happens
nowhere else.

Board support says what's on this board: which pins go where, the clocks,
and which driver sits on which bus. It's the one place that builds and wires
everything at startup, like `main` in the
[shared rules](README.md#a-core-and-its-edges). Each board revision has its
own, chosen by the build.

### The OS abstraction

The application and services use tasks, queues, timers and locks through a
small interface, so the logic runs on the host, and can move between an
RTOS and bare metal. Where a project is sure to stay on one RTOS, services
may use its API directly, but the application's logic never does.

## Memory

- **No heap, or a bounded one.** Allocate statically, or once at startup
  from a fixed pool, and never free. A heap that's used and freed at run
  time fragments, and fails months after the device ships.
- **Create RTOS objects statically,** such as with FreeRTOS's static
  allocation functions, so the build accounts for every byte.
- **Size every buffer and queue for the worst case,** and decide what
  happens when one is full, so an overflow is a choice, not corruption.
- **Measure each task's stack** with the RTOS's high-water mark, and keep a
  margin. No recursion, and no large arrays on the stack.

## Interrupts

- **Handlers do the minimum:** clear the source, capture the data, and wake
  a task. The rest runs in a task or work queue, such as through a FreeRTOS
  task notification or a Zephyr work item, or in the main loop.
- **Handlers call only what's safe in interrupt context,** such as
  FreeRTOS's `FromISR` functions, and never block or wait.
- **Data shared with a handler** goes through a single-producer,
  single-consumer ring buffer, an atomic, or a short critical section.
  `volatile` alone doesn't make an access atomic.

## Real time

- **Write down every deadline,** such as "the motor stops within 2 ms of the
  limit switch", and test it on the hardware.
- **Set priorities by deadline,** with the shortest deadline or period
  highest, so slow work never holds up urgent work.
- **Avoid priority inversion.** A lock shared by tasks of different
  priorities is a mutex with priority inheritance, or is replaced by a queue
  to one owning task.
- **Measure the worst case** under the heaviest load. A deadline is missed
  in the worst case, never in the average.

## Tasks and queues, or a loop

- **A loop in `main`** suits a device with a few jobs and loose timing.
  Each job is a function that runs a short step and returns, never blocking.
- **An RTOS** suits several jobs with different deadlines. Each task has one
  job and owns its state, and tasks talk through queues and notifications
  rather than shared data under locks. Add a task only for a separate
  deadline or a blocking wait, not one per driver.

## State machines

Model the device's behaviour, and each protocol, as explicit state machines:
a state type, a set of events, and one function that takes a state and an
event and returns the next state and the actions to take. Every pair of
state and event is handled, even if only by ignoring it. The machine is then
a pure function, tested on the host for every transition, and a log of its
events can replay a failure from the field.

## Power

- **One power manager decides when to sleep,** so the policy lives in one
  place. Drivers suspend and resume their device when told, restoring
  settings that deep sleep can lose.
- **Sleep whenever there's nothing to do,** such as with the RTOS's tickless
  idle, and wake on interrupts rather than polling, which drains the
  battery.

## Watchdogs

- **Enable the hardware watchdog in production,** clocked independently of
  the main clock where the chip allows, so a clock failure can't stop it.
- **Feed it from one place,** and only when every task has reported in
  recently, so a stuck task resets the device. Never feed it from a timer
  interrupt, which keeps running after the tasks have stopped.
- **Record why the device reset,** from the chip's reset-cause register.

## Faults and safe states

- **Define the safe state** of each output, such as a motor off or a valve
  closed. Startup and the fault handler both drive outputs to it first.
- **On an unrecoverable fault,** such as a failed assertion, a hard fault or
  a stack overflow, make the outputs safe, save the cause to memory that
  survives a reset, and reset.
- **Recover what can be recovered,** such as a sensor that stops answering:
  retry, reset it, then carry on without it and report the failure.
- **Count resets.** A device that keeps resetting stays in a minimal safe
  mode, rather than looping forever.

## Bootloaders and updates

- **The bootloader is small and rarely changes,** because a bad one can't
  be fixed in the field. It checks the application image, starts it, and
  installs updates.
- **Verify every image before running it,** with a signature checked
  against a key built into the bootloader, so a corrupt or forged image
  never runs.
- **Keep two slots,** so an update is written beside the running image, and
  losing power at any moment leaves a bootable one.
- **Roll back a bad update.** The new image boots on trial, and confirms
  itself only after it passes its own checks. If it doesn't, the next reset
  goes back to the old one. [MCUboot](https://docs.mcuboot.com/) works this
  way, and can also refuse a downgrade to an older version.

## Configuration in flash

- **Store settings as versioned records with a checksum,** and migrate old
  versions at boot, so new firmware reads what the old one wrote.
- **Survive power loss during a write:** write a new copy, then mark it
  current, keeping the old copy until then. Use the RTOS's storage, such as
  Zephyr's settings subsystem, where it has one.
- **Fall back to built-in defaults** when no valid record exists, and limit
  writes, because flash wears out.

## Layout

```text
app/                 the application: state machines and rules
services/            storage, protocols, power management
drivers/<device>/    one directory per device
hal/<chip>/          one directory per chip family
boards/<board>/      pins, clocks and wiring for each board
os/                  the OS abstraction, with an RTOS and a host version
bootloader/
tests/
├── host/            unit tests built for the development machine
└── hil/             hardware-in-the-loop tests
```

## Enforce it

- **Build the layers as separate libraries,** with vendor headers on the
  include path only for `hal/` and `boards/`, so a register access in the
  application fails to build.
- **Build the application and drivers for the host** in every check, which
  proves they don't depend on the chip, and fail the build when RAM or flash
  use passes a set limit.
- **Typical rules for checks in `scripts/check`:** only `hal/` and `boards/`
  include vendor headers; drivers don't include other drivers; nothing
  allocates after startup. Follow a coding standard such as MISRA C where
  the product's domain requires one.

## Testing

| Part | Test with |
| --- | --- |
| Application, state machines and services | Unit tests on the host, with fake drivers and OS abstraction |
| Drivers | Host tests against a fake bus that behaves as the datasheet says |
| The whole firmware | An emulator, such as QEMU or [Renode](https://renode.io/), in CI |
| Timing, power and real peripherals | Hardware-in-the-loop tests on real boards |

- **Host tests are most of the suite.** A C test framework such as Unity,
  with CMock to generate fakes from headers, runs them in seconds.
- **Hardware-in-the-loop tests** flash a real board, and drive and measure
  it from a test rig, on every release candidate.
- **Test the failure paths:** a sensor that stops answering, a full queue,
  power lost during a flash write or an update, and a watchdog reset.
