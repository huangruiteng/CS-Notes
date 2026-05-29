---
name: gourmet-organizer
description: Organize tasting menus, menu photos, and visit notes into the right gourmet note. Use when the user shares a restaurant menu, wants a tasting write-up, or asks to merge a new visit into Notes/Gourmet.md without overwriting earlier visits.
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

1. Run `python3 Notes/snippets/markdown_toc.py Notes/Gourmet.md` to see the file structure.
2. Search for the restaurant and nearby cuisine sections with `rg -n "<restaurant>|<cuisine>|<city>" Notes/Gourmet.md`.
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
