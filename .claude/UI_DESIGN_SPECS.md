# UI/UX DESIGN SPECIFICATIONS
**Bensley Operations Platform - Production Ready Design**

---

## DESIGN PHILOSOPHY

**Reference:** Monday.com, Linear, Notion
**Goal:** Enterprise-grade, professional PM software
**Vibe:** Clean, modern, functional (not flashy)

---

## 1. DESIGN SYSTEM

### Color Palette

```
Primary (Bensley Brand)
- Primary: #0d9488 (teal)
- Primary Hover: #0f766e
- Primary Light: #5eead4

Status Colors
- Success: #10b981 (green)
- Warning: #f59e0b (amber)
- Danger: #ef4444 (red)
- Info: #3b82f6 (blue)

Neutrals
- Gray 950: #030712 (text primary)
- Gray 700: #374151 (text secondary)
- Gray 500: #6b7280 (text muted)
- Gray 300: #d1d5db (borders)
- Gray 100: #f3f4f6 (backgrounds)
- Gray 50: #f9fafb (subtle bg)
- White: #ffffff

Priority Colors (Tasks/RFIs)
- Critical: #dc2626 (red 600)
- High: #f59e0b (amber 500)
- Medium: #3b82f6 (blue 500)
- Low: #64748b (slate 500)
```

### Typography

```
Font Family:
- Primary: Inter (system-ui fallback)
- Monospace: 'JetBrains Mono' (for dates, numbers)

Sizes:
- Heading 1: 32px / 2rem (font-bold)
- Heading 2: 24px / 1.5rem (font-semibold)
- Heading 3: 20px / 1.25rem (font-semibold)
- Body Large: 16px / 1rem (font-normal)
- Body: 14px / 0.875rem (font-normal) ← DEFAULT
- Small: 12px / 0.75rem (font-normal)
- Label: 12px / 0.75rem (font-medium, uppercase)

Line Heights:
- Tight: 1.25
- Normal: 1.5
- Relaxed: 1.75
```

### Spacing (4px Grid)

```
- xs: 4px (0.25rem)
- sm: 8px (0.5rem)
- md: 12px (0.75rem)
- lg: 16px (1rem)
- xl: 24px (1.5rem)
- 2xl: 32px (2rem)
- 3xl: 48px (3rem)
- 4xl: 64px (4rem)

Card Padding: 24px (xl)
Section Spacing: 32px (2xl)
Page Margins: 24px (xl)
```

### Shadows

```
- sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)'
- md: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
- lg: '0 10px 15px -3px rgb(0 0 0 / 0.1)'
- xl: '0 20px 25px -5px rgb(0 0 0 / 0.1)'

Usage:
- Card: shadow-sm (hover: shadow-md)
- Dropdown: shadow-lg
- Modal: shadow-xl
```

### Borders

```
- Width: 1px (default)
- Radius:
  - sm: 4px (buttons, inputs)
  - md: 8px (cards)
  - lg: 12px (modals)
  - full: 9999px (pills, avatars)

- Style: solid
- Color: gray-300 (default)
```

---

## 2. COMPONENT SPECIFICATIONS

### Navigation Sidebar

**Layout:**
```
Width: 280px (desktop)
Collapsed: 64px (icon only)
Mobile: Full-screen overlay

Sections:
1. Logo + Collapse Toggle
2. User Profile Card
3. Main Navigation
4. Secondary Navigation
5. Bottom Actions (Settings, Logout)
```

**User Profile Card:**
```tsx
<Card className="mx-4 mb-4 p-3">
  <Avatar src={user.avatar} size="md" />
  <div>
    <Text weight="semibold">{user.name}</Text>
    <Text size="sm" color="muted">{user.role}</Text>
  </div>
  <Badge>{user.department}</Badge>
</Card>
```

**Navigation Structure:**
```
Dashboard
My Day
---
📊 Proposals
  └─ Tracker
  └─ Overview
---
📁 Projects
  └─ Projects List
  └─ Deliverables
  └─ RFIs
---
👥 Team
  └─ PM Workload
  └─ Contacts
---
📧 Meetings
---
💰 Finance (Role: Executive, Finance only)
---
⚙️ Admin (Role: Admin only)
  └─ Suggestions
  └─ Email Review
  └─ Patterns
  └─ System Status
```

### Dashboard Cards

