"""tos-verify-mark — append a `verified` entry to a page, guardrails enforced.

    uv run tos-verify-mark <wiki-relative-page.md> --by <actor>
                           [--at <ISO-8601>] [--promote] [--human-confirmed] [--dry-run]

Actor rules (CLAUDE.md §5, guardrail 2):
  * `process:<id>` — allowed; this is how the cross-check pass writes machine-confirmed.
  * `human:<id>`   — only the config's data.actor, and only with --human-confirmed:
                     the flag is /tos-verify's assertion that the human said "yes".
                     Never pass it anywhere else.
  * anything else (the agent included) — refused. The agent never verifies.

`--promote` flips `status: draft` to `stable` only when the type's gate in
schema/types.md is met by the resulting entries. `generated` is never touched —
a verification is not a meaningful change. No log line, no commit: /tos-verify
owns both, so a failed promote never leaves a dangling log entry.
"""
from __future__ import annotations

import sys

from tos import bundle
from tos import common as pc
from tos.index_add import _flag


def main(argv) -> int:
    dry = "--dry-run" in argv
    promote = "--promote" in argv
    confirmed = "--human-confirmed" in argv
    argv = [a for a in argv if a not in ("--dry-run", "--promote", "--human-confirmed")]
    argv, by, err = _flag(argv, "--by")
    if not err:
        argv, at, err = _flag(argv, "--at")
    if err or len(argv) != 1 or not by:
        print(err or "usage: tos-verify-mark <wiki-relative-page.md> --by <actor> [--at ISO-8601] "
                     "[--promote] [--human-confirmed] [--dry-run]", file=sys.stderr)
        return 2
    cfg = pc.load_config()
    actor = (cfg.get("data") or {}).get("actor")
    if by.startswith("human:"):
        if by != actor:
            print(f"`{by}` is not the config's data.actor ({actor}) — refusing", file=sys.stderr)
            return 1
        if not confirmed:
            print("a human: verification needs --human-confirmed — only /tos-verify passes it, "
                  "on the human's explicit \"yes\" (guardrail 2)", file=sys.stderr)
            return 1
    elif not by.startswith("process:"):
        print(f"`{by}` can not verify: only `process:<id>`, or the human through /tos-verify "
              "(the agent never verifies)", file=sys.stderr)
        return 1

    wiki = pc.data_root(cfg) / "wiki"
    page = pc.bundle_path(wiki, argv[0])
    if page is None:
        print(f"`{argv[0]}` points outside the bundle — pass a path relative to {wiki}", file=sys.stderr)
        return 2
    if not page.exists():
        print(f"`{argv[0]}` does not exist under {wiki}", file=sys.stderr)
        return 1
    text = page.read_text(encoding="utf8")
    fm, _, fm_err = pc.split_frontmatter(text)
    if fm_err or fm is None:
        print(f"`{argv[0]}` frontmatter is unreadable ({fm_err or 'no frontmatter'}) — fix it first",
              file=sys.stderr)
        return 1
    if at:
        if pc.parse_datetime(at) is None:
            print(f"--at `{at}` is not ISO-8601", file=sys.stderr)
            return 2
    else:
        at = pc.now(cfg).isoformat()
    try:
        new_text = bundle.append_verified_entry(text, by, at)
    except ValueError as e:
        print(f"`{argv[0]}` {e} — fix it by hand", file=sys.stderr)
        return 1

    new_fm, _, new_err = pc.split_frontmatter(new_text)
    if new_err or not any(e.get("by") == by for e in pc.verified_entries(new_fm)):
        sys.exit(f"internal error: the edited frontmatter did not take the entry ({new_err})")

    promoted = gate_note = became_record = None
    if promote:
        t = str(fm.get("type"))
        entry = pc.load_registry().get(t, {})
        gate = entry.get("gate_kind", "H")
        # the tier, not the presence of an entry: a verification older than the page's
        # `generated.at` reads as changed-since-verified, and a page nobody has re-read
        # since it last changed is not one the gate lets through
        tier = pc.trust_tier(new_fm)
        met = gate == "-" or (gate == "M" and tier in ("machine-confirmed", "human-reviewed")) or (
            gate == "H" and tier == "human-reviewed")
        if fm.get("status") != "draft":
            gate_note = f"status is `{fm.get('status')}` — --promote only lifts draft"
        elif met:
            edits = {"status": "status: stable"}
            # a type whose horizon runs "while draft, then —" becomes a record on promotion:
            # keeping the draft's expiry would have lint report the stable page as stale (RFC)
            if entry.get("record_when_stable"):
                edits["stale_after"] = pc.STALE_AFTER_RECORD
                became_record = True
            new_text = bundle.edit_frontmatter_lines(new_text, edits)
            promoted = True
        elif tier == "changed-since-verified":
            gate_note = ("gate not met: the verification is older than the page's `generated.at`, so the page "
                         "reads as changed-since-verified — re-read it and verify at a current time")
        else:
            gate_note = f"gate not met: a `{t}` needs {'a human: verification' if gate == 'H' else 'verification'}"

    if not dry:
        page.write_text(new_text, encoding="utf8")
    final_fm, _, _ = pc.split_frontmatter(new_text)
    print(f"verified: {argv[0]} by {by} at {at} — tier {pc.trust_tier(final_fm)}"
          + (", promoted to stable" if promoted else "")
          + (" (a record now: stale_after ~)" if became_record else ""))
    if gate_note:
        print(gate_note)
    if dry:
        print("(dry run — nothing written)")
    return 0


def cli() -> None:
    sys.exit(main(sys.argv[1:]))


if __name__ == "__main__":
    cli()
