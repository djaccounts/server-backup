# Composition Guide

Techniques for creating professional images with picture-it, learned from real production use.

## Table of Contents

1. Typography & Font Size Calculator
2. Text Behind Subject
3. Multi-Pass Editing
4. Product Photography with Real Images
5. Magazine Covers and Posters
6. Color Grading and Post-Processing
7. Background Removal Best Practices
8. Writing Effective FAL Prompt
9. Overlay Composition with JSON

---

## 1. Typography

### When to Use Which

- **Big titles, hero text, headlines:** Use FAL via `edit` command. The model renders text naturally into the scene. Just say "very large bold" in the prompt — no pixel math needed.
- **Precise small text** (credits, URLs, badges, coverlines): Use `compose` or `text` with Satori. Run `picture-it download-fonts` first if fonts aren't installed.

### Satori Font Sizing (only applies to `compose`/`text` commands)

Images display much smaller on phones. Quick rule: **on a 1080px image, nothing under 36px is readable on a phone.**

| Platform | Image width | Scale | Min readable |
|---|---|---|---|
| Instagram | 1080px | 3× | 36px+ |
| Blog/OG | 1200px | 2× | 24px+ |
| YouTube thumb | 1280px | 6× | 80px+ |

### Typography Rules

- **Max 3 text sizes** per image — more creates noise
- **Brand name > tagline** — brand should be the largest text, not the tagline
- **Font pairing:** Use a serif + sans-serif pair or two complementary sans-serifs.

| Pair | Vibe |
|---|---|
| Playfair Display + Inter | Elegant editorial |
| DM Serif Display + Inter | Classic luxury |
| Space Grotesk + Inter | Tech / SaaS |
| Poppins + Open Sans | Friendly modern |

**For FAL model text** (`edit`/`generate`): Any font works — just describe it in the prompt. The model renders it.

**For Satori text** (`compose`/`text`): picture-it bundles Inter, Space Grotesk, and DM Serif Display. Drop additional `.ttf` files into `~/.picture-it/fonts/`.

---

## 2. Text Behind Subject

The most impactful technique for thumbnails and posters. The text appears to be part of the 3D scene, not floating on top.

```bash
picture-it generate --prompt "basketball player mid-jump, low angle, stadium lights" --model flux-dev --size 1280x720 -o player.png

picture-it edit -i player.png \
  --prompt "Add 'CLUTCH' in very large bold white block capital letters BEHIND the basketball player. The player's body overlaps and partially covers the letters, proving the text is behind her. Bold condensed sans-serif font. Keep everything else identical." \
  --model seedream -o thumbnail.png
```

**Key prompt patterns:**
- "Add [TEXT] BEHIND the [subject]"
- "The [subject's] body overlaps and partially covers the letters"
- "Bold condensed sans-serif font, solid [color]"
- "Keep everything else identical"

---

## 3. Multi-Pass Editing

The most powerful technique. Each pass adds one layer of complexity.

**Pattern: Generate → Edit → Post-process**

```bash
# Pass 1: Base environment
picture-it generate --prompt "dark stage with emerald spotlight, reflective floor, volumetric fog" --size 2048x1080 -o stage.png

# Pass 2: Place objects into the scene
picture-it edit -i stage.png -i logo.png \
  --prompt "Place Figure 2 as a large glowing 3D object in the center spotlight." \
  --model seedream -o composed.png

# Pass 3: Add atmosphere
picture-it edit -i composed.png \
  --prompt "Add volumetric fog at ground level and more dust particles in the light beams. Keep everything else identical." \
  --model seedream -o atmospheric.png

# Pass 4: Final sizing and grading
picture-it crop -i atmospheric.png --size 1200x630 --position attention -o cropped.png
picture-it grade -i cropped.png --name cinematic -o final.png
picture-it vignette -i final.png --opacity 0.3 -o hero.png
```

