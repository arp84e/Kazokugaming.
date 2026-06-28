export default function manifest() {
  return {
    name: "KazokuGaming",
    short_name: "KazokuGaming",
    description:
      "Noticias de videojuegos, tecnología e inteligencia artificial en español.",
    start_url: "/",
    display: "standalone",
    background_color: "#0b0f19",
    theme_color: "#66c0f4",
    icons: [
      {
        src: "/icon-192.png",
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/icon-512.png",
        sizes: "512x512",
        type: "image/png",
      },
    ],
  };
}
