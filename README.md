# Wording

One pack of six writing skills for **Claude Code and Codex**.

## Why this exists

An AI draft can be fluent and still make the reader work too hard. The main point gets buried. Abstract phrases hide who does what. A confident conclusion goes further than its evidence. A shorter rewrite quietly drops a condition that mattered.

“Make it better” leaves the model to decide what better means. Writing has different jobs: an explanation should help someone understand; a proposal should justify a decision; instructions should help someone complete a task. The same polished voice and structure will not serve all three equally well.

Wording turns those jobs into reusable instructions. Each skill identifies the reader's need, chooses a suitable structure, and checks the result against the source material. The shared priorities are:

- **Meaning:** name supported actors and actions, clarify references, and remove empty emphasis.
- **Fidelity:** preserve facts, uncertainty, conditions, commitments, and the writer's actual position.
- **Reader fit:** adapt detail, organization, tone, and the next step to the audience and purpose.
- **Useful revision:** fix a specific weakness, then stop when the brief is met.

This reduces the need to paste the same editorial instructions into every conversation. It also gives revisions a clearer target than a list of banned words. Sentence length, passive voice, headings, and technical terms remain choices governed by the task.

## Choose a skill

| Skill | Reader's job | Typical uses |
| --- | --- | --- |
| [wording-explain](skills/wording-explain/SKILL.md) | Understand | Explanations, articles, FAQs, factual updates |
| [wording-persuade](skills/wording-persuade/SKILL.md) | Choose or act | Proposals, pitches, advocacy, persuasive copy |
| [wording-analyze](skills/wording-analyze/SKILL.md) | Weigh evidence | Research synthesis, comparisons, recommendations |
| [wording-instruct](skills/wording-instruct/SKILL.md) | Complete a task | Tutorials, procedures, onboarding |
| [wording-correspond](skills/wording-correspond/SKILL.md) | Respond | Emails, outreach, requests, follow-ups |
| [wording-edit](skills/wording-edit/SKILL.md) | Improve a draft | Clarity, structure, concision, voice adaptation |

Choose one primary skill. Use `analyze` for an open question and `persuade` for an explicit advocacy task. Use `correspond` when the recipient and relationship shape the message. Each skill is self-contained.

## Install the pack

Download and extract a release, or clone this repository. From its root, use **Python 3.9 or later**:

```sh
# Preview installation for both tools.
python3 tools/skills.py install --scope user

# Install all six skills for use across projects.
python3 tools/skills.py install --scope user --apply
```

The installer links the shared `skills/` folders into `~/.agents/skills` for Codex and `~/.claude/skills` for Claude Code. Keep the downloaded folder in place while using linked installations. Existing unrelated files are never overwritten.

Options:

- Omit `--scope user` to install only in this project. Project links are relative and survive moving the folder.
- Add `--provider codex` or `--provider claude` to select one tool.
- Add `--copy` for independent copies where symlinks are unsuitable. Copies need separate updates.

Open a new session if the skills do not appear. See the official [Codex](https://learn.chatgpt.com/docs/build-skills) and [Claude Code](https://code.claude.com/docs/en/skills) documentation for discovery and invocation details.

## Use a skill

**Codex**

```text
$wording-explain Explain this feature to a first-time user. Use only the facts below: …
```

**Claude Code**

```text
/wording-persuade Draft a proposal for this audience, using this evidence: …
```

Descriptions also support automatic selection. For a more precise brief, supply whichever fields matter:

```text
Reader:
What the reader should understand or do:
Source facts or material:
Required length or format:
Voice sample or tone preference:
```

The skills follow the requested genre and format. They use available sources and tools without pretending to have verified inaccessible material. A draft does not authorize sending, publishing, or making commitments.

### Claude.ai

Claude.ai imports individual skills through **Customize → Skills**. Generate one upload ZIP per skill:

```sh
python3 tools/skills.py package --output packages
```

Upload the generated ZIPs separately. Each contains a skill folder with `SKILL.md` inside it. The full pack archive is for distribution and local installation; Claude.ai requires these individual upload files. [Upload instructions](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills).

## Design basis and limits

The pack uses the open [Agent Skills format](https://agentskills.io/specification), with provider-neutral instructions and concise `name`/`description` metadata. The approach draws on [plain-language principles](https://www.archives.gov/open/plain-writing/10-principles.html) and [explicit outcomes and relevant examples in prompting](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices). The [discussion that prompted this project](https://x.com/zhizdev/status/2119874095269707977) is useful motivation; its informal chart is not a validated model ranking.

These are writing instructions, not a guarantee of accuracy or a universally best style. Quality depends on the model, the brief, and the supplied evidence. Review important claims and judge the output by what the intended reader can understand or do.

## Check the pack

```sh
python3 tools/skills.py validate
python3 -m unittest discover -s tools -p 'test_*.py'
```

The checks cover metadata, references, installation, collision handling, and upload archives. They do not measure writing quality. Tests use synthetic temporary folders.

## License

[MIT](LICENSE).
