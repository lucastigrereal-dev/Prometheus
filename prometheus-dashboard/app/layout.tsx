import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Prometheus Command Center",
  description: "AI Knowledge Brain Dashboard + Executor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Navigation */}
        <nav className="bg-gray-900 border-b border-gray-800">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-8">
                <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Prometheus
                </Link>
                <div className="flex space-x-4">
                  <Link href="/" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                    Knowledge Brain
                  </Link>
                  <Link href="/executor" className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">
                    Executor
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {children}
      </body>
    </html>
  );
}
