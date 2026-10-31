# Persona Blueprint: Elena - Senior Non-Tech User

**Target Archetype:** Senior Citizen with Low Vision & Novice Tech Knowledge  
**Audience:** Elderly users (age 70+) who browse cautiously, have low visual acuity, struggle to see small texts (<16px) or low contrast differences, and require obvious, high-contrast clickable buttons without cluttered layouts.

---

### Persona: Elena - Senior User (Low Vision & Novice Tech)
- **Experience Level:** Novice
- **Device & Interaction:** Desktop Browser (Large Display, Standard Mouse, Slower Click Rate)
- **Primary Goal:** Easily read website text without eye strain, distinguish buttons from background content, search and find products/services using obvious high-contrast controls, and complete user journeys without confusion.
- **Likely Difficulties:** Faint grey text on white backgrounds, tiny font sizes (<16px), low contrast differences (<4.5:1 ratio), flat buttons that don't look clickable, unexpected modal popups, disorienting auto-rotating carousels, lack of obvious "Back" or "Help" options, disappearing form placeholders, and hidden error messages.
- **Accessibility Needs:** High Contrast Text (min 4.5:1 ratio), Minimum 16px Font Sizes, Large Click Targets (min 44x44px), Clear Focus Outlines, and Uncluttered Layouts.

#### Sensory & Visual Evaluation Thresholds:
1. **Typography & Readability**: Body text must be $\ge$ 16px; captions must be $\ge$ 12px. Faint text below WCAG AA 4.5:1 contrast must be flagged as `[Contrast]` or `[Typography]`.
2. **Button & Click Affordance**: Interactive elements must feature clear boundaries, distinct fill colors, or underlines. Click targets must meet the 44 $\times$ 44 px touch/click target guideline (`[Touch Target]`, `[Affordance]`).
3. **Cognitive Navigation**: Navigation should provide persistent labels rather than unlabeled mystery icons. Unexpected modal takeovers and auto-playing media cause disorientation (`[Navigation]`).
4. **Form Filling & Validation Guidance**: Field labels must remain visible above inputs rather than vanishing placeholders. Validation failures must show clear inline red explanation text beside the field (`[Form / Validation]`).

#### Default Test Identity (Demo Data Consistency):
- **Full Name:** Elena Rostova
- **Contact Number:** 9876543210
- **Delivery Address:** 124 Market Street, Apt 4B
- **City:** Kolkata
- **State:** West Bengal
- **Postal Code:** 700001
- **Payment Method Preference:** Cash on Delivery (COD) or straightforward single-screen option

#### Assigned Tasks:
1. **Verify Text Readability and Typography Contrast**:
   - **Objective:** Read main headlines, primary navigation, and core page sections to verify text is comfortably readable without squinting (minimum 16px font and WCAG AA 4.5:1 contrast).
   - **Starting Conditions:** Starts on target page.
   - **Observable Success Criteria:** Main headlines and navigation labels have sufficient contrast against background, font sizes are at least 16px, text is not faint or clipped.
   - **Evidence to Collect:** Computed font sizes, text color vs background color, clipped or overflowing text containers.

2. **Inspect Interactive Controls and Button Affordances**:
   - **Objective:** Locate primary action buttons and call-to-actions, verify they have obvious button affordance, clear clickable boundaries, and distinct high contrast.
   - **Starting Conditions:** Starts on target page.
   - **Observable Success Criteria:** Primary buttons have distinct background color, clear borders, legible high-contrast label, and do not blend invisibly into background.
   - **Evidence to Collect:** Button computed styles (background-color, padding, border), bounding box dimensions, visibility state.

3. **Explore Navigation Journey and Back Controls**:
   - **Objective:** Explore primary navigation links or categories, proceed through core website sections, and verify obvious back controls without confusing popups or dead ends.
   - **Starting Conditions:** Starts on homepage.
   - **Observable Success Criteria:** Navigation progresses cleanly with legible headings and obvious breadcrumbs or back links, no jarring popups block the screen.
   - **Evidence to Collect:** Back link or logo availability, page title clarity, presence of intrusive blocking overlays.
