---
name: prototype
description: >-
  Builds a throwaway prototype to answer one design question you can't
  judge in words: a single HTML file to click through a state model's
  scenarios, or several structurally different variants of a screen to
  flip between on the real page. Records the answer for the spec, with the
  confirmed scenarios as examples the build tests. The vibe workflow
  offers it for such a decision.
argument-hint: "<the question>"
disable-model-invocation: true
---

# Prototype: answer one question by trying it

Question: $ARGUMENTS

Some decisions only become clear once you can click them: whether an
order can be cancelled after part of it ships, or how a settings page
should be laid out. Build a throwaway prototype that answers one such
question, let the user react to it, and record the answer for the spec.

- **A logic prototype** answers how something should behave. It's one
  HTML file anyone can open and click through: free-play buttons, and
  scenarios that walk through the awkward cases. The scenarios the user
  confirms become examples in the spec, which the build turns into its
  first tests.
- **A UI prototype** answers how a screen should look. Three variants,
  each built under a different constraint, sit on the real page, and the
  user flips between them.

The prototype lives on `spike/prototype-<slug>`, never merged; the answer
goes into the spec, and the feature is built test-first from it.

## The agents

`vibes:prototyper`.

**Check it's loaded before anything else:** it must be among the agent
types you can spawn. If it's missing, stop and tell the user, as the vibe
skill's [agents section](../vibe/SKILL.md#the-agents) says, which gives
the cause and the fix, and why no other agent may stand in for one.

## Set up

1. **Pick the shape.** A question about behaviour, rules, states or the
   shape of data is **logic**. A question about how a screen looks is
   **UI**, and needs a project whose UI runs locally. If it's unclear,
   ask the user, recommending one. Pick a short slug, such as
   `part-shipped-cancel`.
2. **Check the working tree is clean.** If it isn't, ask the user what to
   do. The current branch is the base branch.
3. **Find the guides:** `git ls-files | "${CLAUDE_PLUGIN_ROOT}/bin/guides-for"`,
   and the glossary, as the vibe skill's
   [Phase 0](../vibe/SKILL.md#phase-0-set-up) does.
4. **Make the run directory and the branch,** from the repository root:

   ```sh
   mkdir -p .vibes/prototype-<slug>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   git switch -c spike/prototype-<slug>
   ```

After each prototyper, check it stayed on the prototype branch and
committed nothing; if it didn't, stop and tell the user.

## Logic

1. **Spawn `vibes:prototyper` in `logic` mode,** with the question and
   what the user has said about it, the branch, the run directory, the
   guides and glossary, the prototype's path,
   `prototypes/<slug>/index.html`, and the path of
   `${CLAUDE_PLUGIN_ROOT}/bin/prototype-check`. On `NEEDS:`, tell the
   user, and stop.
2. **Check it yourself:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/prototype-check" prototypes/<slug>/index.html`
   must print `PROTOTYPE OK`. If not, give its lines to a fresh prototyper
   to fix. Then commit it, with a subject of 50 characters at most:
   `git add prototypes/<slug> && git commit -m "Prototype <what it tries>"`.
3. **Hand it over.** Open the file, with `open` on macOS or `xdg-open` on
   Linux, and give its path. Show `scenarios.md`, and ask the user to
   click through, then to confirm what each scenario does or say what's
   wrong, recommending they look hardest at the refused action. They can
   also send the file to someone who knows the domain, with
   `/vibes:questionnaire`.
4. **Revise on feedback:** a fresh prototyper in `logic` mode with the
   feedback, then check, commit and hand over again. Done when the user
   confirms every scenario, or says the question is settled.

## UI

1. **Find the host page:** the existing page the screen belongs on, or
   would sit inside. A page in place shows design problems that an empty
   one hides. Only when nothing fits, ask the user where a throwaway page
   should go, following the project's own routing.
2. **Spawn three `vibes:prototyper`s in `variant` mode in one message,**
   with the question, the branch, the run directory, the guides and
   glossary, the host page, and each its letter and constraint:
   - **A, everything at once:** the densest view, with all the data and
     actions visible together;
   - **B, one main action:** the thing most visits come to do, front and
     centre, and the rest out of the way;
   - **C, in steps:** the screen split into sections or steps the user
     moves through.

   When the user names a constraint of their own, add a D for it.
3. **Check they differ:** a fresh prototyper in `compare` mode. If it
   replies `CONVERGED`, have the second of the two rebuilt by a fresh
   prototyper under a constraint none has had, such as **phone first:**
   built for the smallest screen, then compare again. Do this at most
   twice.
4. **Wire them up:** a fresh prototyper in `wire` mode, with the host page
   and the variants' files. Then commit everything on the branch.
5. **Hand it over:** tell the user how to run the app and reach each
   variant, from its reply, with each variant's structure in a line from
   `variants/*.md`. Ask which they'd keep, or which parts of each, such
   as "the header from B with the list from C".
6. **Try a combination once,** if the user asks for one: a fresh
   prototyper in `variant` mode, with the next letter and the
   combination as its constraint, then `wire` mode again, then commit and
   hand over. Done when the user has chosen a structure.

## Record the answer

1. **Write `answer.md`** in the run directory from
   `${CLAUDE_PLUGIN_ROOT}/skills/prototype/templates/answer.md`: the
   question, the answer, for logic each confirmed scenario as an example
   with its expected result, for UI the chosen structure in words, what's
   still open, and the branch and its head commit.
2. **Go back to the base branch,** `git switch <base branch>`, and keep
   the prototype branch: it's the record of what was tried.
3. **Report:** the answer, the path of `answer.md`, the branch, and, when
   no vibes run is waiting for it, that `/vibes:vibe` can take the answer
   into a spec.

In a vibes run, `answer.md` is the user's answer to the question: the
designer writes it into the spec, each example becoming a requirement
the build tests, citing `spike/prototype-<slug>` at its commit.
