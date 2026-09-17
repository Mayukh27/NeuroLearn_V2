"use client"

import { ShieldCheck } from "lucide-react"

/**
 * Shell for /admin — deliberately NOT the student Sidebar/Navbar. Admin is
 * a separate, non-gamified administrative interface: no XP/streak chrome,
 * no student nav items, and it is never reachable from the student sidebar.
 * The page itself (page.tsx) still owns the actual key-gate/unlock logic;
 * this layout only controls the surrounding chrome.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--bg-primary)] flex flex-col">
      <header className="flex items-center gap-2 h-14 px-6 border-b border-[var(--border-subtle)] shrink-0">
        <ShieldCheck size={18} className="text-violet-400" />
        <span className="text-sm font-semibold text-[var(--text-primary)]">
          NeuroLearn Admin
        </span>
      </header>
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}
