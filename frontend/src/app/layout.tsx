import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Eco Monitor",
  description: "AI Ecosystem Monitoring System",
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
