"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  {
    name: "Encode",
    href: "/encode", // Corresponds to pages/encode/page.tsx
  },
  {
    name: "Decode",
    href: "/decode", // Corresponds to pages/decode/page.tsx
  },
  {
    name: "Community",
    href: "/community", // Corresponds to pages/community/page.tsx
  },
  {
    name: "GitHub",
    href: "https://github.com/TonyMontana-dev/ciphare",
    external: true,
  },
] satisfies { name: string; href: string; external?: boolean }[];

// Header component
// Renders the navigation links and logo in the header section of the app (navigation bar)
export const Header: React.FC = () => {
  const pathname = usePathname();  // Get the current path name
  return (
    <header className="top-0 z-30 w-full px-4 sm:fixed backdrop-blur bg-zinc-900/50">
      <div className="container mx-auto">
        <div className="flex flex-col items-center justify-between gap-2 pt-6 sm:h-20 sm:flex-row sm:pt-0">
          <Link href="/" className="text-2xl font-semibold duration-150 text-zinc-100 hover:text-white">
            Ciphare
          </Link>
          {/* Desktop navigation */}
          <nav className="flex items-center grow">
            <ul className="flex flex-wrap items-center justify-end gap-4 grow">
              {navigation.map((item) => (
                <li key={item.href}>
                  <Link
                    className={`flex items-center px-3 py-2 duration-150 text-sm sm:text-base hover:text-zinc-50
                    ${pathname === item.href ? "text-zinc-200" : "text-zinc-400"}`}
                    href={item.href}
                    target={item.external ? "_blank" : undefined}
                    rel={item.external ? "noopener noreferrer" : undefined}
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      {/* Optional: Fancy fading bottom border effect */}
      <div className="h-[1px] bg-gradient-to-r from-transparent via-zinc-600/50 to-transparent mt-2"></div>
    </header>
  );
};
