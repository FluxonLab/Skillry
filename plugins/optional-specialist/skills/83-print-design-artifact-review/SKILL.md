---
name: print-design-artifact-review
description: Use when you need to review print-ready design artifacts, NFC cards, QR codes, bleed, export formats, and production handoff.
---

# Print Design Artifact Review

## Purpose
Review design files and exported artifacts intended for physical printing: NFC business cards, loyalty cards, menu cards, flyers, and posters. Verify print-readiness: color mode (CMYK), resolution (300 DPI minimum), bleed and trim, font embedding, PDF/X compliance, QR code scannability at printed size, and NFC chip placement compatibility.

## When to use
- Reviewing design files (Figma export, Illustrator, Canva PDF) before sending to a print vendor.
- Auditing QR code or NFC card artwork for production hand-off.
- Checking bleed, safe zone, and trim marks on any card, flyer, or poster design.
- Reviewing PDF exports for font embedding and color profile correctness.
- Evaluating NFC card designs for chip placement restrictions and antenna zone clearance.

## When not to use
- Digital-only assets (web banners, social media images) — no print standards apply.
- Code review of the software that generates print-ready PDFs — use a general code review skill for that.
- Photography editing or brand identity design critique — scope is technical print readiness, not aesthetic judgment.

## Procedure

### 1. Color mode
- All elements must be in **CMYK** mode — RGB colors shift unpredictably in print; blues often become purple, bright reds become dull.
- Spot colors (Pantone): if specified, verify color names exactly match the vendor's supported Pantone library (Pantone Solid Coated, Solid Uncoated, etc.).
- Black text and fine elements: use **100% K only** (not Rich Black `C:60 M:40 Y:40 K:100`) to prevent misregistration blur on small text.
- Rich Black is appropriate only for large background fills (> 1 cm²).
- White elements: confirm they are set to 0% of all CMYK channels — "white" in RGB that is never converted to true CMYK white will print as a light tint.
- Total ink coverage: most offset print vendors cap at **300% TAC** (Total Area Coverage). Verify dark areas do not exceed this.

### 2. Resolution
- Raster images: minimum **300 DPI** at the final print size. An image placed at 50% of its pixel size has effectively 600 DPI — safe. An image stretched to 200% has 150 DPI — unacceptable.
- Check the effective DPI of every placed raster image, not just the document resolution.
- Logos and icons should be **vector** (SVG/EPS/AI paths), not rasterized PNG/JPG. A vector logo looks sharp at any size.
- QR codes must be vector (SVG) or raster at ≥ 600 DPI at the final printed size. A blurry QR will fail to scan.
- NFC chip activation indicator graphics (tap icon, signal waves) must also be vector.

### 3. Bleed, trim, and safe zone
- **Bleed**: artwork that reaches the card/page edge must extend **3 mm beyond the trim line** (2 mm for some vendors — confirm before handoff). Background color, photos, and full-bleed elements must fill the bleed zone.
- **Trim line**: the intended final cut edge of the card or page.
- **Safe zone**: all critical content (text, logos, QR codes, NFC tap indicators) must be kept **≥ 3 mm inside the trim line**. Content outside the safe zone risks being cut off.
- Standard card size (CR80): 85.6 × 54 mm trim; artwork canvas should be 91.6 × 60 mm (with 3 mm bleed on all sides).
- Verify the document canvas dimensions include bleed; trim marks should be visible in the PDF.

### 4. Font embedding and typography
- All fonts must be **fully embedded** in the exported PDF. Unembedded fonts will substitute at the print shop, changing layout and appearance.
- Alternatively, convert all text to **outlines/curves** before export — this eliminates font dependency but prevents text editing post-export.
- Font size minimums for legibility: body text ≥ 6 pt for standard paper; fine print ≥ 5 pt. Below 4 pt, ink spread makes text unreadable on most substrates.
- Tracking/kerning on small text (< 8 pt): slightly positive tracking (+20–40 units) improves legibility in print.
- Avoid very thin font weights (< 100 weight, hairline strokes < 0.25 pt) in white on dark — ink spread can close the letterforms.

### 5. PDF/X compliance
- Export target: **PDF/X-1a** (single-file, CMYK/spot only, fonts embedded, no transparency) or **PDF/X-4** (allows transparency and layers, required for some modern RIPs).
- Confirm with the vendor which PDF/X version they require before export.
- PDF/X-1a: no RGB, no transparency. Flatten all transparencies before export.
- PDF/X-4: transparency is preserved; the RIP handles flattening.
- Verify the PDF contains no JavaScript, no form fields, no multimedia — these are invalid in PDF/X.
- Color profile: embed the correct output intent ICC profile as required by the vendor (e.g., FOGRA39 for European coated offset, SWOP for US).

### 6. QR code — print size and scannability
- Minimum printed QR size: **2 × 2 cm** for error correction level M; **1.5 × 1.5 cm** for level H — below this, scanners reliably fail.
- Quiet zone: white margin around the QR must be at least **4 module widths** on all sides. No background patterns or content should enter the quiet zone.
- Color: QR code modules must be dark (≥ 60% K or equivalent) on a light background (contrast ratio ≥ 4:1). Avoid printing QR in spot colors that appear light after printing.
- Test the final artwork by scanning a proof at actual printed size before approving.
- Do not rotate a QR code more than 90° — most scanners handle 90° rotation but some readers fail beyond that.

