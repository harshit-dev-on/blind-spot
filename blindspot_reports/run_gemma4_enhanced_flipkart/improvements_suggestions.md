# UX Improvement Suggestions: https://www.flipkart.com

- **Target URL:** https://www.flipkart.com
- **Audit Goal:** Audit website usability and user journey
- **Date:** 2026-10-31T10:02:43.653616+00:00

## 1. Executive Summary
The initial user experience on Flipkart is severely degraded by persistent and unmanageable modal dialogs, specifically the 'Login' overlay, which completely obstructs the main content. For a user with low vision and novice tech skills, the inability to dismiss these popups using standard keyboard/mouse interactions (as demonstrated by the repeated failures) creates an immediate and insurmountable barrier to entry. The reliance on intrusive modals for basic interactions severely compromises usability, forcing the user to spend all available steps attempting to close a window rather than engaging with the shopping journey.

## 2. Interactive Journey Summary
- **Total Steps Taken:** 4
- **Key Milestones Explored:** The user attempted to interact with the landing page but was repeatedly blocked by a large, non-dismissible 'Login' modal overlay. All four observed steps involved attempting to dismiss this modal using the 'Escape' key, resulting in repeated action failures and no progression into browsing or searching.

## 3. Improvement Suggestions
*(Every suggestion must be backed by an observed screenshot evidence link)*

### Suggestion 1: Layout <Modal Management> Persistent and Unskippable Overlays
- **Observed Behavior:** A large modal dialog titled 'Login' consistently appears upon landing on the homepage and cannot be dismissed using the 'Escape' key, as evidenced across Steps 0 through 4.
- **UX Friction / Impact:** This creates an immediate, high-stress barrier for a novice user. For someone with low vision, being unable to dismiss an overlay without knowing specific interaction patterns leads to frustration and complete abandonment of the task.
- **Suggested Improvement:** Implement a clear, highly visible 'Close' button (e.g., an 'X' icon) within all modal dialogs, ensuring it meets WCAG contrast standards. Furthermore, consider making login prompts optional or accessible via a less intrusive banner element rather than a full-screen modal on initial load.
- **Evidence:** screenshots/step-000.png

### Suggestion 2: Touch Target <Modal Dismissal> Ineffective Escape Key Handling
- **Observed Behavior:** In all four interaction steps, attempting to press 'Escape' to dismiss the modal resulted in a timeout error, indicating the system did not correctly register the dismiss action.
- **UX Friction / Impact:** For a user relying on keyboard navigation (common for low vision users), the failure of the primary expected dismissal method renders the modal functionally permanent and inaccessible.
- **Suggested Improvement:** Ensure robust focus management and keyboard trap prevention for all modal components. The 'Escape' key must reliably trigger the modal's dismissal function.
- **Evidence:** screenshots/step-001.png

### Suggestion 3: Typography <Information Density> Lack of Contextual Clarity on Initial Load
- **Observed Behavior:** The page title ("Online Shopping Site for Mobiles, Electronics, Furniture, Grocery, Lifestyle, Books & More. Best Offers!") is present, but the immediate focus is hijacked by the login modal, obscuring the primary navigational cues.
- **UX Friction / Impact:** Low vision users need clear, scannable headings and immediately visible primary actions (Search Bar, Categories). The modal prevents this critical initial orientation.
- **Suggested Improvement:** Ensure the primary site navigation (Search Bar, main category links) is visually dominant and positioned above any secondary, optional interaction prompts like login modals.
- **Evidence:** screenshots/step-000.png

### Suggestion 4: Layout <Visual Hierarchy> Modal Dominance Over Content
- **Observed Behavior:** The 'Login' modal completely overlays and visually obscures the underlying product listings and main navigation area of the Flipkart homepage.
- **UX Friction / Impact:** This forces the user to perform a difficult, high-cognitive load task (defeating a pop-up) before they can even assess the site's content or offerings, which is exhausting for novice users.
- **Suggested Improvement:** Implement a layered UI approach. Optional prompts should use non-modal overlays or small banners that fade away, preserving the underlying content's visibility and structure.
- **Evidence:** screenshots/step-002.png

### Suggestion 5: Navigation <Accessibility> Reliance on Single-Action Prompts
- **Observed Behavior:** The entire user journey observed was a repeated attempt to resolve a single, persistent issue (the modal), indicating that the primary pathways (Search, Browse Categories) are inaccessible until the modal is cleared.
- **UX Friction / Impact:** This violates the principle of discoverability. The user cannot explore the site's value proposition because the entry point is blocked by a required authentication step presented as a roadblock.
- **Suggested Improvement:** Provide multiple, clearly labeled entry points for users who do not wish to log in immediately (e.g., a "Continue Shopping" button outside the modal, or a clear link to browse without logging in).
- **Evidence:** screenshots/step-003.png