Each `edit` call costs $0.04 (seedream). A 4-pass workflow is ~$0.16 total.

---

## 4. Product Photography with Real Images

When comparing real products, AI edit models alter details. The reliable approach:

```bash
# 1. Remove backgrounds from product photos (use bria for clean edges)
picture-it remove-bg -i product-a.png --model bria -o a-cutout.png
picture-it remove-bg -i product-b.png --model bria -o b-cutout.png

# 2. Generate or create a background
picture-it generate --prompt "split gradient blue left to orange right, dark, premium" --size 1200x630 -o bg.png

# 3. Compose with overlays JSON
picture-it compose -i bg.png --overlays comparison.json -o result.png
```

**Why not use `edit` for products?** AI models change product details. For product blogs, `remove-bg` → `compose` preserves the original pixel-perfectly.

---

## 5. Magazine Covers and Posters

Two-layer approach: FAL for the hero image/scene, Satori for precise typography.

```bash
# 1. Generate editorial portrait
picture-it generate --prompt "sports photography, basketball player mid-action, low angle" --model flux-dev --size 1080x1440 -o portrait.png

# 2. Add title BEHIND subject with FAL
picture-it edit -i portrait.png --prompt "Add 'CLUTCH' in very large bold white letters behind the player..." --model seedream -o titled.png

# 3. Add coverlines, badges, credits with Satori (pixel-perfect)
picture-it compose -i titled.png --overlays magazine-overlays.json --size 1080x1440 -o cover.png
```

---

## 6. Color Grading and Post-Processing

Apply after all compositing is done. These are free (Sharp, no API calls).

| Grade | Effect | Good for |
|---|---|---|
| `cinematic` | Teal shadows, warm highlights | Movie posters, dramatic content |
| `moody` | Desaturated, crushed blacks | Dark/brooding content |
| `vibrant` | Boosted saturation | Product shots, social media |
| `clean` | Slight sharpening | Minimal, professional |
| `warm-editorial` | Golden tones | Editorial, luxury content |
| `cool-tech` | Blue shift, high contrast | Tech, SaaS content |

```bash
picture-it grade -i input.png --name cinematic -o graded.png
picture-it grain -i graded.png --intensity 0.05 -o grained.png
picture-it vignette -i grained.png --opacity 0.3 -o final.png
```

---

## 7. Background Removal Best Practices

| Model | Best for | Edge quality |
|---|---|---|
| `bria` | Product photos, clean objects | Best — tight edges |
| `birefnet` | General purpose | Good but rectangular artifacts |
| `pixelcut` | Alternative | Good |
| `rembg` | Budget option | Acceptable |

Always use `--model bria` and trim after removing background.

---

## 8. Writing Effective FAL Prompts

**For generation (flux):** Be specific about lighting, camera, composition, atmosphere.

**For editing (seedream/banana):** Reference figures explicitly, be explicit about preservation, describe placement physically, for text specify "large bold [color] [style] letters BEHIND the [subject]".

**Common mistakes:** Prompts too vague, not saying "keep everything else identical", using `edit` for product images, not specifying font style for text.

---

## 9. Overlay Composition with JSON

The `compose` command accepts a JSON array of overlay objects. Each overlay has a `type`, position, and rendering properties.

**Overlay types:** `image`, `satori-text`, `shape`, `gradient-overlay`, `watermark`

**Positioning:** Use named zones (`hero-center`, `title-area`, `top-bar`, `bottom-bar`) or raw `{x, y}` percentages.

**Available fonts:** Inter (400, 600, 700), Space Grotesk (500, 700), DM Serif Display (400)

**Satori CSS subset:** flexbox, fontSize, fontFamily, fontWeight, color, backgroundColor, backgroundImage (linear-gradient), textShadow, letterSpacing, lineHeight, borderRadius, border, padding, margin, opacity, gap.

**Satori does NOT support:** display:grid, transforms, animations, box-shadow, filters.