### 7. NFC card specifics
- NFC antenna location: most standard CR80 NFC cards have the antenna embedded in the card body occupying approximately the central 70% of the card area. Verify chip vendor datasheet for exact exclusion zones.
- Do not place metallic inks, foil stamps, or metallic laminates directly over the antenna — they block NFC signal.
- Embossing and debossing directly over the antenna can crack the antenna wire — maintain ≥ 3 mm clearance.
- The "tap here" indicator graphic should be placed near the antenna center (usually card center) to guide users to the correct tap zone.
- If the chip is on one side only, indicate the correct face with the tap icon on that side.
- Card thickness: standard CR80 is 0.76 mm. Thicker substrates or overlaminates > 1.5 mm total stack can reduce NFC read range.

### 8. Production handoff checklist
- Confirm the print vendor's file specification document (substrate, laminate, coating type, color profile, bleed requirement, file format) before exporting.
- Package files: provide PDF/X + original source file + embedded images folder if the vendor requests editable files.
- Naming: use a clear naming convention: `ProjectName_CardFront_v3_PRINT.pdf` — never `final_final2.pdf`.
- Color proof: request a **digital proof** (PDF soft proof) and a **physical color proof** (strike-off) for first production run.
- Quantities and die lines: confirm the correct dieline template from the vendor is used for custom shapes.

## Checklist

Color:
- [ ] Document color mode is CMYK (not RGB).
- [ ] Spot/Pantone colors match vendor's supported library exactly.
- [ ] Black text uses 100% K only.
- [ ] Total ink coverage ≤ 300% TAC on dark areas.

Resolution:
- [ ] All placed raster images ≥ 300 DPI at final print size.
- [ ] Logos and icons are vector.
- [ ] QR code is vector or ≥ 600 DPI at final size.

Bleed and trim:
- [ ] Bleed extends ≥ 3 mm beyond trim on all sides.
- [ ] Critical content (text, QR, logos) is ≥ 3 mm inside trim line.
- [ ] Document canvas dimensions include bleed (e.g., 91.6 × 60 mm for CR80).
- [ ] Trim marks visible in exported PDF.

Fonts:
- [ ] All fonts embedded in PDF or converted to outlines.
- [ ] No text below 5 pt.

PDF export:
- [ ] PDF/X-1a or PDF/X-4 as required by vendor.
- [ ] No transparency in PDF/X-1a export.
- [ ] No JavaScript, form fields, or multimedia in PDF.
- [ ] Correct ICC output intent profile embedded.

QR code:
- [ ] Minimum 2 × 2 cm printed size (error correction M or H).
- [ ] Quiet zone ≥ 4 modules on all sides, clear of background patterns.
- [ ] High contrast (dark modules on light background).
- [ ] Physically scanned proof tested before approval.

NFC card:
- [ ] No metallic ink or foil over antenna zone.
- [ ] Tap indicator positioned over antenna center.
- [ ] Embossing/debossing maintains ≥ 3 mm clearance from antenna.

## Common issues & anti-patterns

- **RGB PDF sent to printer**: colors shift; blues go purple, greens go yellow. Always convert to CMYK before export.
- **Low-resolution logo rasterized**: a logo screenshotted from a website at 72 DPI prints as a blurry blob. Always use original vector files.
- **Bleed missing on background**: when the background stops at the trim line, paper-white edges appear at the cut if the cutter shifts even 0.5 mm.
- **QR too small**: a 1 × 1 cm QR at error correction L is unreliable — many phones fail to scan it, especially in dim lighting.
- **Metallic foil over NFC antenna**: the card's NFC stops working the moment the foil is applied. Check the antenna map from the card manufacturer.
- **Rich Black on thin text**: `C:60 M:40 Y:40 K:100` on 8 pt text causes color misregistration (slight CMYK plate misalignment) producing a blurry colored halo around letters.
- **Font not embedded — substituted at print shop**: the printer's RIP substitutes a default font, reflowing the layout and cutting off text.
- **No physical proof ordered for first run**: color differences between screen and print are only caught by a physical proof. Digital-only proofing misses substrate and coating effects.

## Required output

Return a structured report with:
- **Summary**: print-ready / needs corrections / blocked (critical production issue).
- **Color assessment**: mode, TAC, black type treatment.
- **Resolution audit**: each placed image — source DPI, effective DPI at print size, pass/fail.
- **Bleed and safe zone status**: measured bleed extension, content clearance from trim.
- **QR/NFC integrity**: size, quiet zone, antenna clearance.
- **Findings table**: severity (critical / high / medium / low / info), category, description, remediation.
- **Vendor handoff readiness**: list of files required, naming, proof type recommended.

## Safety

- Do not send files to a print vendor or submit a print order during review.
- Do not access or print confidential card data (full card numbers, PINs) that may appear on card artwork samples.
- If artwork contains personal identifiable information (name, phone, address on a business card sample), handle only within the scope of the review and do not distribute.
- Flag any artwork claiming to be a payment card (credit/debit) with realistic card number formatting — confirm it uses a clearly fictional number range (e.g., starting with 0000) to avoid misuse.
