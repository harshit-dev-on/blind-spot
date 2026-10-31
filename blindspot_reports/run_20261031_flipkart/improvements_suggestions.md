# UX Improvement Suggestions: https://www.flipkart.com

- **Target URL:** https://www.flipkart.com/
- **Audit Goal:** Audit website usability and user journey
- **Date:** 2026-10-31T09:47:30.000000+00:00

## 1. Executive Summary
The live audit of Flipkart from the perspective of Elena (Senior User with Low Vision & Novice Tech) identified severe friction points across initial discovery, category browsing, diopter specification visibility, and cart persistence. The immediate obstruction by an unprompted login modal, empty white screens upon clicking top navigation categories, and truncated medical/optical product specifications significantly hinder autonomous browsing for elderly and low-vision shoppers.

## 2. Interactive Journey Summary
- **Total Steps Taken:** 10
- **Key Milestones Explored:** Homepage landing modal dismissal -> Category navigation failure ('Books') -> Search execution for 'reading glasses' -> Product search results evaluation -> Product details page inspection -> Cart verification and login barrier detection.

## 3. Improvement Suggestions
*(Every suggestion must be backed by an observed screenshot evidence link)*

### Suggestion 1: Layout <Intrusive Pre-Browsing Login Modal>
- **Observed Behavior:** Upon landing on the homepage (Step 0), a full-screen blocking modal overlay demanding a phone number appears immediately before the user has seen any merchandise or expressed intent to purchase.
- **UX Friction / Impact:** For elderly and novice users like Elena, unexpected modal popups create anxiety, cognitive overload, and the false impression that browsing requires account registration. The close button is located in the external corner and lacks descriptive labeling.
- **Suggested Improvement:** Eliminate premature blocking login dialogs. Allow users to freely explore categories and products, deferring authentication until the final checkout step.
- **Evidence:** `screenshots/step-000.png`

### Suggestion 2: Navigation <Blank White Screen on Category Header Interaction>
- **Observed Behavior:** Clicking the top-level 'Books' category navigation icon (Step 2) loaded a completely blank white viewport beneath the header with zero progress indicators, skeleton loaders, or feedback.
- **UX Friction / Impact:** Low-vision and novice users are left stranded assuming the application has frozen or crashed. Without skeleton loaders or fallback content, users lose orientation.
- **Suggested Improvement:** Implement immediate visual skeleton screens and ensure top navigation categories reliably route to their corresponding department landing pages.
- **Evidence:** `screenshots/step-002.png`

### Suggestion 3: Typography <Low Contrast in Search Autocomplete Subheadings>
- **Observed Behavior:** Typing a query into the primary search bar (Step 3) triggers an autocomplete dropdown where subcategory breadcrumbs (e.g., 'in Reading Glasses', 'in Frames') are rendered in light blue text against a pure white background.
- **UX Friction / Impact:** The contrast ratio fails WCAG AA standards (falling below 3:1), rendering the category distinctions invisible to users with reduced visual acuity.
- **Suggested Improvement:** Darken secondary category text to a minimum 4.5:1 contrast ratio (e.g., `#2874F0` or `#1A53B0`) and increase font size to at least 14px.
- **Evidence:** `screenshots/step-003.png`

### Suggestion 4: Layout <Truncation of Critical Optical Specifications in Catalog Grid>
- **Observed Behavior:** In the product search results grid (Step 4), product title diopters are aggressively truncated with ellipsis (e.g. `+1.0...`, `+2....`).
- **UX Friction / Impact:** For reading glasses, the diopter power (+1.50, +2.00, +2.50) is the most critical deciding factor. Truncating this value forces elderly users to click into every individual product card just to confirm the power rating.
- **Suggested Improvement:** Provide dedicated, untruncated badge pills for key technical specifications (such as Optical Power, Dimensions, or Compatibility) directly on search result cards.
- **Evidence:** `screenshots/step-004.png`

### Suggestion 5: Layout <Delayed Image Hydration & Placeholder Blocks on Product Detail Page>
- **Observed Behavior:** Upon opening the product page (Step 5), the entire image gallery rendered as four large blank grey boxes while surrounding text had already populated.
- **UX Friction / Impact:** Visually impaired users rely heavily on high-resolution imagery to verify frame thickness and build quality. Blank placeholders create confusion about whether images are missing or broken.
- **Suggested Improvement:** Prioritize hero image loading with lightweight progressive blurred thumbnails or shimmer placeholders rather than flat grey rectangles.
- **Evidence:** `screenshots/step-005.png`

### Suggestion 6: Form <Silent Cart Rejection for Unauthenticated Shoppers>
- **Observed Behavior:** Clicking 'Add to cart' on the product page followed by navigating to Cart (Step 10) displayed 'Missing Cart items? Login', discarding the user's item selection.
- **UX Friction / Impact:** Senior users expect cart items to persist in their browser session. Forcing authentication and wiping guest cart state creates severe abandonment and purchase frustration.
- **Suggested Improvement:** Retain guest cart items in `localStorage` or session cookies, and seamlessly merge guest items when the user eventually logs in during checkout.
- **Evidence:** `screenshots/step-010.png`
