# Resume an unfinished vibe run

How to carry on a `/vibes:vibe` run that stopped, once
[Resume an unfinished run](SKILL.md#resume-an-unfinished-run) has found
its `state.md`. The phases and sections named here are the vibe skill's.

1. **Read where the run stopped:** `state.md`, the spec and design, the
   rebuild plan and the latest round directory. Tell the user which phase
   and step you're resuming from.
2. **Check git agrees.** The branches exist, the right one is checked out,
   and its latest commits match the state. Where they disagree, git is
   right: update `state.md` to match.
3. **Look at uncommitted changes.** On the rebuild branch they're usually an
   unfinished red, green or refactor step: finish it if the test list shows
   which entry it belongs to, and ask the user otherwise. Never discard
   changes without asking.
4. **Carry on from the first unfinished step:**
   - in a review round with findings files missing, run only the missing
     reviewers, with the same brief;
   - when the designer, the spiker or a builder didn't report, run it
     again, and tell it what already exists so it carries on rather than
     starting over;
   - in the build, give a fresh builder the next batch, starting from the
     first entry in the test list that isn't ticked off;
   - when `state.md` names an audit that was running and its log has no
     result, start it again, as
     [Phase 7](SKILL.md#phase-7-review-the-rebuild) says.
