import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "hadiscover - Discover Home Assistant Automations from the Community",
  description:
    "Search and explore powerful Home Assistant automations from the community. Find triggers, actions, and blueprints shared on GitHub. Discover real-world automation examples to enhance your smart home.",
  keywords: [
    "Home Assistant",
    "automations",
    "smart home",
    "YAML",
    "GitHub",
    "home automation",
    "triggers",
    "blueprints",
    "IoT",
    "search engine",
  ],
  authors: [{ name: "DevSecNinja" }],
  creator: "DevSecNinja",
  publisher: "hadiscover",
  metadataBase: new URL("https://hadiscover.com"),
  alternates: {
    canonical: "https://hadiscover.com",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://hadiscover.com",
    title: "hadiscover - Discover Home Assistant Automations",
    description:
      "Search and explore powerful Home Assistant automations from the community. Find triggers, actions, and blueprints shared on GitHub.",
    siteName: "hadiscover",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "hadiscover - Home Assistant Automation Discovery",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "hadiscover - Discover Home Assistant Automations",
    description:
      "Search and explore powerful Home Assistant automations from the community. Find triggers, actions, and blueprints shared on GitHub.",
    images: ["/og-image.png"],
    creator: "@DevSecNinja",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0f" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <link rel="manifest" href="/site.webmanifest" />
        <meta name="theme-color" content="#0a0a0f" />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
