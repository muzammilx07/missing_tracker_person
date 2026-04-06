import { Manrope, Sora } from "next/font/google";
import "./globals.css";
import "react-toastify/dist/ReactToastify.css";
import AppChrome from "@/components/AppChrome";
import ClientToaster from "@/components/ClientToaster";

const manrope = Manrope({
  subsets: ["latin"],
  variable: "--font-body",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-display",
});

export const metadata = {
  title: "Missing Person Tracker",
  description: "Missing person case tracking and sighting workflows",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${manrope.variable} ${sora.variable} bg-(--background) text-(--foreground)`}
      >
        <AppChrome>{children}</AppChrome>
        <ClientToaster />
      </body>
    </html>
  );
}