**Standard Card:**
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Subtitle</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
  <CardFooter>
    <Button variant="ghost" size="sm">View All →</Button>
  </CardFooter>
</Card>
```

**Stat Card:**
```tsx
<Card>
  <div className="flex items-center justify-between">
    <div>
      <Text size="sm" color="muted">Label</Text>
      <Text size="2xl" weight="bold">$1.2M</Text>
      <Text size="sm" color="success">+12% from last month</Text>
    </div>
    <Icon className="h-12 w-12 text-muted" />
  </div>
</Card>
```

### Tables

**Modern Table Style (Monday.com):**
```tsx
<Table>
  <TableHeader sticky>
    <TableRow>
      <TableHead sortable>Project</TableHead>
      <TableHead sortable>Status</TableHead>
      <TableHead sortable>Due Date</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow hoverable clickable>
      <TableCell>
        <div className="flex items-center gap-3">
          <Avatar size="sm" />
          <div>
            <Text weight="medium">Project Name</Text>
            <Text size="sm" color="muted">Code</Text>
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant="success">Active</Badge>
      </TableCell>
      <TableCell>
        <Text tabular>Dec 29, 2025</Text>
      </TableCell>
      <TableCell>
        <DropdownMenu>...</DropdownMenu>
      </TableCell>
    </TableRow>
  </TableBody>
</Table>
```

**Features:**
- Sticky header on scroll
- Sortable columns (click header)
- Row hover state (light gray bg)
- Row click → Navigate to detail
- Inline editing (double-click cell)
- Bulk selection (checkboxes on hover)

### Forms

**Input Fields:**
```tsx
<FormField>
  <Label>Email Address</Label>
  <Input
    type="email"
    placeholder="you@bensley.com"
    error={errors.email}
  />
  <FormDescription>We'll never share your email.</FormDescription>
  <FormMessage>{errors.email}</FormMessage>
</FormField>
```

**Select Dropdowns:**
```tsx
<Select>
  <SelectTrigger>
    <SelectValue placeholder="Select PM" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="1">
      <div className="flex items-center gap-2">
        <Avatar size="xs" src={pm.avatar} />
        <span>{pm.name}</span>
      </div>
    </SelectItem>
  </SelectContent>
</Select>
```

**Date Picker:**
```tsx
<Popover>
  <PopoverTrigger asChild>
    <Button variant="outline">
      <CalendarIcon />
      {date ? format(date, 'PPP') : 'Pick a date'}
    </Button>
  </PopoverTrigger>
  <PopoverContent>
    <Calendar
      mode="single"
      selected={date}
      onSelect={setDate}
    />
  </PopoverContent>
</Popover>
```

### Modals

**Standard Modal:**
```tsx
<Dialog>
  <DialogContent size="lg">
    <DialogHeader>
      <DialogTitle>Add New Task</DialogTitle>
      <DialogDescription>Create a task for this project</DialogDescription>
    </DialogHeader>

    <DialogBody>
      {/* Form fields */}
    </DialogBody>

    <DialogFooter>
      <Button variant="ghost" onClick={onCancel}>Cancel</Button>
      <Button onClick={onSave}>Create Task</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

**Sizes:**
- sm: 400px
- md: 600px
- lg: 800px
- xl: 1000px
- full: 95vw

---

## 3. PAGE LAYOUTS

### Standard Page Layout

```tsx
<Page>
  {/* Page Header */}
  <PageHeader>
    <div className="flex items-center justify-between">
      <div>
        <Breadcrumb>
          <BreadcrumbItem>Projects</BreadcrumbItem>
          <BreadcrumbItem current>25 BK-033</BreadcrumbItem>
        </Breadcrumb>
        <PageTitle>Ritz-Carlton Nusa Dua</PageTitle>
        <PageDescription>Luxury resort in Bali</PageDescription>
      </div>
      <div className="flex gap-2">
        <Button variant="outline">Export</Button>
        <Button>+ Add Task</Button>
      </div>
    </div>
  </PageHeader>

  {/* Tabs (if multi-section page) */}
  <Tabs>
    <TabsList>
      <TabsTrigger value="overview">Overview</TabsTrigger>
      <TabsTrigger value="tasks">Tasks</TabsTrigger>
      <TabsTrigger value="team">Team</TabsTrigger>
    </TabsList>
  </Tabs>

  {/* Page Content */}
  <PageContent>
    {/* Cards, tables, widgets */}
  </PageContent>
</Page>
```

