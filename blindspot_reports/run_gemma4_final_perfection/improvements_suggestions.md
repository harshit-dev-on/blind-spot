# UX Improvement Suggestions: https://www.flipkart.com

- **Target URL:** https://www.flipkart.com
- **Audit Goal:** Audit website usability and user journey
- **Date:** 2026-10-31T10:10:16.348837+00:00

## 1. Executive Summary
The initial user experience is severely hampered by intrusive, mandatory overlay modals (login prompts) that block core shopping functionality, forcing the user to waste multiple steps trying to dismiss them. For a novice user with low vision, this constant interruption creates significant cognitive load and frustration. While the search functionality is present, the reliance on complex modal dismissal patterns makes the entry point unnecessarily difficult. Improving modal management and ensuring high contrast on key elements are critical for accessibility and usability improvements.

## 2. Interactive Journey Summary
- **Total Steps Taken:** 5
- **Key Milestones Explored:** The user's journey was dominated by repeatedly attempting to close an intrusive login modal using the 'Escape' key (Steps 1-3). After finally dismissing the modal (Step 4), the user successfully navigated to the primary search bar and entered the query "reading glasses" (Step 5).

## 3. Improvement Suggestions
*(Every suggestion must be backed by an observed screenshot evidence link)*

### Suggestion 1: Layout <Modal Barrier> Non-Skippable Initial Modals
- **Observed Behavior:** Upon landing on the homepage (Step 0), a large, intrusive login modal immediately overlays the entire screen content, preventing the user from viewing or interacting with the main site navigation or product listings.
- **UX Friction / Impact:** For a novice user, this creates an immediate and insurmountable barrier to entry. For a user with low vision, the modal obscures critical visual anchors (like navigation menus or search bars), forcing them to spend time troubleshooting the overlay instead of shopping.
- **Suggested Improvement:** Change the initial login prompt from a mandatory, full-screen overlay to a less intrusive banner or a clear, dismissible prompt accessible via a small icon.
- **Evidence:** screenshots/step-000.png

### Suggestion 2: Navigation <Modal Dismissal> Inconsistent Modal Interaction
- **Observed Behavior:** The system repeatedly failed to dismiss the modal using the 'Escape' key across multiple attempts (Steps 1, 2, and 3), indicating a failure in the modal's focus management or event listener handling.
- **UX Friction / Impact:** Inconsistent or failed dismissal controls drastically increases user anxiety and perceived technical failure, especially for users unfamiliar with web interactions.
- **Suggested Improvement:** Ensure that all modal dialogs are correctly coded to respond reliably to the 'Escape' keypress, providing immediate and predictable dismissal feedback.
- **Evidence:** screenshots/step-001.png (and subsequent steps showing failed dismissal attempts)

### Suggestion 3: Typography <Contrast/Sizing> Element Readability within Overlays
- **Observed Behavior:** While the modal's content is present in the screenshots (Step 0), the visual presentation of its elements is often low contrast against the background or the modal box itself, making text difficult to parse for low-vision users.
- **UX Friction / Impact:** Low contrast forces users with low vision to strain or zoom in excessively, leading to fatigue and task abandonment.
- **Suggested Improvement:** Review the color palette used for all modal text and interactive elements to ensure WCAG AA compliance (minimum 4.5:1 contrast ratio).
- **Evidence:** screenshots/step-000.png

### Suggestion 4: Touch Target <Affordance> Clear Dismissal Controls
- **Observed Behavior:** The user was unable to reliably close the modal until a specific element (`@e109`) was targeted in Step 4, suggesting that the primary visual cue for dismissal (e.g., an 'X' icon) may be too small or poorly positioned within the modal structure.
- **UX Friction / Impact:** Small, ambiguous targets force users to precisely aim, which is difficult for users with reduced motor control or low vision.
- **Suggested Improvement:** Increase the size and visual prominence of the close button (e.g., the 'X' icon) on all overlaid elements to meet minimum touch target size recommendations (44x44 CSS pixels).
- **Evidence:** screenshots/step-004.png

### Suggestion 5: Layout <Search Input> Prominence and Labeling
- **Observed Behavior:** After successfully navigating past the modal, the search bar is visible at the top (Step 5). However, the initial context provided by the surrounding elements is sparse, relying heavily on the user knowing where to look for the search functionality.
- **UX Friction / Impact:** For a novice user, the search field might not be immediately obvious as the primary input area if it lacks a clear, high-contrast label or placeholder text, leading to hesitation.
- **Suggested Improvement:** Ensure the search input field has clear, persistent visual labeling (or a very descriptive placeholder) that remains visible even when the modal is dismissed, guiding the user immediately to the intended task.
- **Evidence:** screenshots/step-005.png
