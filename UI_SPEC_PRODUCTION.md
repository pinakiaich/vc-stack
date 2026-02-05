# VC Firm Filter - Production UI Specification

**Document Version:** 1.0  
**Date:** January 22, 2026  
**Status:** Developer Handover Pack  
**Prepared For:** Engineering Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Application Shell](#2-application-shell)
3. [Design Tokens](#3-design-tokens)
4. [Canonical DataGrid Specification](#4-canonical-datagrid-specification)
5. [Page Specifications](#5-page-specifications)
   - [5.1 Run Setup Page](#51-run-setup-page)
   - [5.2 Results List Page](#52-results-list-page)
   - [5.3 Memo View Page](#53-memo-view-page)
6. [Component States](#6-component-states)
7. [Acceptance Criteria](#7-acceptance-criteria)
8. [Dev Assignments](#8-dev-assignments)
9. [Appendix](#9-appendix)

---

## 1. Executive Summary

### 1.1 Current Flow (Preserved)

```
Excel Upload → Criteria Input → Run Filter → Results List → Click Firm → Investment Memo
```

This specification transforms the Streamlit prototype into a production-grade React/TypeScript application while **preserving all existing business logic and memo content structure**.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| UI component specifications | Memo content changes |
| Design system tokens | Business logic changes |
| Page wireframes & states | AI/ML algorithm changes |
| DataGrid specifications | Backend API changes |
| Acceptance criteria | Authentication/authorization |
| Developer assignments | Deployment infrastructure |

### 1.3 Tech Stack (Recommended)

| Layer | Technology |
|-------|------------|
| Framework | React 18+ with TypeScript |
| State Management | Zustand or React Query |
| UI Library | Radix UI Primitives |
| Styling | Tailwind CSS + CSS Variables |
| DataGrid | TanStack Table v8 |
| Forms | React Hook Form + Zod |
| File Upload | react-dropzone |
| Charts | Recharts or Visx |

---

## 2. Application Shell

### 2.1 Layout Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GLOBAL HEADER                                │
│  ┌──────────┐  ┌────────────────────────────────┐  ┌─────────────┐  │
│  │   Logo   │  │      Navigation Tabs           │  │ User Menu   │  │
│  └──────────┘  └────────────────────────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                                                               │  │
│  │                      MAIN CONTENT AREA                        │  │
│  │                                                               │  │
│  │   • Run Setup (Full Width)                                    │  │
│  │   • Results List (Full Width with DataGrid)                   │  │
│  │   • Memo View (Content + Sidebar Layout)                      │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                         STATUS BAR                                   │
│  [API Status] [Cache Status] [RAG Status] [Last Run Info]           │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Shell Component Specification

```typescript
// AppShell.tsx
interface AppShellProps {
  children: React.ReactNode;
  navigation: NavigationItem[];
  statusBar: StatusBarConfig;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: IconType;
  href: string;
  badge?: number | string;
  disabled?: boolean;
}

interface StatusBarConfig {
  apiConnected: boolean;
  cacheEnabled: boolean;
  cacheHitRate?: number;
  ragChunksLoaded: number;
  lastRunTimestamp?: Date;
}
```

### 2.3 Navigation Items

| ID | Label | Icon | Route | Badge Logic |
|----|-------|------|-------|-------------|
| `run-setup` | Run Setup | `Upload` | `/` | — |
| `results` | Results | `List` | `/results` | Count of results |
| `memo` | Investment Memo | `FileText` | `/memo/:id` | — |

### 2.4 Responsive Breakpoints

| Breakpoint | Width | Layout Behavior |
|------------|-------|-----------------|
| `xs` | < 640px | Single column, stacked navigation |
| `sm` | ≥ 640px | Single column, horizontal navigation |
| `md` | ≥ 768px | Two-column layouts available |
| `lg` | ≥ 1024px | Full layout, sidebar visible |
| `xl` | ≥ 1280px | Maximum content width (1200px) |
| `2xl` | ≥ 1536px | Centered with larger gutters |

---

## 3. Design Tokens

### 3.1 Color Palette

```css
:root {
  /* Primary Brand Colors */
  --color-primary-50: #eff6ff;
  --color-primary-100: #dbeafe;
  --color-primary-200: #bfdbfe;
  --color-primary-300: #93c5fd;
  --color-primary-400: #60a5fa;
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;
  --color-primary-700: #1d4ed8;
  --color-primary-800: #1e40af;
  --color-primary-900: #1e3a8a;

  /* Neutral/Gray Scale */
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-300: #d1d5db;
  --color-gray-400: #9ca3af;
  --color-gray-500: #6b7280;
  --color-gray-600: #4b5563;
  --color-gray-700: #374151;
  --color-gray-800: #1f2937;
  --color-gray-900: #111827;

  /* Semantic Colors */
  --color-success-50: #ecfdf5;
  --color-success-500: #10b981;
  --color-success-600: #059669;
  --color-success-700: #047857;

  --color-warning-50: #fffbeb;
  --color-warning-500: #f59e0b;
  --color-warning-600: #d97706;
  --color-warning-700: #b45309;

  --color-error-50: #fef2f2;
  --color-error-500: #ef4444;
  --color-error-600: #dc2626;
  --color-error-700: #b91c1c;

  --color-info-50: #eff6ff;
  --color-info-500: #3b82f6;
  --color-info-600: #2563eb;

  /* Score Gradient (for match scores) */
  --color-score-excellent: #10b981; /* 90-100% */
  --color-score-good: #22c55e;      /* 75-89% */
  --color-score-moderate: #f59e0b;  /* 50-74% */
  --color-score-low: #ef4444;       /* 0-49% */

  /* Surface Colors */
  --color-surface-primary: #ffffff;
  --color-surface-secondary: #f9fafb;
  --color-surface-tertiary: #f3f4f6;
  --color-surface-elevated: #ffffff;
  
  /* Border Colors */
  --color-border-default: #e5e7eb;
  --color-border-muted: #f3f4f6;
  --color-border-emphasis: #d1d5db;
}
```

### 3.2 Typography Scale

```css
:root {
  /* Font Families */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Font Sizes */
  --text-xs: 0.75rem;      /* 12px */
  --text-sm: 0.875rem;     /* 14px */
  --text-base: 1rem;       /* 16px */
  --text-lg: 1.125rem;     /* 18px */
  --text-xl: 1.25rem;      /* 20px */
  --text-2xl: 1.5rem;      /* 24px */
  --text-3xl: 1.875rem;    /* 30px */
  --text-4xl: 2.25rem;     /* 36px */

  /* Line Heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* Letter Spacing */
  --tracking-tight: -0.025em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;
}
```

### 3.3 Typography Usage Matrix

| Element | Size | Weight | Line Height | Color |
|---------|------|--------|-------------|-------|
| Page Title | `--text-2xl` | `--font-semibold` | `--leading-tight` | `--color-gray-900` |
| Section Header | `--text-lg` | `--font-semibold` | `--leading-snug` | `--color-gray-800` |
| Card Title | `--text-base` | `--font-medium` | `--leading-normal` | `--color-gray-900` |
| Body Text | `--text-sm` | `--font-normal` | `--leading-normal` | `--color-gray-700` |
| Caption | `--text-xs` | `--font-normal` | `--leading-normal` | `--color-gray-500` |
| Label | `--text-sm` | `--font-medium` | `--leading-none` | `--color-gray-700` |
| Code/Mono | `--text-sm` | `--font-normal` | `--leading-relaxed` | `--color-gray-800` |

### 3.4 Spacing Scale

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
  --space-24: 6rem;     /* 96px */
}
```

### 3.5 Border Radius

```css
:root {
  --radius-none: 0;
  --radius-sm: 0.125rem;   /* 2px */
  --radius-default: 0.25rem; /* 4px */
  --radius-md: 0.375rem;   /* 6px */
  --radius-lg: 0.5rem;     /* 8px */
  --radius-xl: 0.75rem;    /* 12px */
  --radius-2xl: 1rem;      /* 16px */
  --radius-full: 9999px;
}
```

### 3.6 Shadows

```css
:root {
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-default: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  
  /* Inset shadows for inputs */
  --shadow-inner: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);
  
  /* Focus ring */
  --shadow-focus: 0 0 0 3px var(--color-primary-200);
}
```

### 3.7 Animation Tokens

```css
:root {
  /* Durations */
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
  --duration-slower: 500ms;

  /* Easing */
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
```

### 3.8 Z-Index Scale

```css
:root {
  --z-base: 0;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-overlay: 300;
  --z-modal: 400;
  --z-popover: 500;
  --z-toast: 600;
  --z-tooltip: 700;
}
```

---

## 4. Canonical DataGrid Specification

### 4.1 Overview

The DataGrid is used in the **Results List** page to display filtered firms. This specification ensures consistent behavior, accessibility, and performance.

### 4.2 Column Schema

```typescript
interface FirmResultColumn {
  id: string;
  header: string;
  accessor: keyof FirmResult | ((row: FirmResult) => any);
  width: number | 'auto' | 'flex';
  minWidth?: number;
  maxWidth?: number;
  sortable: boolean;
  filterable: boolean;
  resizable: boolean;
  sticky?: 'left' | 'right';
  align?: 'left' | 'center' | 'right';
  cellRenderer?: 'default' | 'score' | 'badge' | 'link' | 'truncate' | 'custom';
}

interface FirmResult {
  id: string;
  rank: number;
  name: string;
  score: number;
  reason: string;
  industry: string;
  stage: string;
  revenue: string;
  location: string;
  description: string;
  opportunityScore: number | null;
  exitProbabilityScore: number | null;
}
```

### 4.3 Column Definitions

| Column | ID | Width | Min | Sortable | Filterable | Renderer | Sticky |
|--------|-----|-------|-----|----------|------------|----------|--------|
| Rank | `rank` | 60px | 50px | Yes | No | Badge | Left |
| Name | `name` | flex(2) | 150px | Yes | Yes | Link | Left |
| Score | `score` | 100px | 80px | Yes | Yes | ScoreBar | — |
| Industry | `industry` | flex(1) | 100px | Yes | Yes | Badge | — |
| Stage | `stage` | 100px | 80px | Yes | Yes | Badge | — |
| Reason | `reason` | flex(3) | 200px | No | Yes | Truncate | — |
| Actions | `actions` | 80px | 80px | No | No | Actions | Right |

### 4.4 DataGrid Component Interface

```typescript
interface DataGridProps<T> {
  // Data
  data: T[];
  columns: ColumnDef<T>[];
  loading?: boolean;
  error?: Error | null;
  
  // Selection
  selectable?: boolean;
  selectedRows?: Set<string>;
  onSelectionChange?: (selectedIds: Set<string>) => void;
  
  // Sorting
  sortable?: boolean;
  defaultSort?: { column: string; direction: 'asc' | 'desc' };
  onSortChange?: (sort: SortState) => void;
  
  // Filtering
  filterable?: boolean;
  globalFilter?: string;
  columnFilters?: ColumnFilter[];
  onFilterChange?: (filters: ColumnFilter[]) => void;
  
  // Pagination
  pagination?: PaginationConfig;
  pageSize?: number;
  currentPage?: number;
  totalCount?: number;
  onPageChange?: (page: number) => void;
  
  // Row Interaction
  onRowClick?: (row: T) => void;
  onRowDoubleClick?: (row: T) => void;
  rowClassName?: (row: T) => string;
  
  // Virtualization
  virtualizeRows?: boolean;
  rowHeight?: number;
  overscan?: number;
  
  // Empty/Loading States
  emptyState?: React.ReactNode;
  loadingState?: React.ReactNode;
  errorState?: React.ReactNode;
  
  // Density
  density?: 'compact' | 'normal' | 'comfortable';
  
  // Accessibility
  ariaLabel: string;
  ariaDescribedBy?: string;
}
```

### 4.5 Cell Renderers

#### 4.5.1 ScoreBar Renderer

```typescript
interface ScoreBarProps {
  value: number; // 0-100
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

// Rendering rules:
// - 90-100%: Green (#10b981), label "Excellent"
// - 75-89%:  Light Green (#22c55e), label "Good"
// - 50-74%:  Yellow (#f59e0b), label "Moderate"
// - 0-49%:   Red (#ef4444), label "Low"
```

**Visual Specification:**
```
┌──────────────────────────────┐
│ ████████████░░░░░░ 78.5%     │
└──────────────────────────────┘
Width: 100px
Height: 24px (md), 20px (sm), 28px (lg)
Border Radius: 4px
Background: var(--color-gray-200)
Fill: Gradient based on score
Label: Right-aligned percentage
```

#### 4.5.2 Badge Renderer

```typescript
interface BadgeProps {
  value: string;
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md';
}

// Stage mapping:
const stageBadgeMap: Record<string, BadgeVariant> = {
  'Seed': 'info',
  'Series A': 'primary',
  'Series B': 'success',
  'Series C': 'warning',
  'Growth': 'default',
  'Pre-IPO': 'error',
};
```

#### 4.5.3 Link Renderer (Firm Name)

```typescript
interface LinkCellProps {
  value: string;
  href?: string;
  onClick?: () => void;
  icon?: IconType;
}

// Styling:
// - Font weight: 500
// - Color: var(--color-primary-600)
// - Hover: Underline, var(--color-primary-700)
// - Focus: Ring with var(--shadow-focus)
```

#### 4.5.4 Truncate Renderer (Reason)

```typescript
interface TruncateCellProps {
  value: string;
  maxLines?: 1 | 2 | 3;
  expandable?: boolean;
}

// Behavior:
// - Show first N lines
// - Ellipsis at end
// - Tooltip on hover showing full content
// - Optional "Show more" button
```

### 4.6 DataGrid States

| State | Visual Treatment |
|-------|------------------|
| Default | Standard table layout |
| Loading | Skeleton rows (10 rows of animated placeholders) |
| Empty | Centered empty state illustration + message |
| Error | Error banner above table + retry button |
| Filtered (no results) | "No results match your filters" + clear filters button |
| Single Selection | Row background: `var(--color-primary-50)` |
| Multi Selection | Checkboxes in first column |

### 4.7 Keyboard Navigation

| Key | Action |
|-----|--------|
| `Tab` | Move between interactive elements |
| `Arrow Up/Down` | Navigate between rows |
| `Arrow Left/Right` | Navigate between cells |
| `Enter` | Activate row (trigger click handler) |
| `Space` | Toggle row selection |
| `Escape` | Clear selection |
| `Ctrl/Cmd + A` | Select all rows |

### 4.8 Performance Requirements

| Metric | Requirement |
|--------|-------------|
| Initial Render (100 rows) | < 100ms |
| Sort Operation | < 50ms |
| Filter Operation | < 100ms |
| Scroll (virtualized) | 60 FPS |
| Memory (1000 rows) | < 50MB |

---

## 5. Page Specifications

## 5.1 Run Setup Page

### 5.1.1 Route & Meta

| Property | Value |
|----------|-------|
| Route | `/` or `/run-setup` |
| Page Title | "Run Setup - VC Firm Filter" |
| Meta Description | "Upload Excel file and configure filtering criteria" |

### 5.1.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Run Setup                                                                   │
│  Upload your firm data and configure filtering criteria                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 1: Upload Excel File                                          │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                                                             │    │    │
│  │  │         ┌──────────┐                                        │    │    │
│  │  │         │  📄 📤   │                                        │    │    │
│  │  │         └──────────┘                                        │    │    │
│  │  │                                                             │    │    │
│  │  │    Drag & drop your Excel file here, or click to browse    │    │    │
│  │  │                                                             │    │    │
│  │  │    Supported formats: .xlsx, .xls                          │    │    │
│  │  │                                                             │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  │                                                                      │    │
│  │  [Advanced Options ▼]                                               │    │
│  │    • Skip rows: [0____]                                             │    │
│  │    • Name column: [Auto-detect ▼]                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 2: Configure API Key                                          │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  🔑 OpenAI API Key                                          │    │    │
│  │  │  [sk-•••••••••••••••••••••••••••••••••••]  [🔄 Change]      │    │    │
│  │  │  ✅ API Key configured                                       │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 3: Enter Filtering Criteria                                   │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │  Describe what you're looking for:                          │    │    │
│  │  │  ┌───────────────────────────────────────────────────────┐  │    │    │
│  │  │  │ Looking for AI/ML startups with revenue >$1M,         │  │    │    │
│  │  │  │ Series A stage, B2B focus, strong technical team      │  │    │    │
│  │  │  │                                                       │  │    │    │
│  │  │  │                                                       │  │    │    │
│  │  │  └───────────────────────────────────────────────────────┘  │    │    │
│  │  │  💡 Tip: Be specific about industry, stage, metrics         │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  STEP 4: Optional Enhancements                                      │    │
│  │                                                                      │    │
│  │  ┌─────────────────────────┐  ┌─────────────────────────┐          │    │
│  │  │  📚 RAG Documents       │  │  🧠 VC Knowledge Base   │          │    │
│  │  │  [+] Add documents      │  │  ✅ 1,234 chunks loaded │          │    │
│  │  │  0 documents loaded     │  │  [🔄 Rebuild]           │          │    │
│  │  └─────────────────────────┘  └─────────────────────────┘          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │           [🔍 Filter Top 10 Firms]                                  │    │
│  │                                                                      │    │
│  │           Estimated time: ~30 seconds                               │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.1.3 Component Breakdown

#### FileUploader Component

```typescript
interface FileUploaderProps {
  accept: string[];              // ['.xlsx', '.xls']
  maxSize: number;               // bytes (default: 10MB)
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  file?: File | null;
  processing?: boolean;
  error?: string;
}

// States:
// - Empty: Show drop zone with icon and instructions
// - Dragging: Highlight border, show "Drop file here"
// - Selected: Show file name, size, remove button
// - Processing: Show progress bar or spinner
// - Error: Show error message with retry option
```

**Drop Zone Specifications:**

| Property | Value |
|----------|-------|
| Height | 200px (min), auto (max) |
| Border | 2px dashed `var(--color-gray-300)` |
| Border (hover) | 2px dashed `var(--color-primary-500)` |
| Border (dragging) | 2px solid `var(--color-primary-500)` |
| Border radius | `var(--radius-lg)` |
| Background | `var(--color-gray-50)` |
| Background (dragging) | `var(--color-primary-50)` |

#### CriteriaInput Component

```typescript
interface CriteriaInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
  suggestions?: string[];
  onSubmit?: () => void;
}
```

**Textarea Specifications:**

| Property | Value |
|----------|-------|
| Min Height | 120px |
| Max Height | 300px |
| Resize | Vertical only |
| Font | `var(--font-sans)`, `var(--text-base)` |
| Padding | `var(--space-3)` |
| Border | 1px solid `var(--color-border-default)` |
| Focus | `var(--shadow-focus)` |

### 5.1.4 Data Preview Panel

When file is uploaded, show preview:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  📊 Data Preview                                           [Collapse ▲] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ✅ Loaded 247 firms from Excel                                         │
│                                                                          │
│  Column Detection:                                                       │
│  ┌──────────────┬───────────────┬──────────────┐                       │
│  │ ✅ Name      │ ✅ Industry   │ ✅ Stage     │                       │
│  │ ✅ Revenue   │ ⚠️ Description│ ❌ Location  │                       │
│  └──────────────┴───────────────┴──────────────┘                       │
│                                                                          │
│  First 5 rows:                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ # │ Name          │ Industry    │ Stage   │ Revenue             │   │
│  ├───┼───────────────┼─────────────┼─────────┼─────────────────────┤   │
│  │ 1 │ TechCorp AI   │ AI/ML       │ Series A│ $2.5M ARR           │   │
│  │ 2 │ DataFlow Inc  │ Data Infra  │ Seed    │ $500K               │   │
│  │ 3 │ CloudSecure   │ Cybersec    │ Series B│ $8M ARR             │   │
│  └───┴───────────────┴─────────────┴─────────┴─────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.1.5 State Machine

```
┌─────────────────┐
│    INITIAL      │
│  (Empty form)   │
└────────┬────────┘
         │ Upload file
         ▼
┌─────────────────┐
│   PROCESSING    │──── Error ────►┌─────────────────┐
│  (Parsing file) │                │  UPLOAD_ERROR   │
└────────┬────────┘                └────────┬────────┘
         │ Success                          │ Retry
         ▼                                  │
┌─────────────────┐◄────────────────────────┘
│  FILE_LOADED    │
│ (Preview shown) │
└────────┬────────┘
         │ Enter criteria + click "Filter"
         ▼
┌─────────────────┐
│   FILTERING     │──── Error ────►┌─────────────────┐
│  (AI analyzing) │                │  FILTER_ERROR   │
└────────┬────────┘                └─────────────────┘
         │ Success
         ▼
┌─────────────────┐
│   COMPLETED     │
│ (Navigate to    │
│  Results List)  │
└─────────────────┘
```

---

## 5.2 Results List Page

### 5.2.1 Route & Meta

| Property | Value |
|----------|-------|
| Route | `/results` |
| Page Title | "Results - VC Firm Filter" |
| Query Params | `?q={criteria}&sort={column}&order={asc|desc}&page={n}` |

### 5.2.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Results                                                      [← New Run]   │
│  Showing 10 firms matching your criteria                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  🎯 Criteria: "AI/ML startups, Series A, B2B, revenue >$1M"        │    │
│  │  📊 Processed 247 firms in 28.3s  │  💾 Cache: 65% hit rate        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Search results...                              [Filter ▼] [Export ▼]│    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │                                                                      │    │
│  │  ┌────┬──────────────────┬───────────┬────────────┬─────────────┐  │    │
│  │  │ #  │ Firm Name        │ Score     │ Industry   │ Stage       │  │    │
│  │  ├────┼──────────────────┼───────────┼────────────┼─────────────┤  │    │
│  │  │ 1  │ 📌 TechCorp AI   │ ████ 92%  │ 🏷️ AI/ML  │ Series A    │  │    │
│  │  │    │ Strong AI/ML team with proven B2B traction...            │  │    │
│  │  ├────┼──────────────────┼───────────┼────────────┼─────────────┤  │    │
│  │  │ 2  │ 📌 DataFlow Inc  │ ███░ 85%  │ 🏷️ Data   │ Series A    │  │    │
│  │  │    │ Data infrastructure play with enterprise focus...        │  │    │
│  │  ├────┼──────────────────┼───────────┼────────────┼─────────────┤  │    │
│  │  │ 3  │ 📌 CloudSecure   │ ███░ 78%  │ 🏷️ Security│ Series B   │  │    │
│  │  │    │ Cybersecurity with AI-powered threat detection...        │  │    │
│  │  ├────┼──────────────────┼───────────┼────────────┼─────────────┤  │    │
│  │  │ 4  │ 📌 MLOps Pro     │ ██░░ 72%  │ 🏷️ ML Ops │ Series A    │  │    │
│  │  │    │ MLOps platform with strong developer adoption...         │  │    │
│  │  ├────┼──────────────────┼───────────┼────────────┼─────────────┤  │    │
│  │  │ 5  │ 📌 NeuralNet Co  │ ██░░ 68%  │ 🏷️ AI/ML  │ Seed        │  │    │
│  │  │    │ Early stage but promising neural network technology...   │  │    │
│  │  └────┴──────────────────┴───────────┴────────────┴─────────────┘  │    │
│  │                                                                      │    │
│  │  [Show 5 more results...]                                           │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  💡 Click on any firm name to view detailed investment memo                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2.3 Results Card Component

For each result row, use a card-based layout on mobile and table row on desktop:

```typescript
interface ResultCardProps {
  rank: number;
  firm: FirmResult;
  isSelected?: boolean;
  onClick: () => void;
  onHover?: () => void;
}
```

**Card Layout (Mobile/Tablet):**

```
┌─────────────────────────────────────────────────────────────────────┐
│  #1                                                    Score: 92%   │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                                                                │ │
│  │  📌 TechCorp AI                                                │ │
│  │                                                                │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │ │
│  │  │ 🏷️ AI/ML │  │ Series A │  │ $2.5M ARR│                     │ │
│  │  └──────────┘  └──────────┘  └──────────┘                     │ │
│  │                                                                │ │
│  │  Strong AI/ML team with proven B2B traction in the enterprise │ │
│  │  space. Recurring revenue model with 120% NDR...              │ │
│  │                                                                │ │
│  │                                        [View Memo →]           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2.4 Filter Panel

```
┌─────────────────────────────────────────────────────────────────────┐
│  Filters                                                [Clear All] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Score Range                                                         │
│  [──────●────────────●──────]                                       │
│   50%                  100%                                          │
│                                                                      │
│  Industry                                                            │
│  ☑️ AI/ML (3)                                                        │
│  ☑️ Data Infrastructure (2)                                          │
│  ☑️ Cybersecurity (2)                                                │
│  ☐ FinTech (1)                                                       │
│  ☐ HealthTech (2)                                                    │
│                                                                      │
│  Stage                                                               │
│  ☑️ Seed (2)                                                         │
│  ☑️ Series A (5)                                                     │
│  ☐ Series B (2)                                                      │
│  ☐ Series C (1)                                                      │
│                                                                      │
│                                           [Apply Filters]            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2.5 Export Options

```typescript
interface ExportOptions {
  format: 'csv' | 'xlsx' | 'json' | 'pdf';
  columns: string[];  // Which columns to include
  includeReason: boolean;
  fileName?: string;
}
```

**Export Menu:**

```
┌──────────────────────┐
│  Export Results      │
├──────────────────────┤
│  📄 CSV              │
│  📊 Excel (.xlsx)    │
│  📋 JSON             │
│  📑 PDF Report       │
└──────────────────────┘
```

### 5.2.6 State Machine

```
┌─────────────────┐
│    LOADING      │
│ (Fetch results) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────────┐
│ EMPTY  │ │  LOADED    │
│(No     │ │ (Results   │
│results)│ │  displayed)│
└────────┘ └──────┬─────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌──────────┐
│FILTERED│  │ SORTED   │  │SELECTING │
│(Subset │  │ (Reorder │  │(Firm     │
│shown)  │  │  results)│  │ clicked) │
└────────┘  └──────────┘  └──────┬───┘
                                 │
                                 ▼
                          ┌──────────┐
                          │ NAVIGATE │
                          │(To Memo) │
                          └──────────┘
```

---

## 5.3 Memo View Page

### 5.3.1 Route & Meta

| Property | Value |
|----------|-------|
| Route | `/memo/:firmId` or `/memo/:dealId` |
| Page Title | "{Firm Name} - Investment Memo" |
| Back Navigation | Results List |

### 5.3.2 Wireframe

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [← Back to Results]                                                        │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                                                                      │    │
│  │  TechCorp AI                                            Score: 92%  │    │
│  │  ─────────────────────────────────────────────────────────────────  │    │
│  │                                                                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │    │
│  │  │ 🏷️ AI/ML │  │ Series A │  │ 📍 SF, CA│  │ 💰 $2.5M ARR     │    │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘    │    │
│  │                                                                      │    │
│  │  Match Reason:                                                       │    │
│  │  Strong AI/ML team with proven B2B traction in the enterprise       │    │
│  │  space. Recurring revenue model with 120% NDR demonstrates          │    │
│  │  product-market fit.                                                 │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────┐  ┌───────────────────┐  │
│  │                                               │  │                   │  │
│  │  MEMO CONTENT                                 │  │  SIDEBAR          │  │
│  │                                               │  │                   │  │
│  │  ┌─────────────────────────────────────────┐  │  │  📊 Quick Stats   │  │
│  │  │  🏢 Company Information                 │  │  │  ──────────────   │  │
│  │  │  ▼ Expanded                             │  │  │  Revenue: $2.5M   │  │
│  │  │  ─────────────────────────────────────  │  │  │  Employees: 45    │  │
│  │  │  Company Name: TechCorp AI              │  │  │  Founded: 2021    │  │
│  │  │  Country: United States                 │  │  │  Funding: $8M     │  │
│  │  │  Industry: AI/ML - Enterprise Software  │  │  │                   │  │
│  │  └─────────────────────────────────────────┘  │  │  📈 Scores        │  │
│  │                                               │  │  ──────────────   │  │
│  │  ┌─────────────────────────────────────────┐  │  │  Match: 92%       │  │
│  │  │  📊 Quantitative Data                   │  │  │  Opportunity: 85% │  │
│  │  │  ▼ Expanded                             │  │  │  Exit Prob: 72%   │  │
│  │  │  ─────────────────────────────────────  │  │  │                   │  │
│  │  │  ┌──────────────┬──────────────┐        │  │  │  🔗 Links         │  │
│  │  │  │ Market Size  │ Growth Rate  │        │  │  │  ──────────────   │  │
│  │  │  │ TAM: $45B    │ CAGR: 32%    │        │  │  │  🌐 Website       │  │
│  │  │  │ SAM: $12B    │              │        │  │  │  📰 Crunchbase    │  │
│  │  │  └──────────────┴──────────────┘        │  │  │  💼 LinkedIn      │  │
│  │  │  ┌──────────────┬──────────────┐        │  │  │                   │  │
│  │  │  │ Revenue      │ Valuation    │        │  │  │  📝 Actions       │  │
│  │  │  │ $2.5M ARR    │ $25M         │        │  │  │  ──────────────   │  │
│  │  │  │ 120% NDR     │ 10x multiple │        │  │  │  [Create Deal]    │  │
│  │  │  └──────────────┴──────────────┘        │  │  │  [Export PDF]     │  │
│  │  └─────────────────────────────────────────┘  │  │  [Share]          │  │
│  │                                               │  │                   │  │
│  │  ┌─────────────────────────────────────────┐  │  └───────────────────┘  │
│  │  │  📈 Industry Background & Growth        │  │                         │
│  │  │  ► Collapsed                            │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  │                                               │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  🏛️ Company Background                  │  │                         │
│  │  │  ► Collapsed                            │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  │                                               │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  👤 Founder Profile                     │  │                         │
│  │  │  ► Collapsed                            │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  │                                               │                         │
│  │  ┌─────────────────────────────────────────┐  │                         │
│  │  │  ⚔️ Competition & Market Landscape      │  │                         │
│  │  │  ► Collapsed                            │  │                         │
│  │  └─────────────────────────────────────────┘  │                         │
│  │                                               │                         │
│  └───────────────────────────────────────────────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3.3 Memo Sections (Preserved from Prototype)

**CRITICAL: Do not change memo content structure. The following sections must be preserved exactly as they exist in the prototype:**

| Section | Icon | Default State | Content Source |
|---------|------|---------------|----------------|
| Company Information | 🏢 | Expanded | `company_name`, `country_of_incorporation`, `industry` |
| Quantitative Data | 📊 | Expanded | `quantitative_data` object |
| Industry Background & Growth | 📈 | Collapsed | `industry_background` |
| Company Background | 🏛️ | Collapsed | `company_background` |
| Founder Profile | 👤 | Collapsed | `founder_profile` |
| Competition & Market Landscape | ⚔️ | Collapsed | `competition` |

### 5.3.4 Accordion Component

```typescript
interface AccordionProps {
  items: AccordionItem[];
  defaultExpanded?: string[];
  allowMultiple?: boolean;
  onChange?: (expandedIds: string[]) => void;
}

interface AccordionItem {
  id: string;
  icon: IconType;
  title: string;
  content: React.ReactNode;
  badge?: string;
  status?: 'complete' | 'partial' | 'empty';
}
```

**Accordion Styling:**

| Property | Value |
|----------|-------|
| Border | 1px solid `var(--color-border-default)` |
| Border radius | `var(--radius-lg)` |
| Header padding | `var(--space-4)` |
| Header background | `var(--color-surface-secondary)` |
| Header background (hover) | `var(--color-gray-100)` |
| Content padding | `var(--space-4)` `var(--space-6)` |
| Chevron rotation | 0° (collapsed) → 180° (expanded) |
| Transition | `var(--duration-normal)` `var(--ease-out)` |

### 5.3.5 Quantitative Data Grid

```
┌───────────────────────────────────────────────────────────────────────────┐
│  📊 Quantitative Data                                                      │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  Market Size                              Company Metrics                  │
│  ┌────────────────────────────────┐      ┌────────────────────────────┐   │
│  │  📈 TAM                        │      │  💰 Revenue                │   │
│  │  $45 Billion                   │      │  $2.5M ARR                 │   │
│  │                                │      │                            │   │
│  │  📊 SAM                        │      │  💵 Funding Raised         │   │
│  │  $12 Billion                   │      │  $8M Series A              │   │
│  │                                │      │                            │   │
│  │  📈 CAGR                       │      │  💎 Valuation              │   │
│  │  32%                           │      │  $25M (10x revenue)        │   │
│  └────────────────────────────────┘      │                            │   │
│                                          │  👥 Employees              │   │
│                                          │  45                        │   │
│                                          └────────────────────────────┘   │
│                                                                            │
│  ──────────────────────────────────────────────────────────────────────   │
│  📋 All Metrics                                                           │
│  ┌─────────────────────────────┬──────────────────────────────────────┐   │
│  │ Metric                      │ Value                                │   │
│  ├─────────────────────────────┼──────────────────────────────────────┤   │
│  │ Market Size (TAM)           │ $45 Billion                          │   │
│  │ Serviceable Market (SAM)    │ $12 Billion                          │   │
│  │ Market Growth (CAGR)        │ 32%                                  │   │
│  │ Company Revenue             │ $2.5M ARR                            │   │
│  │ Net Dollar Retention        │ 120%                                 │   │
│  │ Funding Raised              │ $8M (Series A)                       │   │
│  │ Valuation                   │ $25M                                 │   │
│  │ Employee Count              │ 45                                   │   │
│  └─────────────────────────────┴──────────────────────────────────────┘   │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.3.6 Sidebar Component

```typescript
interface MemoSidebarProps {
  firm: FirmResult;
  researchData: ResearchData;
  onCreateDeal: () => void;
  onExport: (format: ExportFormat) => void;
  onShare: () => void;
}
```

**Sidebar Sections:**

1. **Quick Stats** - Key metrics at a glance
2. **Scores** - Match score, opportunity score, exit probability
3. **Links** - External links (website, Crunchbase, LinkedIn)
4. **Actions** - Create Deal, Export PDF, Share

### 5.3.7 Research Status Indicator

```typescript
interface ResearchStatusProps {
  status: 'pending' | 'researching' | 'complete' | 'partial' | 'failed';
  completedFields: number;
  totalFields: number;
  qualityScore: number;
  lastUpdated?: Date;
}
```

**Status Visual Treatment:**

| Status | Icon | Color | Message |
|--------|------|-------|---------|
| `pending` | ⏳ | Gray | "Research not started" |
| `researching` | 🔄 | Blue (animated) | "Researching..." |
| `complete` | ✅ | Green | "Research complete (X/Y fields)" |
| `partial` | ⚠️ | Yellow | "Partial data (X/Y fields)" |
| `failed` | ❌ | Red | "Research failed - Retry" |

### 5.3.8 State Machine

```
┌─────────────────┐
│    LOADING      │
│ (Fetch firm &   │
│  research data) │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────────┐
│ ERROR  │ │  LOADED     │
│(404 or │ │ (Memo       │
│ API    │ │  displayed) │
│ error) │ └──────┬──────┘
└────────┘        │
            ┌─────┴─────┐
            ▼           ▼
      ┌──────────┐ ┌──────────────┐
      │REFRESHING│ │ CREATING_DEAL│
      │(Re-fetch │ │ (Modal open) │
      │ research)│ └──────────────┘
      └──────────┘
```

---

## 6. Component States

### 6.1 Global Loading States

| Component | Loading State |
|-----------|---------------|
| Page | Full-page skeleton with content placeholders |
| DataGrid | Skeleton rows (animated pulse) |
| Accordion | Collapsed with skeleton content |
| Card | Skeleton with preserved aspect ratio |
| Button | Disabled + spinner icon |
| Form | All inputs disabled, submit button loading |

### 6.2 Empty States

#### 6.2.1 No File Uploaded

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                        ┌────────────┐                           │
│                        │   📄 📤    │                           │
│                        └────────────┘                           │
│                                                                  │
│                   No file uploaded yet                          │
│                                                                  │
│         Upload an Excel file to start filtering firms           │
│                                                                  │
│                    [Upload File]                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.2.2 No Results

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                        ┌────────────┐                           │
│                        │   🔍 ❌    │                           │
│                        └────────────┘                           │
│                                                                  │
│                   No matching firms found                       │
│                                                                  │
│         Try adjusting your criteria or uploading a              │
│         different dataset                                        │
│                                                                  │
│              [Modify Criteria]    [New Upload]                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.2.3 Research Not Available

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│                        ┌────────────┐                           │
│                        │   🔬 📋    │                           │
│                        └────────────┘                           │
│                                                                  │
│              Research data not available                        │
│                                                                  │
│         Click "Conduct Research" to gather information          │
│         about this company from the internet                    │
│                                                                  │
│                  [Conduct Research]                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Error States

#### 6.3.1 API Error

```typescript
interface ErrorStateProps {
  title: string;
  message: string;
  code?: string;
  retryable: boolean;
  onRetry?: () => void;
  onBack?: () => void;
}
```

**Error Banner:**

```
┌─────────────────────────────────────────────────────────────────┐
│  ❌ Error: Unable to process your request                       │
│                                                                  │
│  The filtering service encountered an error. This might be      │
│  due to API rate limits or connectivity issues.                 │
│                                                                  │
│  Error code: FILTER_API_ERROR                                   │
│                                                                  │
│                    [Retry]    [Go Back]                         │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.3.2 File Processing Error

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️ Error: Could not process Excel file                         │
│                                                                  │
│  The file format is not supported or the file is corrupted.     │
│                                                                  │
│  Supported formats: .xlsx, .xls                                 │
│                                                                  │
│                    [Try Another File]                           │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 Success States

#### 6.4.1 File Uploaded Successfully

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ File uploaded successfully                                   │
│                                                                  │
│  firms_data.xlsx (245 KB)                                       │
│  247 firms loaded • 12 columns detected                         │
│                                                                  │
│                              [Remove]                           │
└─────────────────────────────────────────────────────────────────┘
```

#### 6.4.2 Filtering Complete

```
┌─────────────────────────────────────────────────────────────────┐
│  ✅ Filtering complete!                                          │
│                                                                  │
│  Found 10 firms matching your criteria                          │
│  Processed 247 firms in 28.3 seconds                            │
│                                                                  │
│                    [View Results →]                             │
└─────────────────────────────────────────────────────────────────┘
```

### 6.5 Button States

| State | Background | Border | Text | Cursor | Icon |
|-------|------------|--------|------|--------|------|
| Default | `--color-primary-600` | none | white | pointer | — |
| Hover | `--color-primary-700` | none | white | pointer | — |
| Active | `--color-primary-800` | none | white | pointer | — |
| Focus | `--color-primary-600` | `--shadow-focus` | white | pointer | — |
| Disabled | `--color-gray-300` | none | `--color-gray-500` | not-allowed | — |
| Loading | `--color-primary-500` | none | white | wait | Spinner |

### 6.6 Input States

| State | Border | Background | Shadow |
|-------|--------|------------|--------|
| Default | `--color-border-default` | white | none |
| Hover | `--color-gray-400` | white | none |
| Focus | `--color-primary-500` | white | `--shadow-focus` |
| Error | `--color-error-500` | `--color-error-50` | none |
| Disabled | `--color-gray-200` | `--color-gray-50` | none |
| ReadOnly | `--color-gray-200` | `--color-gray-50` | none |

---

## 7. Acceptance Criteria

### 7.1 Run Setup Page

#### AC-RS-001: File Upload

```gherkin
Feature: Excel File Upload

  Scenario: User uploads valid Excel file
    Given I am on the Run Setup page
    When I drag and drop a valid .xlsx file onto the upload zone
    Then I should see a success message "File uploaded successfully"
    And I should see the file name and size displayed
    And I should see a preview of the first 5 rows
    And the "Filter Top 10 Firms" button should be enabled

  Scenario: User uploads invalid file type
    Given I am on the Run Setup page
    When I upload a .pdf file
    Then I should see an error message "Unsupported file format"
    And the upload zone should reset to empty state

  Scenario: File exceeds size limit
    Given I am on the Run Setup page
    When I upload an Excel file larger than 10MB
    Then I should see an error message "File too large. Maximum size is 10MB"
```

#### AC-RS-002: Criteria Input

```gherkin
Feature: Filtering Criteria Input

  Scenario: User enters valid criteria
    Given I have uploaded a valid Excel file
    When I enter "AI/ML startups, Series A, B2B focus" in the criteria field
    And I click "Filter Top 10 Firms"
    Then I should see a loading indicator
    And I should be navigated to the Results List page within 60 seconds

  Scenario: User submits empty criteria
    Given I have uploaded a valid Excel file
    When I leave the criteria field empty
    And I click "Filter Top 10 Firms"
    Then I should see an error message "Please enter filtering criteria"
    And the form should not submit
```

#### AC-RS-003: API Key Configuration

```gherkin
Feature: API Key Management

  Scenario: User configures valid API key
    Given I am on the Run Setup page
    And no API key is configured
    When I enter a valid OpenAI API key starting with "sk-"
    And I click "Save API Key"
    Then I should see a success indicator "API Key configured"
    And the key should be masked (showing only last 4 characters)

  Scenario: User enters invalid API key
    Given I am on the Run Setup page
    When I enter "invalid-key-format"
    And I click "Save API Key"
    Then I should see an error message "Invalid API key format"
```

### 7.2 Results List Page

#### AC-RL-001: Results Display

```gherkin
Feature: Results Display

  Scenario: Results loaded successfully
    Given filtering has completed with 10 results
    When I navigate to the Results List page
    Then I should see 10 firm cards/rows
    And each result should display: rank, name, score, industry, stage, reason
    And results should be sorted by score descending by default

  Scenario: Click firm to view memo
    Given I am viewing the Results List
    When I click on a firm name "TechCorp AI"
    Then I should be navigated to the Memo View page for TechCorp AI
    And the URL should update to /memo/{firmId}
```

#### AC-RL-002: DataGrid Functionality

```gherkin
Feature: DataGrid Interactions

  Scenario: Sort by column
    Given I am viewing the Results List
    When I click on the "Score" column header
    Then results should be sorted by score ascending
    When I click on the "Score" column header again
    Then results should be sorted by score descending

  Scenario: Filter results
    Given I am viewing the Results List
    When I open the filter panel
    And I select "Series A" in the Stage filter
    Then only firms with Stage "Series A" should be displayed
    And the result count should update accordingly
```

#### AC-RL-003: Export Functionality

```gherkin
Feature: Export Results

  Scenario: Export to CSV
    Given I am viewing the Results List with 10 results
    When I click Export and select "CSV"
    Then a CSV file should be downloaded
    And the file should contain all 10 results with columns: Rank, Name, Score, Industry, Stage, Reason
```

### 7.3 Memo View Page

#### AC-MV-001: Memo Display

```gherkin
Feature: Memo Content Display

  Scenario: View complete memo
    Given I am viewing the memo for "TechCorp AI"
    Then I should see the firm header with name and score
    And I should see badges for industry, stage, location
    And I should see the match reason
    And I should see accordion sections for all memo content
    And "Company Information" and "Quantitative Data" should be expanded by default

  Scenario: Expand/collapse sections
    Given I am viewing a memo
    When I click on the "Industry Background" section header
    Then the section should expand showing the content
    When I click on the section header again
    Then the section should collapse
```

#### AC-MV-002: Research Data

```gherkin
Feature: Research Data Integration

  Scenario: Research data available
    Given the firm has completed research data
    When I view the memo
    Then all sections should show populated content
    And the research status should show "Complete"

  Scenario: Research data missing
    Given the firm has no research data
    When I view the memo
    Then I should see "Research not available" messages in content sections
    And I should see a "Conduct Research" button
    When I click "Conduct Research"
    Then research should begin and status should show "Researching..."
```

#### AC-MV-003: Actions

```gherkin
Feature: Memo Actions

  Scenario: Create deal from memo
    Given I am viewing a memo
    When I click "Create Deal" in the sidebar
    Then a modal/form should appear with pre-filled firm information
    And I should be able to create a new deal

  Scenario: Export memo to PDF
    Given I am viewing a memo
    When I click "Export PDF"
    Then a PDF document should be generated and downloaded
    And the PDF should contain all memo sections
```

### 7.4 Accessibility Requirements

#### AC-A11Y-001: Keyboard Navigation

```gherkin
Feature: Keyboard Accessibility

  Scenario: Navigate with keyboard only
    Given I am using keyboard navigation
    When I press Tab
    Then focus should move through interactive elements in logical order
    And focus indicators should be clearly visible
    And I should be able to activate buttons with Enter or Space

  Scenario: DataGrid keyboard navigation
    Given I am focused on the DataGrid
    When I press Arrow Down
    Then focus should move to the next row
    When I press Enter
    Then the firm memo should open
```

#### AC-A11Y-002: Screen Reader Support

```gherkin
Feature: Screen Reader Accessibility

  Scenario: Results announced correctly
    Given I am using a screen reader
    When results are loaded
    Then I should hear "10 results found"
    And each result should be announced with rank, name, and score

  Scenario: Form errors announced
    Given I am using a screen reader
    When a form validation error occurs
    Then the error message should be announced
    And focus should move to the first field with an error
```

### 7.5 Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Initial page load (LCP) | < 2.5s | Lighthouse |
| Time to Interactive (TTI) | < 3.5s | Lighthouse |
| First Input Delay (FID) | < 100ms | Core Web Vitals |
| Cumulative Layout Shift (CLS) | < 0.1 | Core Web Vitals |
| DataGrid render (100 rows) | < 100ms | Performance API |
| Sort operation | < 50ms | Performance API |
| Filter operation | < 100ms | Performance API |
| Memo page load | < 1s | Performance API |

---

## 8. Dev Assignments

### 8.1 Team Structure

| Role | Responsibility |
|------|----------------|
| **Frontend Lead** | Architecture, code review, integration |
| **UI Engineer 1** | Run Setup page, file upload, form handling |
| **UI Engineer 2** | Results List page, DataGrid implementation |
| **UI Engineer 3** | Memo View page, accordion, sidebar |
| **Design Engineer** | Design system, tokens, component library |

### 8.2 Sprint Breakdown

#### Sprint 1: Foundation (Week 1-2)

| Task | Assignee | Estimate | Dependencies |
|------|----------|----------|--------------|
| Set up React/TypeScript project | Frontend Lead | 4h | — |
| Configure Tailwind + CSS variables | Design Engineer | 8h | — |
| Implement design tokens | Design Engineer | 16h | — |
| Create AppShell component | Frontend Lead | 8h | Design tokens |
| Create base Button component | Design Engineer | 4h | Design tokens |
| Create base Input component | Design Engineer | 4h | Design tokens |
| Create Badge component | Design Engineer | 4h | Design tokens |
| Set up routing (React Router) | Frontend Lead | 4h | AppShell |
| API client setup (React Query) | Frontend Lead | 8h | — |

#### Sprint 2: Run Setup Page (Week 3-4)

| Task | Assignee | Estimate | Dependencies |
|------|----------|----------|--------------|
| FileUploader component | UI Engineer 1 | 16h | Base components |
| File drag-and-drop | UI Engineer 1 | 8h | FileUploader |
| Excel preview component | UI Engineer 1 | 12h | FileUploader |
| CriteriaInput component | UI Engineer 1 | 8h | Base Input |
| API Key input/storage | UI Engineer 1 | 8h | Base Input |
| Run Setup page assembly | UI Engineer 1 | 8h | All above |
| Form validation (Zod) | UI Engineer 1 | 8h | Run Setup page |
| Loading/error states | UI Engineer 1 | 8h | Run Setup page |

#### Sprint 3: Results List Page (Week 5-6)

| Task | Assignee | Estimate | Dependencies |
|------|----------|----------|--------------|
| DataGrid base component | UI Engineer 2 | 24h | Base components |
| ScoreBar cell renderer | UI Engineer 2 | 4h | DataGrid |
| Link cell renderer | UI Engineer 2 | 4h | DataGrid |
| Truncate cell renderer | UI Engineer 2 | 4h | DataGrid |
| Column sorting | UI Engineer 2 | 8h | DataGrid |
| Column filtering | UI Engineer 2 | 8h | DataGrid |
| Filter panel component | UI Engineer 2 | 12h | DataGrid |
| Export functionality | UI Engineer 2 | 8h | DataGrid |
| Results List page assembly | UI Engineer 2 | 8h | All above |

#### Sprint 4: Memo View Page (Week 7-8)

| Task | Assignee | Estimate | Dependencies |
|------|----------|----------|--------------|
| Accordion component | UI Engineer 3 | 12h | Base components |
| Firm header component | UI Engineer 3 | 8h | Badge |
| Quantitative data grid | UI Engineer 3 | 12h | Base components |
| Memo sidebar component | UI Engineer 3 | 12h | Base components |
| Research status indicator | UI Engineer 3 | 4h | Badge |
| Create Deal modal | UI Engineer 3 | 12h | Form components |
| PDF export | UI Engineer 3 | 12h | — |
| Memo View page assembly | UI Engineer 3 | 8h | All above |

#### Sprint 5: Integration & Polish (Week 9-10)

| Task | Assignee | Estimate | Dependencies |
|------|----------|----------|--------------|
| End-to-end flow testing | All | 16h | All pages |
| Accessibility audit & fixes | Design Engineer | 16h | All pages |
| Performance optimization | Frontend Lead | 16h | All pages |
| Responsive design polish | Design Engineer | 16h | All pages |
| Error handling improvements | All | 8h | All pages |
| Documentation | Frontend Lead | 8h | — |
| Final QA & bug fixes | All | 24h | All above |

### 8.3 Definition of Done

A feature is considered "Done" when:

- [ ] Code is written and follows style guide
- [ ] Unit tests written with >80% coverage
- [ ] Integration tests for critical paths
- [ ] Accessibility audit passes (WCAG 2.1 AA)
- [ ] Performance targets met
- [ ] Code reviewed by at least one peer
- [ ] Design review approved
- [ ] Documentation updated
- [ ] No known bugs
- [ ] Deployed to staging environment

---

## 9. Appendix

### 9.1 File Structure

```
src/
├── app/
│   ├── layout.tsx
│   ├── page.tsx (Run Setup)
│   ├── results/
│   │   └── page.tsx
│   └── memo/
│       └── [id]/
│           └── page.tsx
├── components/
│   ├── ui/
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Badge/
│   │   ├── Accordion/
│   │   ├── DataGrid/
│   │   ├── FileUploader/
│   │   └── ...
│   ├── layout/
│   │   ├── AppShell/
│   │   ├── Header/
│   │   ├── Navigation/
│   │   └── StatusBar/
│   └── features/
│       ├── run-setup/
│       ├── results-list/
│       └── memo-view/
├── hooks/
│   ├── useFileUpload.ts
│   ├── useFilterResults.ts
│   └── useMemoData.ts
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── firms.ts
│   │   └── research.ts
│   ├── utils/
│   └── validators/
├── stores/
│   ├── filterStore.ts
│   └── resultsStore.ts
├── styles/
│   ├── globals.css
│   └── tokens.css
└── types/
    ├── firm.ts
    ├── research.ts
    └── api.ts
```

### 9.2 API Contracts (Expected)

```typescript
// Filter Request
POST /api/filter
{
  criteria: string;
  fileData: Base64String;
  options?: {
    skipRows?: number;
    nameColumn?: string;
  };
}

// Filter Response
{
  results: FirmResult[];
  metadata: {
    totalProcessed: number;
    processingTimeMs: number;
    cacheHitRate: number;
  };
}

// Research Request
POST /api/research/{firmId}
{
  firmName: string;
  additionalInfo?: Record<string, string>;
}

// Research Response
{
  companyName: string;
  countryOfIncorporation: string;
  industry: string;
  quantitativeData: Record<string, string>;
  industryBackground: string;
  companyBackground: string;
  founderProfile: string;
  competition: string;
  validation: {
    isComplete: boolean;
    qualityScore: number;
    missingFields: string[];
  };
}
```

### 9.3 Design System Component Checklist

| Component | Status | Assignee |
|-----------|--------|----------|
| Button | 🔲 | Design Engineer |
| Input | 🔲 | Design Engineer |
| Textarea | 🔲 | Design Engineer |
| Select | 🔲 | Design Engineer |
| Checkbox | 🔲 | Design Engineer |
| Badge | 🔲 | Design Engineer |
| Card | 🔲 | Design Engineer |
| Accordion | 🔲 | UI Engineer 3 |
| DataGrid | 🔲 | UI Engineer 2 |
| FileUploader | 🔲 | UI Engineer 1 |
| Modal | 🔲 | Design Engineer |
| Toast | 🔲 | Design Engineer |
| Tooltip | 🔲 | Design Engineer |
| Progress | 🔲 | Design Engineer |
| Skeleton | 🔲 | Design Engineer |
| EmptyState | 🔲 | Design Engineer |
| ErrorState | 🔲 | Design Engineer |

### 9.4 Browser Support Matrix

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |
| Mobile Safari | 14+ |
| Chrome Android | 90+ |

### 9.5 References

- [Current Streamlit Prototype](./streamlit_app.py)
- [Radix UI Primitives](https://www.radix-ui.com/)
- [TanStack Table](https://tanstack.com/table)
- [Tailwind CSS](https://tailwindcss.com/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-22 | EngSpec Lead | Initial production UI spec |

---

*This specification preserves the existing business flow (Excel→criteria→run→results list→click firm→memo) and memo content structure while defining a production-grade UI implementation.*
