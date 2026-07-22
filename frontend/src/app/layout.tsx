import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { CurrencyProvider } from "@/context/CurrencyContext";
import { WorkspaceProvider } from "@/context/WorkspaceContext";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
  preload: true,
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
  preload: true,
});

export const metadata: Metadata = {
  title: "TradeCore | Professional Trading Journal & Market Screener",
  description: "Track your trades, analyze setups, audit your psychology, and screen the markets using Camarilla, CPR, and SMC.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${mono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <link rel="preconnect" href="http://localhost:8000" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="http://localhost:8000" />
      </head>
      <body className="min-h-full flex flex-col bg-tv-bg text-foreground font-sans" suppressHydrationWarning>
        <AuthProvider>
          <CurrencyProvider>
            <WorkspaceProvider>
              {children}
            </WorkspaceProvider>
          </CurrencyProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
