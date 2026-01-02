import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "hadiscover - Discover Home Assistant Automations",
  description:
    "Search and explore powerful Home Assistant automations from the community. Find triggers, actions, and blueprints shared on GitHub.",
  icons: {
    icon: "/favicon.ico",
    apple: "/logo.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
