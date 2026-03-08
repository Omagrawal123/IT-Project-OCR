import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Event Poster Extraction",
  description: "Extract structured event data from poster images using AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
