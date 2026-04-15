# Design System Specification: Technical Neo-Brutalism

## 1. Overview & Creative North Star
**Creative North Star: "The Architectural Compiler"**

This design system is a visual manifesto for the technical elite. It moves away from the "softness" of modern SaaS and leans into the rigid, unapologetic structuralism of technical blueprints and terminal interfaces. We are merging **Neo-Brutalism** (heavy weights, stark shadows, and high contrast) with **High-End Editorial Documentation** (precision spacing, wide margins, and sophisticated sans-serif scales).

The system breaks the standard "web template" look through **intentional asymmetry**. Layouts should feel like a perfectly composed schematic—stable and heavy on one side, airy and precise on the other. We don't just "show" code; we frame it as an artifact of value.

---

## 2. Colors & Surface Philosophy
The palette is a high-octane mix of industrial neutrals punctuated by a visceral "Ignition Orange."

*   **Core Palette:**
    *   **Primary (`#b52701`):** Use for critical CTAs and level-up indicators. 
    *   **Surface (`#f9f9f6`):** An off-white, "bone" paper texture that prevents eye strain compared to pure white.
    *   **On-Surface (`#1a1c1a`):** Deep charcoal for maximum legibility.
*   **The "No-Line" Rule for Layout:** While the brand uses sharp borders for *components*, large architectural sections should be defined by shifts in background color. Use `surface-container-low` (`#f4f4f1`) to set apart a side-rail from the main editor without a 1px divider.
*   **Surface Hierarchy:**
    *   **Level 0 (Base):** `surface` (`#f9f9f6`)
    *   **Level 1 (Sectioning):** `surface-container` (`#eeeeeb`)
    *   **Level 2 (In-Editor Widgets):** `surface-container-high` (`#e8e8e5`)
*   **Signature Textures:** For high-impact moments (like reaching a new "Level"), use a gradient transition from `primary` to `primary_container` (`#ff5c35`).

---

## 3. Typography
The typography is the backbone of the "Technical Documentation" aesthetic. We utilize a mix of high-character geometric sans and functional body text.

*   **The Display Scale:** `spaceGrotesk` is our voice. It feels engineered. Use `display-lg` (3.5rem) for massive achievement headers.
*   **The Technical Scale:** `inter` is our engine. It is utilized for the code editor interface, body copy, and status labels. It is chosen for its neutrality, allowing the high-contrast layout to do the heavy lifting.
*   **Label-SM (`#5b413a`):** Use the `on_surface_variant` for metadata or "line numbers" in the editor. This subtle shift in tone maintains hierarchy without losing the high-contrast feel.

---

## 4. Elevation & Depth: The Brutalist Offset
We reject traditional, blurry shadows. Depth is an architectural choice.

*   **The Shadow Principle:** Instead of soft shadows, use the **Hard Offset**. Floating cards or buttons must feature a solid, 100% opaque black or `primary` shadow, offset by 4px or 8px (e.g., `box-shadow: 4px 4px 0px #1a1c1a`).
*   **Nesting & Tonal Layering:** To keep the UI from feeling "flat," nest elements within container tiers. A `surface-container-lowest` card sitting on a `surface-container-low` background provides a soft, "lifted" feel without a shadow.
*   **Ghost Borders:** For non-interactive elements that require containment, use the `outline_variant` (`#e3beb6`) at 20% opacity. For interactive code editors, use a solid 2px `outline` (`#8f7069`) to anchor the eye.

---

## 5. Components

### Interactive Code Editor
*   **Container:** `surface_container_lowest` background, `outline` (2px solid), and a heavy 8px hard offset shadow.
*   **Gutter:** `surface_container` with `label-sm` line numbers.
*   **Active Line:** `surface_container_high` highlight with no border.

### Buttons (The "Tactile Toggle")
*   **Primary:** `primary` background, `on_primary` text. Hard offset shadow (4px). On hover, the button "depresses"—the shadow disappears, and the button translates 4px down/right.
*   **Secondary:** `surface` background, 2px `on_surface` border.
*   **Tertiary:** No background, `spaceGrotesk` bold text, underlined with a 2px `primary` stroke.

### Gamification Elements
*   **Level Progress Bar:** Track is `secondary_container` (`#e2e2e2`). The fill is a gradient from `primary` to `primary_container`. No rounded corners (use `none` or `sm`).
*   **Badges:** Use `surface_bright` with a 2px `primary` border. All icons must be stroke-based to match the "technical drawing" style.

### Input Fields
*   **Default:** `surface_container_lowest` with a 1px `outline`. 
*   **Focus State:** 2px `primary` border with a 4px `primary` hard offset shadow. This creates a "glow" that feels physical and intentional.

---

## 6. Do's and Don'ts

### Do
*   **Do** use asymmetrical grid layouts. If a section has three columns, let one occupy 50% while the others split the remaining space.
*   **Do** use uppercase `spaceGrotesk` for `label-md` and `label-sm` to evoke the feeling of a blueprint.
*   **Do** lean into the "Heavy Border" look for interactive zones (Editors, Main CTAs).

### Don't
*   **Don't** use soft, 360-degree shadows. If it floats, it must have a directional, hard-edged offset.
*   **Don't** use "Standard" 1px grey dividers. Separate content using vertical whitespace (24px/32px/48px steps) or tonal shifts in surface color.
*   **Don't** use vibrant colors outside of the `primary` orange scale. The "Technical" look relies on the discipline of a limited palette.

---

## 7. Spacing Scale
The spacing must be rigid and mathematical. 
*   **Base Unit:** 4px.
*   **Component Padding:** 12px (sm), 16px (md), 24px (lg).
*   **Section Gaps:** 64px or 80px to provide the "Editorial" breathing room that balances the heavy Neo-Brutalist elements.