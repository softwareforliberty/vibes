---
name: test-driven-development
description: >-
  Writes code test-first using the red-green-refactor cycle. Use when adding a
  feature or new behaviour, fixing a bug, or changing code that needs a safety
  net, in any language.
---

# Test-Driven Development

Write a failing test, make it pass with the simplest code that works, then
clean up. Repeat in small steps. Every piece of behaviour is driven by a test
that was seen to fail first, so the tests prove what the code does and protect
it from regressions.

## When to use this skill

- **New behaviour:** a feature, an endpoint, a function, a rule.
- **Bug fixes:** reproduce the bug with a failing test before touching the
  code.
- **Risky changes:** before refactoring code that has no tests, add tests that
  pin down its current behaviour.

Skip it only for throwaway spikes. When a spike turns into real code, rewrite
it test-first.

## Before you start

1. **Find how the project runs its tests.** Look for the test command in the
   README, the build file or CI config. For the standard test, coverage and
   lint tools of each language, see that language's `tools.md` in
   [`lang/`](../../lang/), for example
   [`lang/Python/tools.md`](../../lang/Python/tools.md).
2. **Run the existing suite once** and confirm it passes. If it doesn't, stop
   and report it: you can't tell your failures from existing ones.
3. **Write a test list.** Break the task into small behaviours, one line each,
   ordered from simplest to hardest. Edge cases and error cases are entries
   too. Add to the list as you discover more; don't try to finish it up front.

## The cycle

Work through the test list one entry at a time. Each pass through the cycle
should take minutes, not hours.

### 1. Red: write one failing test

- Write a single test for the next behaviour on the list, and nothing else.
  Write it as if the code already exists, so it shows the interface you want
  callers to use.
- **Run it and watch it fail.** Check that it fails for the expected reason,
  for example an assertion about the missing behaviour, not a typo, an import
  error or a broken fixture. A test you've never seen fail might not be able
  to fail at all.
- If it passes straight away, the behaviour already exists or the test is
  wrong. Find out which before going on.

### 2. Green: make it pass

- Write the **simplest code that makes the test pass**, even if it's naive.
  Hard-coding a value is fine when only one test needs it; the next test will
  force the general version.
- Don't add behaviour no test asks for. If you think of something else the
  code should do, add it to the test list instead.
- Run the test, then the rest of the relevant suite. Everything must pass
  before you move on.

### 3. Refactor: clean up while green

- Improve names, remove duplication and simplify, in both the code and the
  tests. Follow the language's `coding-style.md` and `idioms.md` in `lang/`.
- Change structure only, never behaviour. Run the tests after each small
  step, so a failure points at the step that caused it.
- Stop refactoring when the code is clear. Then pick the next test from the
  list.

### 4. Commit at green

Commit whenever the tests are green and the change is a complete step, usually
after green or after a refactor. Each commit holds a test together with the
code that makes it pass. Never commit with failing tests. See the
[atomic commits](../atomic-commits/SKILL.md) skill for how to shape each
commit.

## Fixing a bug

1. Write a test that reproduces the bug and fails. Name it after the correct
   behaviour, not the bug: `test_total_includes_shipping`, not
   `test_bug_123`.
2. Confirm it fails the way the bug report describes.
3. Fix the code until the test passes, then run the full suite.
4. Commit the test and the fix together, so the history shows both.

## Writing good tests

- **One behaviour per test.** A test should have one reason to fail. Several
  assertions are fine when they check the same behaviour.
- **Name the behaviour.** The name says what the code does in which
  situation: `returns_empty_list_when_no_orders_match`. A failing test's name
  should explain the failure.
- **Arrange, act, assert.** Set up the inputs, run the one thing under test,
  then check the result, in that order and with no logic in between.
- **Test through the public interface.** Test what callers see, not private
  functions or internal state. Tests tied to the implementation break on
  every refactor and stop being a safety net.
- **Keep tests fast and deterministic.** No real network, no sleeping, no
  dependence on the clock, the order tests run in, or shared state. Inject
  the clock, random source and other collaborators so tests can control them.
- **Fake only at the boundaries.** Replace slow or external things such as the
  network, the file system or a payment service. Don't mock code you own just
  to isolate a function: test the real collaborators together.
- **Keep test code clean.** Tests follow the same style guide as production
  code. Extract helpers for repeated setup, but keep each test readable on
  its own.

## When a test is hard to write

Difficulty writing a test is feedback about the design, not a reason to skip
the test.

- **Too much setup** means the code has too many dependencies. Split it, or
  pass the dependencies in.
- **Can't observe the result** means the code hides its effect. Return a
  value, or expose the effect through a collaborator you can replace in the
  test.
- **Needs a private function** means that function is its own unit. Move it
  somewhere it can be tested publicly.

## Anti-patterns

- **Writing tests after the code.** They tend to confirm what the code does,
  not what it should do, and are never seen to fail.
- **Changing a test to make it pass.** Only change a test when the requirement
  changed. Otherwise fix the code.
- **Big steps.** A test that needs an hour of code before it passes was too
  big. Back out, and write a smaller test.
- **Skipping the refactor step.** The code works but gets harder to change
  with every cycle.
- **Chasing coverage.** Coverage shows what isn't tested; it doesn't prove
  what is. Write tests for behaviour, and let coverage follow. The `lang/`
  tools set an 80% branch-coverage minimum as a floor, not a goal.

## Checklist

Before saying the work is done:

- [ ] Every behaviour on the test list has a test, and each was seen to fail
      before it passed.
- [ ] The full test suite passes, not just the new tests.
- [ ] The language's linters and coverage check pass (see its `tools.md`).
- [ ] No test was weakened or deleted to get to green.
- [ ] Each commit pairs tests with the code they cover, and every commit is
      green.
