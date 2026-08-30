# Home

Engine-owned dashboard, installed by `/tos-init` from `schema/vault/Home.md`; not part of the OKF bundle, not indexed, not logged. Needs the Dataview community plugin (Settings → Community plugins → Browse → Dataview).

## Unverified, newest first

```dataview
TABLE type, status, generated.at AS written, stale_after
FROM "wiki"
WHERE type AND !verified AND type != "Review"
SORT generated.at DESC
LIMIT 10
```

## Changed since verification

```dataview
TABLE type, generated.at AS written, verified
FROM "wiki"
WHERE verified AND generated.at > max(map(verified, (v) => v.at))
```

## Stale or expiring within a week

```dataview
TABLE type, status, stale_after
FROM "wiki"
WHERE stale_after AND stale_after <= date(today) + dur(7 days) AND status != "deprecated"
SORT stale_after ASC
```

## Drafts older than two weeks

```dataview
TABLE type, generated.at AS written
FROM "wiki"
WHERE status = "draft" AND generated.at <= date(today) - dur(14 days) AND type != "Review"
SORT generated.at ASC
```

## Checkpoints passed

```dataview
TABLE type, owner, next_checkpoint
FROM "wiki/delivery"
WHERE next_checkpoint AND next_checkpoint < date(today)
SORT next_checkpoint ASC
```

## Systems due for review

```dataview
TABLE owner, stale_after
FROM "wiki/systems"
WHERE type = "System" AND stale_after <= date(today) + dur(14 days)
SORT stale_after ASC
```

## RFCs stuck in draft

```dataview
TABLE status, generated.at AS opened
FROM "wiki/design/rfcs"
WHERE status = "draft" AND generated.at <= date(today) - dur(14 days)
```

## Open questions

```dataview
LIST description
FROM "wiki/questions"
WHERE status AND status != "deprecated"
SORT generated.at DESC
```
