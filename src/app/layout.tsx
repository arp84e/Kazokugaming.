import './globals.css';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'KazokuGaming | Videojuegos, Tecnología e IA',
  description: 'Portal hispano especializado en videojuegos, hardware, inteligencia artificial, guías y herramientas interactivas.',
  openGraph: {
    title: 'KazokuGaming',
    description: 'El nexo del gaming, la tecnología y la IA.',
    url: 'https://kazokugaming.com',
    siteName: 'KazokuGaming',
    locale: 'es_ES',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body className="antialiased min-h-screen flex flex-col justify-between">
        {/* Aquí irá el Navbar en el futuro */}
        <main className="flex-grow">{children}</main>
        {/* Aquí irá el Footer en el futuro */}
      </body>
    </html>
  );
}
