"use client";

import { BookOpen, Layers, Sun, User } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useT, type Key } from "@/lib/i18n";
import { useDb } from "@/lib/store/db";

const TABS: { href: string; key: Key; icon: typeof Sun }[] = [
  { href: "/today", key: "nav.today", icon: Sun },
  { href: "/decks", key: "nav.decks", icon: Layers },
  { href: "/dictionary", key: "nav.dictionary", icon: BookOpen },
  { href: "/me", key: "nav.me", icon: User },
];

export function TabBar() {
  const pathname = usePathname();
  const { t } = useT();
  const db = useDb();
  const firstName = db.me?.profile.name.split(" ")[0];
  return (
    <nav aria-label={t("nav.main")} className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-card/95 backdrop-blur">
      <ul className="mx-auto flex max-w-[640px] items-stretch justify-around px-2 pb-[env(safe-area-inset-bottom)]">
        {TABS.map(({ href, key, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(`${href}/`);
          const label = key === "nav.me" && firstName ? firstName : t(key);
          return (
            <li key={href} className="flex-1">
              <Link
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex h-16 flex-col items-center justify-center gap-1 text-[11px] transition ${active ? "font-extrabold text-ink" : "font-semibold text-ink-3 hover:text-ink-2"}`}
              >
                <span className={`grid h-7 w-12 place-items-center rounded-full transition ${active ? "bg-peach" : ""}`}>
                  <Icon className={`size-[22px] ${active ? "text-primary" : ""}`} strokeWidth={active ? 2.5 : 2} aria-hidden />
                </span>
                <span className="max-w-[80px] truncate">{label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
