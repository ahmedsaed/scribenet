import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ClientNavbar from "@/components/layout/ClientNavbar";
import Footer from "@/components/layout/Footer";
import ToastContainer from "@/components/ToastContainer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ScribeNet - AI-Powered Book Writing",
  description: "Multi-Agent Book Writing System powered by AI",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="flex flex-col min-h-screen">
          <ClientNavbar />
          <main className="flex-1">
            {children}
          </main>
          <Footer />
        </div>
        <ToastContainer />
      </body>
    </html>
  );
}
