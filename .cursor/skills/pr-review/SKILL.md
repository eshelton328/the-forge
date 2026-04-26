---
name: pr-review
description: >-
  Review a pull request and render findings as a Cursor Canvas. Use when the
  user asks to review a PR, do a PR review, review a branch, or code-review
  a pull request.
---

# PR Review Skill

Review a pull request end-to-end — gather context, analyze every changed file,
and present findings in a structured Cursor Canvas.

## Workflow

### 1. Gather context

Run these in parallel:

```bash
# Commits on the branch
git log --oneline main..<branch>

# File-level summary
git diff --stat main..<branch>

# Associated PR metadata (title, body, number, state)
gh pr list --head <branch> --json number,title,url,body,state
```

If an `origin/<branch>` remote ref exists, prefer it over a local branch.

### 2. Read every diff

Get the full diff per-file (or per logical group) so nothing is missed:

```bash
git diff main..<branch> -- <path>
```

For large files, also read the full file on the branch to catch issues beyond
the diff context:

```bash
git show <branch>:<path>
```

### 3. Analyze

For each changed file, look for:

- **Correctness** — bugs, logic errors, off-by-ones, race conditions.
- **Security** — injection, secrets, permissions, supply-chain (action pinning).
- **Behavioral changes** — semantic shifts that might break existing consumers.
- **Missing coverage** — deleted safety checks, dropped rules, untested paths.
- **Consistency** — naming, style, formatting deviations within the PR itself.
- **Documentation** — misleading comments, stale references, missing context.

Also note what the PR does well — good patterns, thoughtful design, etc.

### 4. Classify findings

Use four fixed severity levels:

| Severity | Meaning | Tone (canvas) |
|----------|---------|---------------|
| **High** | Bugs, security holes, missing safety checks — must fix before merge | `danger` |
| **Medium** | Behavioral changes, inconsistencies, supply-chain concerns — should fix | `warning` |
| **Low** | Defensive-coding nits, wasted resources, minor clarity issues | `info` |
| **Nit** | Style, naming, formatting — take it or leave it | `neutral` |

### 5. Decide verdict

Choose one based on the highest-severity finding:

| Verdict | When | Callout tone |
|---------|------|--------------|
| **Approve** | No high or medium findings | `success` |
| **Request changes** | Any high findings | `warning` |
| **Comment** | Medium findings but no high | `info` |

### 6. Render as a Cursor Canvas

Create a `.canvas.tsx` file following the canvas skill conventions.
Read the canvas skill at `~/.cursor/skills-cursor/canvas/SKILL.md` before
writing the file.

Use the template below. The key sections are:

1. **Header** — PR title, branch, file/line summary.
2. **Severity stats** — `Grid` of `Stat` components, one per severity level.
3. **What's good** — bullet-style positives using `Text` with `weight="semibold"` spans.
4. **Findings table** — `Table` with severity `Pill`, file, and issue title. Row tones for high/medium.
5. **Details** — collapsible `Card` per finding (high cards open by default).
6. **Verdict** — `Callout` with the appropriate tone and a 1–2 sentence summary.

#### Canvas template

```tsx
import {
  Callout,
  Card, CardBody, CardHeader,
  Divider, Grid,
  H1, H2,
  Pill, Row,
  Stack, Stat,
  Table, Text,
} from "cursor/canvas";

// -- data types used throughout the canvas --

type Severity = "high" | "medium" | "low" | "nit";

interface Finding {
  severity: Severity;
  file: string;      // path relative to repo root
  title: string;     // one-line summary
  detail: string;    // full explanation
}

// -- helper maps --

const SEVERITY_ORDER: Record<Severity, number> = { high: 0, medium: 1, low: 2, nit: 3 };

function severityTone(s: Severity): "danger" | "warning" | "info" | "neutral" {
  if (s === "high") return "danger";
  if (s === "medium") return "warning";
  if (s === "low") return "info";
  return "neutral";
}

function severityLabel(s: Severity): string {
  return s === "nit" ? "Nit" : s.charAt(0).toUpperCase() + s.slice(1);
}

// -- inline data (populated per review) --

const TITLE = "PR Review: <branch-name>";
const SUBTITLE = "<pr-title> — N files, +A/−D";

const positives: string[] = [
  // "**Bold label** — explanation of what's good."
];

const findings: Finding[] = [
  // { severity: "high", file: "path/to/file", title: "...", detail: "..." },
];

const VERDICT_TONE: "success" | "warning" | "info" = "warning";
const VERDICT_TITLE = "Request changes";
const VERDICT_BODY = "Summary of why.";

// -- derived --

const sorted = [...findings].sort(
  (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]
);

function countSeverity(s: Severity): number {
  return findings.filter((f) => f.severity === s).length;
}

// -- component --

export default function PRReview() {
  return (
    <Stack gap={24}>
      <Stack gap={4}>
        <H1>{TITLE}</H1>
        <Text tone="secondary">{SUBTITLE}</Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value={String(countSeverity("high"))}   label="High"   tone="danger"  />
        <Stat value={String(countSeverity("medium"))} label="Medium" tone="warning" />
        <Stat value={String(countSeverity("low"))}    label="Low"    tone="info"    />
        <Stat value={String(countSeverity("nit"))}    label="Nit"                   />
      </Grid>

      <Divider />

      <H2>What's good</H2>
      <Stack gap={8}>
        {positives.map((p, i) => (
          <Text key={i}>{p}</Text>
        ))}
      </Stack>

      <Divider />

      <H2>Findings</H2>
      <Table
        headers={["Severity", "File", "Issue"]}
        rows={sorted.map((f) => [
          <Pill tone={severityTone(f.severity)} size="sm" active>
            {severityLabel(f.severity)}
          </Pill>,
          <Text size="small" tone="secondary">{f.file.split("/").pop()}</Text>,
          f.title,
        ])}
        rowTone={sorted.map((f) =>
          f.severity === "high" ? "danger"
            : f.severity === "medium" ? "warning"
            : undefined
        )}
      />

      <Divider />

      <H2>Details</H2>
      {sorted.map((f, i) => (
        <Card key={i} collapsible defaultOpen={f.severity === "high"}>
          <CardHeader
            trailing={
              <Pill tone={severityTone(f.severity)} size="sm" active>
                {severityLabel(f.severity)}
              </Pill>
            }
          >
            {f.title}
          </CardHeader>
          <CardBody>
            <Stack gap={8}>
              <Text size="small" tone="secondary">{f.file}</Text>
              <Text>{f.detail}</Text>
            </Stack>
          </CardBody>
        </Card>
      ))}

      <Divider />

      <H2>Verdict</H2>
      <Callout tone={VERDICT_TONE} title={VERDICT_TITLE}>
        {VERDICT_BODY}
      </Callout>
    </Stack>
  );
}
```

#### Populating the template

- Fill `findings` with one entry per issue. Keep `title` to one line; put
  the full explanation in `detail`.
- Fill `positives` with bold-label + dash + explanation strings. The canvas
  `Text` component renders markdown-style bold automatically.
- For the "What's good" section, use inline `<Text as="span" weight="semibold">`
  for bold labels rather than relying on markdown bold.
- Set `VERDICT_TONE`, `VERDICT_TITLE`, `VERDICT_BODY` per the verdict table.
- Name the canvas file `pr-review-<branch>.canvas.tsx`.

### 7. Summarize in chat

After creating the canvas, post a brief chat summary:

1. Verdict (approve / request changes / comment).
2. Count of findings per severity.
3. One sentence per high-severity finding.
4. One sentence covering the positives.

Keep it concise — the canvas has the details.
