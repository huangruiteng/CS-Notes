# Optional LoopX Integration

Read this reference only when the owning project already uses LoopX for document
ownership. Follow the installed `loopx-doc-registry` skill and current CLI help;
this example does not replace their contract. Document patching itself requires
no LoopX installation, Goal creation, or authority migration.

1. Find the owning repository from the user's named project, target document
   context, or current working directory. Do not choose the repository merely
   because this skill was historically used there.
2. Inspect `.loopx/registry.json` and the registry-declared active state.
3. If several goals could own the document, use the LoopX selection gate. Do
   not silently register the material under an unrelated Goal just because the
   current agent is working there.
4. Choose a stable, public-safe `source_id`. Put private names and raw URLs only
   in the ignored local manifest.
5. Preview the registration first:

```bash
loopx --registry <project-root>/.loopx/registry.json \
  register-authority-source \
  --goal-id <goal-id> \
  --source-id <stable-source-id> \
  --source-ref '<raw-lark-url-or-token>' \
  --source-kind lark_doc \
  --role <public-safe-role> \
  --freshness current \
  --owner-status <owner-status> \
  --gate-status readable \
  --boundary local_private \
  --revision '<public-safe-revision>' \
  --conflict-rule '<public-safe-conflict-rule>' \
  --topic <topic-key> \
  --dry-run
```

6. Confirm `raw_source_ref_stored=false`, then execute the same command without
   `--dry-run`.
7. After a verified remote patch, update the source revision with another
   redacted registration. Refresh existing state/Todo/rationale through their
   owners when the document changed project decisions, acceptance, or next
   actions. Keep private bodies and operational values out of projections.
