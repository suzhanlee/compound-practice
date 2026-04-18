# validate-tasks — Verification Agent for Ralph Loop

## Purpose
Validates that tasks marked as "end" in spec.json actually pass their verification commands.
Updates status if verification fails, enabling ralph loop correction.

## Steps

1. **Read spec.json**
   - Use Read tool to load `.dev/task/spec.json`
   - Filter tasks with `status == "end"`

2. **Verify each "end" task**
   - For each task: run `task.verification` command via Bash
   - Exit code 0 → status remains "end"
   - Exit code != 0 → Update status to "not_start" for re-execution

3. **Update spec.json**
   - Use Bash + jq to update each failed task's status:
     ```bash
     jq --argjson i INDEX '.tasks[$i].status = "not_start"' spec.json > tmp && mv tmp spec.json
     ```
   - Verify JSON remains valid after each update

4. **Report results**
   - Total "end" tasks verified
   - Count passed (remained "end")
   - Count failed (reverted to "not_start") + their action names

## Rules

- Verification exit code is the only criterion (0 = pass, != 0 = fail)
- Failed tasks MUST be set to "not_start" so mini-execute re-processes them
- spec.json must remain valid JSON after all updates
- Do not skip any "end" status task

## Allowed Tools

- Read
- Write  
- Bash
