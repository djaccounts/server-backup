---
name: picture-it
description: Generate and edit images from the CLI using picture-it. Use this skill whenever the user asks to create, edit, or manipulate images — blog headers, social cards, hero images, product comparisons, YouTube thumbnails, movie posters, magazine covers, Instagram edits, background removal, or any visual content. Also trigger when the user mentions picture-it by name, wants to composite images, apply color grading, add text to images, remove or replace backgrounds, crop/resize photos, or needs any kind of image generation or photo editing from the terminal. This skill covers multi-pass AI image editing workflows that chain composable operations together.
compatibility: Requires Node.js 18+ and picture-it CLI (npm package). FAL_KEY environment variable needed for AI operations. Network access to fal.ai for image generation/editing.
license: MIT
metadata:
  author: geongeorge
  version: "0.2.0"
  homepage: https://github.com/geongeorge/picture-it
  source: https://github.com/geongeorge/picture-it
  package: https://www.npmjs.com/package/picture-it
  openclaw:
    primaryEnv: FAL_KEY
    requires:
      env:
        - FAL_KEY
      bins:
        - node
        - picture-it
      config:
        - ~/.picture-it/config.json
    install:
      - kind: npm
        package: picture-it
        bins:
          - picture-it
    data-transmission: User images are uploaded to fal.ai for AI processing. See https://fal.ai/privacy for retention policy.
---

# picture-it

Photoshop for AI agents. Composable image operations from the CLI.

Source: https://github.com/geongeorge/picture-it | npm: https://www.npmjs.com/package/picture-it

## Prerequisites

picture-it must be installed and configured. Requires Node.js 18+.

```bash
# Install (pick one)
npm install -g picture-it
pnpm add -g picture-it
bun install -g picture-it

# Setup
picture-it download-fonts
```

### Credentials

The FAL API key is required for AI operations (generate, edit, remove-bg, upscale). Set it via environment variable or the CLI:

```bash
# Option 1: Environment variable (preferred — use platform-managed secrets)
export FAL_KEY=your-key-here

# Option 2: CLI config (stored in ~/.picture-it/config.json with 0600 permissions)
picture-it auth --fal <fal-api-key>
```

NEVER paste API keys into chat. Always use environment variables or the CLI auth command. Get a FAL key from https://fal.ai.

Note: User images are uploaded to fal.ai for AI processing when using generate, edit, remove-bg, or upscale commands. Local-only commands (crop, grade, grain, vignette, text, compose, template, info) do not transmit data.

## Core Concept

Every command takes an image in and outputs an image. Chain them to build anything. The agent calling picture-it IS the planner — there is no AI planner inside the tool.

## Before You Generate Anything — Think First

Image generation costs real money ($0.03–$0.15 per FAL call). A 4-pass workflow is $0.10+. Don't burn budget on a vague idea — spend time planning before running any commands.

### Step 1: Understand the purpose

Before touching picture-it, get full clarity on what the user wants. Ask yourself:

- **What is this image for?** (blog header, Instagram ad, YouTube thumbnail, product comparison, poster)
- **Who is the audience?** (developers, consumers, enterprise buyers)
- **What should someone FEEL when they see it?** (excitement, trust, urgency, curiosity)
- **What's the one message?** Every good image communicates exactly one thing.
- **Where will it be displayed?** This determines size, text sizing, and composition rules.

If any of these are unclear, ask the user before proceeding. A 30-second question saves $0.15 in wasted generation.

### Step 2: Plan the composition

Think through at least 3 different approaches before picking one. Consider:

- **Can this be done without FAL?** Templates and Satori compose are free. A solid gradient + good typography is often enough.
- **What's the minimum number of FAL calls?** Each call costs money. Plan the fewest passes that achieve the goal.
- **Which technique fits?** Text-behind-subject for thumbnails, remove-bg + compose for product photos, multi-pass for cinematic scenes.

Present your top 2-3 ideas to the user briefly — one sentence each — and let them pick before generating.

### Step 3: Plan the pipeline

Before running the first command, write out the full pipeline with cost estimates. This avoids discovering mid-way that you need a different approach and wasting the earlier calls.

## Commands Quick Reference

| Command | What it does | Needs FAL? |
|---|---|---|
| `generate` | Create image from text prompt | Yes |
| `edit` | Edit image(s) with AI | Yes |
| `remove-bg` | Remove background | Yes |
| `replace-bg` | Remove bg + generate new one | Yes |
| `crop` | Resize/crop to exact dimensions | No |
| `grade` | Apply color grading | No |
| `grain` | Add film grain | No |
| `vignette` | Add edge darkening | No |
| `text` | Render text onto image (Satori) | No |
| `compose` | Overlay images/text/shapes from JSON | No |
| `template` | Built-in templates (no AI) | No |
| `info` | Analyze image dimensions/colors | No |

## Model Selection

Choose the right model for the job — don't overspend.

**Generation-only models:**