### Dashboard Layout (Grid)

```tsx
<div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
  <Card>...</Card>
  <Card>...</Card>
  <Card>...</Card>
</div>
```

### List/Detail Layout (Master-Detail)

```tsx
<div className="grid grid-cols-[400px_1fr] gap-6">
  {/* List */}
  <Card>
    <List>...</List>
  </Card>

  {/* Detail */}
  <Card>
    <Detail>...</Detail>
  </Card>
</div>
```

---

## 4. TASK MANAGEMENT UI (Priority Feature)

### /tasks Page - Full Specification

**Layout:**
```
┌────────────────────────────────────────────┐
│ Tasks                              [+ New] │
├────────────────────────────────────────────┤
│ [🔍 Search] [📅 Due Date ▼] [👤 Assigned ▼]│
│ [List] [Kanban] [Calendar] [Timeline]     │
├────────────────────────────────────────────┤
│                                            │
│  TO DO        IN PROGRESS      DONE        │
│ ┌─────────┐  ┌─────────┐   ┌─────────┐  │
│ │ Task 1  │  │ Task 3  │   │ Task 5  │  │
│ │ 📅 Dec 30│  │ 👤 John │   │ ✓       │  │
│ └─────────┘  └─────────┘   └─────────┘  │
│ ┌─────────┐  ┌─────────┐                 │
│ │ Task 2  │  │ Task 4  │                 │
│ │ 🔴 High │  │ 📎 2    │                 │
│ └─────────┘  └─────────┘                 │
└────────────────────────────────────────────┘
```

**Kanban Board:**
```tsx
<div className="flex gap-4 overflow-x-auto">
  {columns.map(column => (
    <div className="flex-shrink-0 w-80">
      {/* Column Header */}
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-t-lg">
        <h3 className="font-semibold">{column.name}</h3>
        <Badge>{column.count}</Badge>
      </div>

      {/* Droppable Column */}
      <Droppable droppableId={column.id}>
        {(provided) => (
          <div ref={provided.innerRef} {...provided.droppableProps}>
            {column.tasks.map((task, index) => (
              <Draggable key={task.id} draggableId={task.id} index={index}>
                {(provided) => (
                  <TaskCard
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    task={task}
                  />
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>

      {/* Add Task Button */}
      <Button variant="ghost" size="sm" className="w-full">
        + Add Task
      </Button>
    </div>
  ))}
</div>
```

**Task Card (in Kanban):**
```tsx
<Card className="mb-3 cursor-grab active:cursor-grabbing hover:shadow-md transition">
  {/* Priority Indicator */}
  <div className={cn("h-1 rounded-t-lg", priorityColor)} />

  <CardContent className="p-4">
    {/* Task Title */}
    <Text weight="medium" className="mb-2">{task.title}</Text>

    {/* Metadata */}
    <div className="flex items-center gap-2 text-sm text-muted mb-2">
      <Badge variant="outline">{task.project}</Badge>
      {task.dueDate && (
        <div className="flex items-center gap-1">
          <CalendarIcon size={12} />
          <Text size="sm">{formatDate(task.dueDate)}</Text>
        </div>
      )}
    </div>

    {/* Assignee & Icons */}
    <div className="flex items-center justify-between">
      <Avatar size="xs" src={task.assignee.avatar} />
      <div className="flex gap-2">
        {task.hasComments && <MessageSquare size={14} />}
        {task.hasAttachments && <Paperclip size={14} />}
        {task.subtasksCount && <CheckSquare size={14} />}
      </div>
    </div>
  </CardContent>
</Card>
```

