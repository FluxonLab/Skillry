---
name: shadcn-ui-components
description: Use when adding, customising, or reviewing shadcn/ui components in a Next.js or React project — covering CLI installation, CSS variable theming, dark mode, react-hook-form + Zod form patterns, and Radix UI accessibility compliance.
---

# shadcn/ui Components

## Purpose

Deliver production-ready shadcn/ui integration: CLI-driven component installation, CSS variable theming (light + dark), form composition with react-hook-form and Zod, table and data display patterns, accessible dialog and toast usage, and common mistakes that break Tailwind purging or Radix a11y contracts. Every pattern targets Next.js 14+ App Router with TypeScript.

## When to use

- Adding a new UI component (Button, Dialog, Form, Table, Toast, Select, DatePicker, etc.) to a Next.js or React project.
- Setting up shadcn/ui from scratch in a new project.
- Customising the default theme (colours, radius, font) via CSS variables.
- Implementing a form with client-side + server-side validation.
- Reviewing a PR that adds or modifies shadcn components for a11y and theme parity.
- Extending a shadcn component with a custom variant or prop.

## When not to use

- The project uses a different component library (MUI, Chakra, Ant Design) — do not mix.
- The task is a backend or API route with no UI surface.
- The component needed is trivially styled with raw Tailwind and has no Radix dependency.

## Procedure

### 1. Initial setup

```bash
# New Next.js project with shadcn/ui
npx create-next-app@latest my-app --typescript --tailwind --app --src-dir
cd my-app
npx shadcn@latest init

# Prompts: style (Default/New York), base colour, CSS variables (yes)
# This creates: components/ui/, lib/utils.ts, tailwind.config.ts updates
```

`components/ui/` is generated — do not edit generated files directly; extend them via composition.

`lib/utils.ts` (auto-generated):
```typescript
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
 return twMerge(clsx(inputs))
}
```

### 2. Adding components

```bash
# Add individual components
npx shadcn@latest add button
npx shadcn@latest add dialog
npx shadcn@latest add form input label select textarea
npx shadcn@latest add table
npx shadcn@latest add toast
npx shadcn@latest add dropdown-menu
npx shadcn@latest add sheet # side drawer
npx shadcn@latest add command # command palette (cmdk)
npx shadcn@latest add date-picker # Calendar + Popover

# Add multiple at once
npx shadcn@latest add button card badge separator skeleton
```

### 3. CSS variable theming — light + dark

shadcn/ui uses CSS custom properties for all colours. Override in `app/globals.css`:

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
 :root {
 /* Light theme */
 --background: 0 0% 100%;
 --foreground: 222.2 84% 4.9%;
 --card: 0 0% 100%;
 --card-foreground: 222.2 84% 4.9%;
 --popover: 0 0% 100%;
 --popover-foreground: 222.2 84% 4.9%;
 --primary: 221.2 83.2% 53.3%; /* indigo-500 */
 --primary-foreground: 210 40% 98%;
 --secondary: 210 40% 96.1%;
 --secondary-foreground: 222.2 47.4% 11.2%;
 --muted: 210 40% 96.1%;
 --muted-foreground: 215.4 16.3% 46.9%;
 --accent: 210 40% 96.1%;
 --accent-foreground: 222.2 47.4% 11.2%;
 --destructive: 0 84.2% 60.2%;
 --destructive-foreground: 210 40% 98%;
 --border: 214.3 31.8% 91.4%;
 --input: 214.3 31.8% 91.4%;
 --ring: 221.2 83.2% 53.3%;
 --radius: 0.5rem;
 }

 .dark {
 /* Dark theme — every variable must be redefined */
 --background: 222.2 84% 4.9%;
 --foreground: 210 40% 98%;
 --card: 222.2 84% 4.9%;
 --card-foreground: 210 40% 98%;
 --popover: 222.2 84% 4.9%;
 --popover-foreground: 210 40% 98%;
 --primary: 217.2 91.2% 59.8%;
 --primary-foreground: 222.2 47.4% 11.2%;
 --secondary: 217.2 32.6% 17.5%;
 --secondary-foreground: 210 40% 98%;
 --muted: 217.2 32.6% 17.5%;
 --muted-foreground: 215 20.2% 65.1%;
 --accent: 217.2 32.6% 17.5%;
 --accent-foreground: 210 40% 98%;
 --destructive: 0 62.8% 30.6%;
 --destructive-foreground: 210 40% 98%;
 --border: 217.2 32.6% 17.5%;
 --input: 217.2 32.6% 17.5%;
 --ring: 224.3 76.3% 48%;
 }
}
```

Dark mode wiring with `next-themes`:
```bash
npm install next-themes
```

```typescript
// app/providers.tsx
'use client'
import { ThemeProvider } from 'next-themes'

export function Providers({ children }: { children: React.ReactNode }) {
 return (
 <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
 {children}
 </ThemeProvider>
 )
}

// components/ThemeToggle.tsx
'use client'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'
import { Moon, Sun } from 'lucide-react'

export function ThemeToggle() {
 const { theme, setTheme } = useTheme()
 return (
 <Button variant="ghost" size="icon"
 onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
 <Sun className="h-4 w-4 rotate-0 scale-100 dark:-rotate-90 dark:scale-0 transition-all" />
 <Moon className="absolute h-4 w-4 rotate-90 scale-0 dark:rotate-0 dark:scale-100 transition-all" />
 </Button>
 )
}
```

### 4. Form with react-hook-form + Zod

```bash
npm install react-hook-form zod @hookform/resolvers
```

```typescript
// components/SignUpForm.tsx
'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
 Form, FormControl, FormDescription, FormField, FormItem,
 FormLabel, FormMessage,
} from '@/components/ui/form'

