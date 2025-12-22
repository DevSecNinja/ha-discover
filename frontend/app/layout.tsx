import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HA Discover - Search Home Assistant Automations",
  description: "Discover and explore Home Assistant automations from GitHub repositories",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
