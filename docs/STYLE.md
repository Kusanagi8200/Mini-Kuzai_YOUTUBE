# `Documentation visual style`

## `Scope`

This rule applies to every active Markdown documentation page in the Mini-Kuzai YouTube project.

## `Titles and subtitles`

All Markdown headings must use GitHub inline-code highlighting inside the heading syntax so that the title is displayed with a gray background.

Examples:

```markdown
# `Main title`
## `Subtitle`
### `Lower-level heading`
```

Headings inside fenced code blocks are never modified.

## `Footer`

Every active documentation page must end with:

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**

The inline-code formatting provides the required gray highlight on GitHub.

## `Automation`

Use `tools/apply_doc_style.py` to normalize all active Markdown files.

The tool:
- excludes `backups/`
- creates timestamped backups before modifications
- converts active headings outside fenced code blocks
- adds or normalizes the standard footer
- is safe to run repeatedly

---

**`THE KUZ NETWORK - KUSANAGI8200 - @2026`**