**List View:**
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead><Checkbox /></TableHead>
      <TableHead sortable>Task</TableHead>
      <TableHead sortable>Project</TableHead>
      <TableHead sortable>Assigned To</TableHead>
      <TableHead sortable>Due Date</TableHead>
      <TableHead sortable>Priority</TableHead>
      <TableHead sortable>Status</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {tasks.map(task => (
      <TableRow key={task.id} hoverable>
        <TableCell><Checkbox /></TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <div className={cn("w-2 h-2 rounded-full", priorityColor)} />
            <Text weight="medium">{task.title}</Text>
          </div>
        </TableCell>
        <TableCell>{task.project}</TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <Avatar size="xs" src={task.assignee.avatar} />
            <Text>{task.assignee.name}</Text>
          </div>
        </TableCell>
        <TableCell>
          <Text tabular>{formatDate(task.dueDate)}</Text>
        </TableCell>
        <TableCell>
          <Badge variant={priorityVariant}>{task.priority}</Badge>
        </TableCell>
        <TableCell>
          <Badge variant={statusVariant}>{task.status}</Badge>
        </TableCell>
        <TableCell>
          <DropdownMenu>...</DropdownMenu>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

**Task Detail Modal:**
```tsx
<Dialog size="xl">
  <DialogContent className="max-h-[90vh] overflow-y-auto">
    <DialogHeader>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Checkbox checked={task.completed} />
          <Input
            value={task.title}
            variant="unstyled"
            className="text-2xl font-bold"
          />
        </div>
        <DropdownMenu>
          <DropdownMenuItem>Duplicate</DropdownMenuItem>
          <DropdownMenuItem>Delete</DropdownMenuItem>
        </DropdownMenu>
      </div>
    </DialogHeader>

    <DialogBody>
      <div className="grid grid-cols-[1fr_300px] gap-6">
        {/* Main Content */}
        <div className="space-y-6">
          {/* Description */}
          <div>
            <Label>Description</Label>
            <RichTextEditor value={task.description} />
          </div>

          {/* Subtasks */}
          <div>
            <Label>Subtasks</Label>
            <ChecklistItem checked={false}>Subtask 1</ChecklistItem>
            <ChecklistItem checked={true}>Subtask 2</ChecklistItem>
            <Button variant="ghost" size="sm">+ Add Subtask</Button>
          </div>

          {/* Attachments */}
          <div>
            <Label>Attachments</Label>
            <FileUpload multiple />
            {task.attachments.map(file => (
              <FileItem key={file.id} file={file} />
            ))}
          </div>

          {/* Comments */}
          <div>
            <Label>Comments</Label>
            {task.comments.map(comment => (
              <CommentItem key={comment.id} comment={comment} />
            ))}
            <Textarea placeholder="Add a comment..." />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <FormField>
            <Label>Status</Label>
            <Select value={task.status}>
              <SelectItem value="todo">To Do</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="done">Done</SelectItem>
            </Select>
          </FormField>

          <FormField>
            <Label>Assigned To</Label>
            <Select value={task.assignee}>
              {/* Staff list */}
            </Select>
          </FormField>

          <FormField>
            <Label>Due Date</Label>
            <DatePicker value={task.dueDate} />
          </FormField>

          <FormField>
            <Label>Priority</Label>
            <Select value={task.priority}>
              <SelectItem value="critical">🔴 Critical</SelectItem>
              <SelectItem value="high">🟠 High</SelectItem>
              <SelectItem value="medium">🟡 Medium</SelectItem>
              <SelectItem value="low">⚪ Low</SelectItem>
            </Select>
          </FormField>

          <FormField>
            <Label>Project</Label>
            <Select value={task.project}>
              {/* Projects list */}
            </Select>
          </FormField>

          <Separator />

          {/* Metadata */}
          <div className="text-sm text-muted">
            <div>Created {formatDate(task.createdAt)}</div>
            <div>by {task.createdBy}</div>
            <div className="mt-2">Updated {formatDate(task.updatedAt)}</div>
          </div>
        </div>
      </div>
    </DialogBody>
  </DialogContent>
</Dialog>
```

---

## 5. INTERACTION PATTERNS

### Keyboard Shortcuts

```
Global:
- Cmd/Ctrl + K: Command palette (search everything)
- Cmd/Ctrl + /: Show keyboard shortcuts
- Esc: Close modal/drawer
- ?: Help

Navigation:
- g then d: Go to Dashboard
- g then p: Go to Projects
- g then t: Go to Tasks

Tasks:
- c: Create new task
- e: Edit selected task
- Backspace: Delete selected task
- j/k: Navigate up/down in list

Bulk Operations:
- Shift + Click: Select range
- Cmd/Ctrl + A: Select all
- Cmd/Ctrl + D: Deselect all
```

### Drag & Drop

**Task Kanban:**
- Drag task card between columns
- Visual feedback (opacity, outline)
- Drop zones highlighted
- Smooth animation on drop

**Priority Sorting:**
- Drag to reorder tasks in column
- Auto-save new order
- Optimistic UI update

### Inline Editing

**Click to Edit:**
- Double-click table cell → Edit mode
- Enter: Save
- Esc: Cancel
- Tab: Move to next field

**Hover Actions:**
- Hover over row → Show action buttons
- Hover over card → Show drag handle
- Hover over avatar → Show user card

### Bulk Operations

**Select Multiple:**
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>
        <Checkbox
          checked={allSelected}
          indeterminate={someSelected}
          onCheckedChange={toggleAll}
        />
      </TableHead>
      {/* ... */}
    </TableRow>
  </TableHeader>
</Table>

{/* Bulk Actions Bar (appears when items selected) */}
{selectedCount > 0 && (
  <div className="fixed bottom-6 left-1/2 -translate-x-1/2
                  bg-primary text-white rounded-lg shadow-xl px-6 py-3
                  flex items-center gap-4 animate-slide-up">
    <Text weight="medium">{selectedCount} selected</Text>
    <Separator orientation="vertical" className="h-6" />
    <Button variant="ghost" size="sm">Assign</Button>
    <Button variant="ghost" size="sm">Change Status</Button>
    <Button variant="ghost" size="sm">Delete</Button>
    <Button variant="ghost" size="sm" onClick={clearSelection}>×</Button>
  </div>
)}
```

---

## 6. RESPONSIVE DESIGN

### Breakpoints

```
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px
- 2xl: 1536px
```

### Mobile Optimizations

**Navigation:**
- Hamburger menu on mobile
- Bottom nav bar (Dashboard, Tasks, Projects, More)
- Swipe gestures (swipe left/right between tabs)

**Tables:**
- Convert to card list on mobile
- Stack columns vertically
- Horizontal scroll for wide tables

**Forms:**
- Full-width inputs on mobile
- Larger touch targets (min 44x44px)
- Native date/time pickers

**Modals:**
- Full-screen on mobile
- Slide up animation
- Pull-to-dismiss

---

## 7. ANIMATIONS & TRANSITIONS

### Timing

```
- Fast: 150ms (hover, active states)
- Normal: 300ms (modals, drawers)
- Slow: 500ms (page transitions)

Easing:
- ease-in-out (default)
- ease-out (enter)
- ease-in (exit)
```

### Micro-interactions

```tsx
// Button Press
<Button className="active:scale-95 transition-transform">

// Card Hover
<Card className="hover:shadow-lg hover:-translate-y-1 transition-all">

// Checkbox Check
<Checkbox className="data-[state=checked]:scale-110 transition-transform">

// Dropdown Open
<DropdownContent className="animate-slide-down">

// Toast Notification
<Toast className="animate-slide-in-right">
```

---

## 8. LOADING STATES

### Skeleton Screens

```tsx
<Card>
  <Skeleton className="h-8 w-1/3 mb-4" />
  <Skeleton className="h-4 w-full mb-2" />
  <Skeleton className="h-4 w-2/3" />
</Card>
```

### Spinners

```tsx
// Inline Spinner
<Button disabled>
  <Spinner size="sm" className="mr-2" />
  Loading...
</Button>

// Full Page Loader
<div className="flex items-center justify-center min-h-screen">
  <Spinner size="lg" />
</div>
```

### Progress Indicators

```tsx
<Progress value={60} max={100} />
```

---

## 9. EMPTY STATES

```tsx
<EmptyState
  icon={<InboxIcon className="h-16 w-16 text-muted" />}
  title="No tasks yet"
  description="Create your first task to get started"
  action={<Button>+ Create Task</Button>}
/>
```

---

## 10. ERROR STATES

```tsx
<Alert variant="destructive">
  <AlertCircle className="h-4 w-4" />
  <AlertTitle>Error</AlertTitle>
  <AlertDescription>
    Failed to load tasks. <Button variant="link">Try again</Button>
  </AlertDescription>
</Alert>
```

---

## DESIGN CHECKLIST

Before shipping any UI:
- [ ] Matches design system (colors, typography, spacing)
- [ ] Responsive (test mobile, tablet, desktop)
- [ ] Keyboard accessible (tab navigation works)
- [ ] Loading states implemented
- [ ] Empty states implemented
- [ ] Error states implemented
- [ ] Animations smooth (60fps)
- [ ] Touch targets 44x44px minimum (mobile)
- [ ] Color contrast passes WCAG AA
- [ ] Tested with real data (not just lorem ipsum)

---

**Last Updated:** December 29, 2025
**Version:** 1.0
**Status:** Living Document (update as we build)
