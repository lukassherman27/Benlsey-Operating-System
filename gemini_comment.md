## Gemini UI Architecture Audit: Component Strategy

Following the foundational fixes (Security, Stability, Optimization), here is the architectural guidance for the UI of the Proposals Dashboard, focusing on leveraging the `shadcn/ui` component library effectively.

### Assessment:
The current dashboard is functional, but we can accelerate development and improve consistency by strictly adhering to a component-driven strategy with `shadcn/ui`. We should avoid building custom components when a `shadcn` primitive or composite component already exists.

### Recommended `shadcn/ui` Components for the Proposals Dashboard:

**1. For Layout & Core UI:**
- **`Card`**: The primary container for all dashboard widgets (e.g., "Pipeline Value", "Win Rate"). Use `CardHeader`, `CardTitle`, `CardDescription`, and `CardContent`.
- **`Tabs`**: To switch between different views (e.g., "All Proposals", "My Proposals", "Archived"). The `RoleSwitcher` is a good example of this already.
- **`Table`**: The main component for displaying the list of proposals. It supports sorting, filtering, and pagination which are essential here.
- **`Badge`**: Perfect for displaying proposal statuses (`Proposal Sent`, `Negotiation`, `On Hold`). We can create color-coded variants for at-a-glance understanding.

**2. For Actions & Interactivity:**
- **`Button`**: For all primary actions ("New Proposal") and secondary actions (inside table rows).
- **`Dropdown Menu`**: For the "three-dot" menu on each table row to house actions like "Edit", "Archive", "View History". This keeps the UI clean.
- **`Dialog` / `Drawer`**: For the "Quick Edit" and "New Proposal" forms. Use a `Dialog` for wider screens and a `Drawer` for a better mobile experience.
- **`Command`**: An excellent component for a "quick search" or "jump to project" feature, which would be a huge UX win for power users like Bill.

**3. For Data & Analytics (Features from the issue description):**
- **`Bar Chart` (via Recharts, which `shadcn` styles):** To visualize "Win rate analytics by discipline/country".
- **`Data Table` (with Zustand/React Table):** A more advanced version of the `Table` component to handle the client-side logic for "Bulk status updates".

### Strategic Recommendation:
Before building any new UI for the missing features, the **Frontend Agent** should first ensure all existing dashboard elements are composed from the `shadcn/ui` components listed above. This will create a consistent, maintainable, and visually polished foundation to build upon. This alignment is a prerequisite for adding new UI features.