const schema = z.object({
 email: z.string().email('Enter a valid email'),
 password: z.string().min(8, 'At least 8 characters'),
 confirmPassword: z.string(),
}).refine(d => d.password === d.confirmPassword, {
 message: 'Passwords do not match',
 path: ['confirmPassword'],
})

type FormData = z.infer<typeof schema>

export function SignUpForm() {
 const form = useForm<FormData>({
 resolver: zodResolver(schema),
 defaultValues: { email: '', password: '', confirmPassword: '' },
 })

 async function onSubmit(data: FormData) {
 // Server Action or API call
 console.log(data)
 }

 return (
 <Form {...form}>
 <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
 <FormField control={form.control} name="email" render={({ field }) => (
 <FormItem>
 <FormLabel>Email</FormLabel>
 <FormControl>
 <Input placeholder="you@example.com" type="email" {...field} />
 </FormControl>
 <FormDescription>We will never share your email.</FormDescription>
 <FormMessage /> {/* renders Zod error */}
 </FormItem>
 )} />

 <FormField control={form.control} name="password" render={({ field }) => (
 <FormItem>
 <FormLabel>Password</FormLabel>
 <FormControl><Input type="password" {...field} /></FormControl>
 <FormMessage />
 </FormItem>
 )} />

 <FormField control={form.control} name="confirmPassword" render={({ field }) => (
 <FormItem>
 <FormLabel>Confirm password</FormLabel>
 <FormControl><Input type="password" {...field} /></FormControl>
 <FormMessage />
 </FormItem>
 )} />

 <Button type="submit" disabled={form.formState.isSubmitting}>
 {form.formState.isSubmitting ? 'Creating account...' : 'Sign up'}
 </Button>
 </form>
 </Form>
 )
}
```

### 5. Custom component variants

```typescript
// Extend Button with a new variant using cva (class-variance-authority — already a dependency)
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import { ButtonHTMLAttributes, forwardRef } from 'react'

const buttonVariants = cva(
 'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
 {
 variants: {
 variant: {
 default: 'bg-primary text-primary-foreground hover:bg-primary/90',
 secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
 ghost: 'hover:bg-accent hover:text-accent-foreground',
 danger: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
 // Custom variant:
 game: 'bg-amber-500 text-white font-bold tracking-wide hover:bg-amber-400 active:scale-95',
 },
 size: {
 default: 'h-10 px-4 py-2',
 sm: 'h-9 rounded-md px-3',
 lg: 'h-11 rounded-md px-8',
 icon: 'h-10 w-10',
 },
 },
 defaultVariants: { variant: 'default', size: 'default' },
 },
)

export interface ButtonProps
 extends ButtonHTMLAttributes<HTMLButtonElement>,
 VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
 ({ className, variant, size, ...props }, ref) => (
 <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
 ),
)
Button.displayName = 'Button'
export { Button, buttonVariants }
```

## Concrete checks

- [ ] `npx shadcn@latest add <component>` used — files never manually copied from GitHub.
- [ ] All CSS variable pairs (`:root` and `.dark`) defined for every custom colour token.
- [ ] `ThemeProvider` wraps the root layout; `attribute="class"` so Tailwind `dark:` variants fire.
- [ ] Form uses `<Form>` + `<FormField>` + `<FormMessage>` — no raw `<input>` without validation wiring.
- [ ] `zodResolver` passed to `useForm` — client validation matches server schema.
- [ ] Dialog uses `<DialogContent>` with `aria-describedby` or `DialogDescription` — Radix a11y requirement.
- [ ] Toast (`useToast`) called from `'use client'` components only.
- [ ] `cn()` used for conditional class merging — never string concatenation with Tailwind classes.
- [ ] No hardcoded colour values (e.g. `text-gray-700`) where a CSS variable token exists.

## Commands

```bash
# Check installed shadcn version
npx shadcn@latest --version

# Add a component (idempotent — safe to re-run)
npx shadcn@latest add <component-name>

# List all available components
npx shadcn@latest add --help

# Verify CSS variable tokens are applied (browser console)
getComputedStyle(document.documentElement).getPropertyValue('--primary')

# Type-check form schema and component props
npx tsc --noEmit
```

## Required output

When adding or reviewing shadcn components, deliver:
1. Component install command (`npx shadcn@latest add ...`).
2. CSS variable tokens defined in both `:root` and `.dark` — list any gaps.
3. Form schema (Zod) matching the server validation shape.
4. Accessibility contract: Dialog `aria-describedby`, Select keyboard navigation, Toast `role="alert"`.
5. `cn()` usage confirmed for all conditional classes.
6. Dark mode screenshot or description (both themes must render without clipped or invisible text).

## Safety checks

- Never edit files inside `components/ui/` generated by shadcn — they will be overwritten on next `add`. Wrap and extend instead.
- Do not import Radix UI primitives directly alongside shadcn — use shadcn's re-exported wrappers to stay on one version.
- `useToast` must be inside a Client Component (`'use client'`); Server Components cannot call hooks.
- `z.string().min(1)` is not the same as `z.string().nonempty()` — both work, but be consistent.

## Completion criteria

Done means: all added components render in both light and dark mode without colour defects, every form field has a `FormMessage` for validation errors, `npx tsc --noEmit` passes with no type errors, and a screen reader can navigate all interactive components (Dialog, Select, DropdownMenu) via keyboard alone.
