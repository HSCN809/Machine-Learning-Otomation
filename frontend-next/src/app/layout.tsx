import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

import { Providers } from "./providers";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ML Automation | Data Science Copilot",
  description: "Akıllı veri bilimi asistanı - Otomatik EDA, model önerisi ve hiperparametre optimizasyonu",
  keywords: ["machine learning", "data science", "AI", "automation", "EDA", "model training"],
  authors: [{ name: "ML Automation Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" className="dark">
      <body className={`${inter.variable} antialiased circuit-bg`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}

