---
name: feature-sandbox
description: Create and maintain an isolated development workspace for a new feature/module without modifying existing code. Use when the user says things like "新增独立功能模块", "实验性功能", "测试用", "尝试用", "为新增功能创建独立目录", "feature sandbox", "prototype", "新增功能但不改现有代码", or when a new verification environment, RTL module, tool, or analysis track needs its own versioned workspace separate from the main project changelog.
---

# Feature Sandbox Workflow

Use this workflow when the user wants to add a **new, self-contained feature or module** and keep its development history isolated from the main project workflow (e.g., root `修改记录/CHANGES.md`).

Typical use cases:
- A new verification environment (e.g., 420b long-encoding verification).
- A new analysis tool or script package.
- A new documentation/spec extraction track.
- Any feature that should not pollute the main changelog until it is ready for integration.

Do **not** use this workflow for small, inline bug fixes or for changes that are clearly part of the main project flow.

---

## 1. Decide the Workspace Name

Ask the user for a short feature name if it is not obvious from context. The workspace directory name should be `<feature>_ver/`, for example:

- `longcode_ver` for long-encoding verification
- `ddrphy_ver` for a new DDR PHY verification track
- `powercalc_ver` for a new power analysis tool

Place the workspace at the project root unless the user specifies another location.

---

## 2. Create the Directory Structure

Create the following structure under `<feature>_ver/`:

```
<feature>_ver/
├── current_work/              # Working copies of modified/new files
├── <MMDD>v1/                  # First stable snapshot (e.g., 0703v1)
├── <MMDD>v2/                  # Subsequent stable snapshots
├── README.md                  # Purpose, workflow, version status
├── CHANGELOG.md               # Feature-specific changelog
├── migration_checklist.md     # Dependencies and migration notes (optional but recommended)
└── <other analysis docs>.md   # Spec extraction, design notes, etc.
```

Also create the first version folder immediately, even if it is just a placeholder, so the history pattern is established.

---

## 3. Establish Conventions

Document these conventions in `<feature>_ver/README.md`:

- **Timestamp rule**: every modified file ends with a timestamp comment, e.g.:
  ```systemverilog
  // ymzhu 0703_1445
  ```
- **Backup naming**: `<original_name>_YYYYMMDD_vN.<ext>` (e.g., `isptx_sequence_20260703_v1.sv`).
- **Version naming**: `MMDDvN` (e.g., `0703v1`).
- **Scope rule**: feature changes are **not** recorded in the main project changelog (e.g., `修改记录/CHANGES.md`). They live only in `<feature>_ver/CHANGELOG.md`.
- **Integration rule**: when the feature is ready to merge back, copy files from `current_work/` to their real project locations and update the main project filelists/case lists as needed.

---

## 4. Perform the Feature Work

1. Modify or create files in the real project locations (`DV_TCON_C/`, `HDL/`, etc.).
2. Append the agreed timestamp comment to the end of every modified file.
3. Copy the modified files into `<feature>_ver/current_work/` using the backup naming convention.
4. Update `<feature>_ver/CHANGELOG.md` with a dated version entry.
5. If the feature depends on `env_cfg` or other shared project interfaces, update `<feature>_ver/migration_checklist.md` with:
   - files changed
   - `env_cfg`/dependency items the feature relies on
   - known spec gaps or pending confirmations

---

## 5. Take Stable Snapshots

When the user considers a version stable:

1. Copy everything from `current_work/` into a new `<feature>_ver/<MMDD>vN/` folder.
2. Update `README.md` version status table.
3. Keep `current_work/` as the active working copy.

---

## 6. Keep the Main Changelog Clean

If the project has a root changelog (e.g., `修改记录/CHANGES.md`):

- Do **not** add feature-specific detailed entries there.
- Optionally add a single line in the root changelog pointing to `<feature>_ver/CHANGELOG.md` if the user explicitly asks for visibility.
- Otherwise leave the root changelog untouched.

---

## 7. Example Workflow Summary

User: "我要新增一个 420b 长编码验证环境，不要混到主 changelog 里。"

Agent actions:
1. Create `longcode_ver/` with `current_work/`, `0703v1/`, `README.md`, `CHANGELOG.md`, `migration_checklist.md`.
2. Implement `long_encoding_ref_model.sv`, `isptx_sequence.sv` changes in `DV_TCON_C/`.
3. Add `// ymzhu 0703_1445` to each modified file.
4. Back up files to `longcode_ver/current_work/isptx_sequence_20260703_v1.sv`, etc.
5. Write the first entry in `longcode_ver/CHANGELOG.md`.
6. Do **not** write anything into `修改记录/CHANGES.md`.

---

## 8. When the Feature Is Ready to Merge

1. Copy files from `current_work/` back to their real project paths.
2. Update main project filelists, case lists, or `AGENTS.md` if needed.
3. Only then consider adding a brief merge note to the root changelog.
