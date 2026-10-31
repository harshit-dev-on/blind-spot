# UX Improvement Suggestions: http://localhost:8088

- **Target URL:** http://localhost:8088
- **Audit Goal:** Audit website usability and user journey
- **Date:** 2026-10-31T10:50:00Z

## 1. Executive Summary
The live audit conducted as Elena, a senior user with low vision and novice technical skills, verified a fully functional e-commerce workflow from product discovery through checkout confirmation on MediCare. While the core transactional flow functions reliably, notable usability and accessibility friction exists around placeholder text simulating form values, low-contrast text on critical metadata and badges, and subtle quantity selectors that lack distinct tactile affordances.

## 2. Interactive Journey Summary
- **Total Steps Taken:** 11
- **Key Milestones Explored:** Homepage overview -> Search filtering for 'Pain relief' -> Product selection and addition to cart -> Cart verification and pricing review -> Checkout delivery form validation -> Order placement and confirmation in 'My orders'.

## 3. Improvement Suggestions
*(Every suggestion must be backed by an observed screenshot evidence link)*

### Suggestion 1: Form <Deceptive Placeholder Text Appearing as Pre-filled Values>
- **Observed Behavior:** In the checkout delivery address form (Step 4 & Step 7), fields like 'Full name' and 'City' display gray placeholder values ('Alex Morgan', 'Kolkata') that look identical to pre-filled input values, yet the form rejects submission with a generic toast error 'Please complete the delivery details.'
- **UX Friction / Impact:** Senior and novice users assume the system already knows their account name and city, leading to confusion and frustration when the submission is blocked without inline field-specific error highlights.
- **Suggested Improvement:** Either auto-populate the actual input values with user account defaults or use standard top labels with distinct floating placeholders (e.g. 'e.g. Jane Doe'), and provide red inline validation borders on empty required fields upon submit.
- **Evidence:** screenshots/step-007.png

### Suggestion 2: Contrast <Low Visual Contrast on Category Headers and Strike-through Prices>
- **Observed Behavior:** On the homepage and search results (Step 0 & Step 1), eyebrow headers ('HEALTHCARE MADE SIMPLE', 'ONLINE PHARMACY') and strike-through original prices (e.g., '₹38' on Paracetamol) are rendered in very light green and pale gray (`#cbd5e1`) against white backgrounds.
- **UX Friction / Impact:** Users with low vision cannot read the original savings or the section eyebrow headers, failing WCAG AA 4.5:1 minimum contrast thresholds.
- **Suggested Improvement:** Darken muted text and strikethrough prices to a minimum contrast ratio of 4.5:1 (e.g., `#475569` or darker).
- **Evidence:** screenshots/step-001.png

### Suggestion 3: Touch Target <Compact Quantity Increment and Decrement Buttons in Cart>
- **Observed Behavior:** On the Shopping Cart page (Step 3), the quantity decrement (`−`) and increment (`+`) buttons have compact clickable hitboxes with minimal padding and faint border outlines.
- **UX Friction / Impact:** Older adults with mild hand tremors or reduced fine-motor accuracy struggle to tap the exact plus/minus targets without misclicking the adjacent item card or background.
- **Suggested Improvement:** Increase touch target dimensions to at least 44x44 CSS pixels with bold, high-contrast button backgrounds (e.g. solid filled pill controls).
- **Evidence:** screenshots/step-003.png

### Suggestion 4: Navigation <Unlabeled Micro-Icons in Left Sidebar>
- **Observed Behavior:** Left sidebar menu navigation items use small geometric or emoji glyphs (⌂, ▦, ▤, 📦, ◉) adjacent to text labels.
- **UX Friction / Impact:** For users with reduced acuity, the small icon shapes add visual noise without providing unambiguous semantic meaning.
- **Suggested Improvement:** Use standard, well-recognized SVG iconography with a consistent 20px size and explicit `aria-label` or `aria-current="page"` indicators for the active route.
- **Evidence:** screenshots/step-000.png

### Suggestion 5: Feedback <Transient Toast Notification Without Persistent Order Receipt in Checkout>
- **Observed Behavior:** Submitting the order immediately redirects to 'My orders' with a brief floating bottom-right toast ('Demo order placed successfully.') that fades after a few seconds.
- **UX Friction / Impact:** Cautious senior shoppers seek reassurance and an explicit order summary card confirming delivery address, estimated delivery date, and order number before navigating away.
- **Suggested Improvement:** Render a dedicated Order Confirmation page with a printable receipt summary, tracking timeline, and clear next steps before directing the user to general order history.
- **Evidence:** screenshots/step-011.png
