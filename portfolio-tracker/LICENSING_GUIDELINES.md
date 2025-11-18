# Licensing Guidelines

These guidelines document how the InsightPort project applies Creative Commons licensing today and what the team must do when sharing the product internally or preparing a public release.

## 1. Current Licensing Model

- **License:** Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0).
- **Ownership:** InsightPort © 2025 by Filip Naskręt.
- **Scope:** All project assets in this repository (code, copy, UI assets) unless a file explicitly states a different license.
- **Icon Assets:** Creative Commons icons are stored locally in `portfolio-tracker-pro/frontend/public/licenses/` and may be re-used under the same license.

## 2. Internal Use Checklist

Before deploying the product inside the organization:

1. Ensure the footer attribution renders correctly in the UI (see `portfolio-tracker-pro/frontend/src/App.tsx`).
2. Bundle the `LICENSE` file with every internal distribution (source archives, ZIPs, documentation bundles).
3. Preserve the CC footer text and icons in any PDF or HTML exports generated from the app.
4. Do not remove or modify the links to the author (`http://localhost`) or the license.

## 3. Sharing Outside the Team (Non-Commercial)

You may share the unmodified project externally for evaluation or collaboration under these conditions:

- Include the unaltered `LICENSE` file and this guideline document.
- Provide attribution in the README or cover letter using the text:
  `InsightPort © 2025 by Filip Naskręt is licensed under CC BY-NC-ND 4.0`.
- Link to `https://creativecommons.org/licenses/by-nc-nd/4.0/`.
- Do **not** charge for access, hosting, or support without written approval from the author.
- Do **not** publish modified builds or forks—share the original repository or official releases only.

## 4. Handling Commercial or Derivative Requests

1. Collect the requester’s details (company name, intended use, scope, timeline).
2. Escalate the request to Filip Naskręt for approval.
3. Document the outcome (approved/rejected) in the business CRM or shared decision log.
4. If approved, prepare a separate agreement (e.g., commercial license, dual-licensing plan) before granting access.

## 5. Preparing for a Future Public Release

If the project is opened to the public or the license changes:

1. Confirm the new license choice (e.g., CC BY-SA, MIT) and update `LICENSE`, `README.md`, and footer attribution.
2. Replace footer text and icons to match the new license terms.
3. Update this document with the new policy and communicate the change to all maintainers.
4. Tag the repository with a release note summarizing the licensing change.

## 6. Asset & Icon Management

- All Creative Commons icons are downloaded locally so the UI works offline.
- If you add new license icons, store them in `portfolio-tracker-pro/frontend/public/licenses/` and keep filenames lowercase (`cc.svg`, `by.svg`, etc.).
- When exporting reports, ensure the icons are embedded or accessible so the attribution remains intact.

## 7. Responsibilities

- **Maintainer:** Filip Naskręt (primary contact for licensing decisions).
- **Developers:** Must follow section 2 when shipping builds.
- **Product/Legal:** Review section 4 before agreeing to any external licensing change.

Keeping these steps documented ensures we remain compliant today and retain the flexibility to adopt a different license when the project goes public.



