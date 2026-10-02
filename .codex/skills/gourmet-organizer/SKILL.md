---
name: gourmet-organizer
description: Organize menus and visit notes with grounded tasting analysis and comparisons to earlier experiences. Use when the user shares a restaurant menu, wants a tasting write-up, or asks to merge a visit into Notes/Gourmet.md without overwriting earlier visits.
---

# Gourmet Organizer

## Use this skill when

Use this skill when the user:
- shares a tasting menu, menu photo, or dish list;
- asks for a restaurant tasting note or summary;
- wants a new visit merged into `Notes/Gourmet.md`; or
- wants multiple visits to the same restaurant kept side by side.

## Workflow

### 1. Find the right landing spot

1. Use the user-selected note, or `Notes/Gourmet.md` when it exists. Inspect headings with the available Markdown outline tool; missing prior notes do not block a new visit record.
2. Search the chosen note for the restaurant and related cuisine sections. Read only relevant earlier visits for comparison.
3. Prefer updating an existing restaurant section.
4. If the restaurant already exists, preserve prior visits and split the notes by visit, date, or menu type rather than blending everything together.

### 1.5 Lightweight public research

Before writing the final note, do a small public lookup unless the user explicitly says not to:

1. Search the public web for the restaurant name plus city/cuisine/dish keywords.
2. Prefer official restaurant pages, Michelin/Black Pearl/Dianping/Google Maps/Apple Maps/Trip.com listings, local food media, and reliable cuisine references.
3. Use public research only to confirm restaurant positioning, cuisine style, signature dishes, branch identity, and dish/cuisine background.
4. Keep user-provided tasting notes as the source of truth for what was actually eaten and how it tasted.
5. If sources are gated, noisy, or only partially readable, say so and avoid overclaiming.
6. Add links only for sources actually used in the note; do not cite search snippets that were not opened or cannot be reasonably verified.

### 2. Normalize the source material

1. Separate menu-provided information from user-added observations.
2. If a menu photo is hard to read, use the photo only as a draft parse and treat explicit user corrections as the source of truth.
3. Keep track of selected dishes versus menu options that were not chosen.
4. Omit receipt-like details by default: price, quantity, serving count, and portion count. Keep them only when they materially affect the tasting note, such as an unusually large whole fish, a per-person tasting course, a paired comparison, or a value/portion judgment the user explicitly cares about.
5. Preserve concrete sensory details: texture, aroma, temperature, aftertaste, and what made the dish memorable.

### 2.5 Develop the tasting analysis

- By default, add useful tasting interpretation alongside the record. A complete dish list alone does not fulfill a tasting-note request. If the user explicitly wants only a list, respect that scope.
- Start from distinctive dishes and the user's sensory words. Explain relevant ingredients, technique, temperature, aroma, texture, seasoning, or finish; choose the dimensions that teach something rather than applying a fixed template to every dish.
- Read relevant earlier restaurant or ingredient notes and connect genuinely comparable experiences. Explain the basis of comparison; do not force a restaurant ranking or invent a connection when none is useful.
- Distinguish actual tasting observations, sourced culinary background, and proposed things to notice next time. Use language such as “品鉴可看” or “可与……对照” for analysis that the user has not confirmed. Traditional recipes and menu names do not establish the restaurant's actual ingredients or process.
- If public research is blocked, retain clearly qualified general tasting guidance where useful. Report the lookup limit; do not silently reduce the result to transcription or invent restaurant facts.

### 3. Write the note in the house style

- Keep the existing restaurant heading if one already exists.
- Use compact bullets and short tasting analysis instead of long generic prose.
- Preserve the user's viewpoint implicitly through the tasting language; do not write meta phrases like "the user's note says".
- Keep existing content intact. Add, refine, and structure, but do not delete valuable prior notes.
- If the meal has a clear progression, keep the course order.
- End with a short summary only when it helps compare visits or explain the restaurant's style.

### 4. Sources and safety

- Add links only for external sources you actually used.
- For user-provided menu photos or text, no external citation is needed.
- Never overwrite a previous visit just because a newer menu is more detailed.

### 5. Check the actual result

Read the finished note: besides preserving dishes and sensory details, does it add a useful understanding of flavor or technique? Does any comparison to earlier notes explain a meaningful similarity or difference? Are unconfirmed ideas clearly phrased as tasting guidance? Fix these omissions before reporting completion; counts and formatting checks alone are insufficient.

## Recommended output pattern

```markdown
### [rating] Restaurant Name

#### First visit: menu name
- dish
  - ingredients
  - tasting note

#### Second visit: menu name
- dish
  - ingredients
  - tasting note
```
