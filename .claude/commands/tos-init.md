---
description: Create or refresh the data root described by the config (runs tos-init)
argument-hint: [--with-examples | --remove-examples | --dry-run]
---
Follow CLAUDE.md §0 first: resolve and read the config. Then run

    uv run tos-init $ARGUMENTS

and show its output verbatim. If it reports that the config is missing or has no `data.root`, stop and tell the human what to do (copy `config.example.yaml` to `~/.config/tos/config.yaml`, or set `$TOS_CONFIG`). Do not create the data root any other way, and do not write the config.

After a first successful run, tell the human:
1. to open `data.root` in Obsidian as a vault and install the Dataview community plugin;
2. that `raw/inbox/pull.md` is where pointers go and `raw/inbox/` is where notes go;
3. that `--with-examples` installed ten example pages tagged `example` (if it did), removable with `--remove-examples`.
