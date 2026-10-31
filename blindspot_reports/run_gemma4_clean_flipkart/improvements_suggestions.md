# UX Improvement Suggestions: https://www.flipkart.com

- **Target URL:** https://www.flipkart.com
- **Audit Goal:** Audit website usability and user journey
- **Date:** 2026-10-31T10:19:48.399939+00:00

## 1. Executive Summary
The user successfully navigated the search function to find 'reading glasses,' demonstrating a functional search path. However, the experience presents significant usability challenges for a novice user with low vision. Key friction points include potentially low contrast on certain elements, and the product selection process requires precise interaction with small, dense detail options. The reliance on sequential clicks within product variations (Steps 4 and 5) creates cognitive load, which is especially taxing for less tech-savvy users needing clear confirmation of selections.

## 2. Interactive Journey Summary
- **Total Steps Taken:** 5
- **Key Milestones Explored:** Initiated search for 'reading glasses' on the homepage (Step 0 & 1). Navigated to the search results page (Step 2). Selected the first product listing (Step 3). Interacted with product variation selectors (specifically selecting '1.00' in Step 4). Attempted final selection/purchase confirmation on the Product Detail Page (Step 5).

## 3. Improvement Suggestions

### Suggestion 1: Typography & Information Density <Insufficient Readability in Product Listing>
- **Observed Behavior:** On the search results page (Step 2), product information is densely packed with small text blocks and multiple overlapping promotional elements.
- **UX Friction / Impact:** For Elena, who has low vision, the small font size and high information density make scanning and accurately reading product names, prices, and key features extremely difficult, increasing the risk of selecting the wrong item.
- **Suggested Improvement:** Implement a scalable text size hierarchy on product cards. Ensure that product titles and core pricing information use a minimum of 16px font size with sufficient leading (line spacing) to aid legibility.
- **Evidence:** screenshots/step-002.png

### Suggestion 2: Touch Target Size & Clarity <Ambiguous Option Selection>
- **Observed Behavior:** During the product detail view (Step 4), the selection options for reading power (e.g., '1.00') are presented as small, adjacent selectable elements.
- **UX Friction / Impact:** A novice user with low vision may struggle to accurately tap the desired power level without hitting an adjacent, unintended option, leading to frustration and repeated errors.
- **Suggested Improvement:** Increase the minimum touch target size (hit area) for all product variation selectors (like power/size selectors) to meet WCAG AA standards (minimum 44x44 CSS pixels). Visually group these options clearly.
- **Evidence:** screenshots/step-004.png

### Suggestion 3: Navigation & Workflow <Redundant Confirmation Clicks>
- **Observed Behavior:** In Step 5, the user clicks the already-selected '1.00' option again, suggesting the interface requires redundant confirmation steps even when the desired state is already active.
- **UX Friction / Impact:** This adds unnecessary cognitive load. For a novice user, this ambiguity—is the selection *truly* confirmed, or is the click necessary?—creates doubt about the purchase path.
- **Suggested Improvement:** The interface must clearly indicate the *active* selection state (e.g., using a distinct, high-contrast border or checkmark) rather than requiring the user to re-tap the active element to proceed to 'Buy.'
- **Evidence:** screenshots/step-005.png

### Suggestion 4: Contrast & Visual Hierarchy <Low Contrast on Informational Text>
- **Observed Behavior:** While the primary action buttons might be high contrast, ancillary text elements on the product page (such as descriptions or minor feature details) appear to use a muted grey against a white background.
- **UX Friction / Impact:** Low contrast ratios significantly impair readability for users with low vision, forcing them to strain their eyes to distinguish text from the background.
- **Suggested Improvement:** Audit all non-critical text elements (e.g., seller ratings, detailed specs) to ensure a minimum contrast ratio of 4.5:1 against the background, preferably using a darker, discernible grey.
- **Evidence:** screenshots/step-000.png

### Suggestion 5: Layout & Focus Management <Lack of Clear Next Step Indication>
- **Observed Behavior:** After selecting options (Step 4/5), the primary call-to-action (CTA) like "Buy at ₹411" is positioned, but the visual flow from the configuration area to the final purchase button is not strongly guided.
- **UX Friction / Impact:** The user needs a clear, unambiguous visual path to the final purchase button. If the CTA is not visually distinct or follows a clear reading path, the user may miss it or hesitate, especially if the page scroll position is unclear.
- **Suggested Improvement:** Ensure the final purchase CTA ('Buy at ₹411') is visually dominant—larger, using the site’s primary action color, and placed immediately following the configuration options, possibly with a slight visual separation block.
- **Evidence:** screenshots/step-003.png