| Model | Cost | Best for |
|---|---|---|
| `flux-schnell` | $0.003 | Default. Fast drafts, backgrounds, base scenes |
| `imagineart` | $0.03 | High-fidelity realism, accurate text rendering |
| `flux-dev` | $0.03 | Detailed scenes, portraits, cinematic quality |
| `recraft-v3` | $0.04 | Text in images, vector art, brand-style graphics |
| `fibo` | $0.04 | Enterprise, structured/controlled generation |
| `recraft-v4` | $0.25 | Premium. Best composition, lighting, materials. Use sparingly |

**Edit-only models:**

| Model | Cost | Best for |
|---|---|---|
| `reve-fast` | $0.02 | Cheapest. Quick iterations, speed over refinement |
| `kontext-lora` | $0.035 | Edits with LoRA styles, brand-consistent modifications |
| `kontext` | $0.04 | Default. Targeted local edits, scene transforms, text placement |
| `reve` | $0.04 | Style transforms, product variations, context-aware edits |
| `fibo-edit` | $0.04 | Precise control with JSON + masks, object add/remove, restyling |

**Both generate AND edit:**

| Model | Cost | Best for |
|---|---|---|
| `seedream-v4` | $0.03 | Budget option. Good multi-image compositing |
| `seedream` | $0.04 | Multi-image compositing (up to 10 inputs), placing objects in scenes |
| `banana2` | $0.08 | Better image preservation, >10 inputs, extreme aspect ratios, web search |
| `banana-pro` | $0.15 | Premium. Best realism, typography, character consistency for up to 5 people |

**Background removal:** bria (default, best edges), birefnet, pixelcut, rembg

## How to Write Good Prompts

Read `references/prompt-library.md` for a full library of tested prompts. Key rules:

**For generation:** Be specific about lighting, camera, and atmosphere. Vague prompts produce generic results.

**For text-behind-subject:** The key phrase is: *"Add '[TEXT]' in large bold [color] letters BEHIND the [subject] — the [subject's] body overlaps and partially covers the letters."*

**For edits:** Always end with *"Keep everything else exactly the same"* and list what to preserve.

**For background replacement:** Use realistic, specific locations. Over-dramatic backgrounds look fake.

## Typography

**Big titles/hero text:** Use FAL model via `edit` — it handles large text well and integrates it into the scene naturally.

**Precise small text** (credits, URLs, badges): Use `compose` or `text` with Satori. On a 1080px image, nothing under 36px is readable. Max 3 text sizes per image.

## Common Workflows

### Simple: Generate an image
```bash
picture-it generate --prompt "dark cosmic background with nebula" --size 1200x630 -o bg.png
```

### Simple: Add text to an image
```bash
picture-it text -i bg.png --title "Hello World" --font "Space Grotesk" --color white --font-size 64 -o hero.png
```

### Medium: Blog header with AI background + text
```bash
picture-it generate --prompt "abstract dark tech background" --size 1200x630 -o bg.png
picture-it text -i bg.png --title "My Blog Post" --font "DM Serif Display" --font-size 72 -o header.png
picture-it grade -i header.png --name cinematic -o header-graded.png
```

### Advanced: Text behind subject (YouTube thumbnail)
```bash
picture-it generate --prompt "runner on mountain trail at golden hour" --model flux-dev --size 1280x720 -o runner.png
picture-it edit -i runner.png --prompt "Add 'RUN FASTER' in large bold black letters BEHIND the runner — the runner's body overlaps the text" --model seedream -o thumbnail.png
```

### Advanced: Product comparison
```bash
picture-it remove-bg -i product-a.png --model bria -o a-cutout.png
picture-it remove-bg -i product-b.png --model bria -o b-cutout.png
picture-it generate --prompt "split gradient, blue left to orange right" --size 1200x630 -o bg.png
picture-it compose -i bg.png --overlays overlays.json -o comparison.png
```

## Platform Presets

Use `--platform <name>` with `generate` or `crop`:

| Preset | Size |
|---|---|
| `blog-featured` | 1200x630 |
| `og-image` | 1200x630 |
| `youtube-thumbnail` | 1280x720 |
| `instagram-square` | 1080x1080 |
| `instagram-story` | 1080x1920 |
| `twitter-header` | 1500x500 |

## Output Behavior

- **stdout**: only the output file path
- **stderr**: progress logs
- **Exit 0** on success, **Exit 1** on failure

## Gotchas

- Always use `--model bria` for `remove-bg` — the default birefnet leaves rectangular artifacts.
- The `glow` and `shadow` effects in compose blur the rectangular buffer, not the shape. Avoid on cutout images.
- When editing with FAL, the model may alter product details. For accuracy, use `remove-bg` + `compose` instead.
- SeedDream takes ~60 seconds per generation. Don't assume it failed if it's slow.
- Always `crop` to exact dimensions after FAL generation — FAL models output approximate sizes.
- Use `flux-dev` ($0.03) not `flux-schnell` ($0.003) when quality matters.
- Satori does NOT support: display:grid, transforms, animations, box-shadow, filters. Use flexbox only.
- For text behind a subject with `edit`, be very explicit: "the text is BEHIND the subject — the subject's body overlaps and partially covers the letters."