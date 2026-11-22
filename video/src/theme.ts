import "@fontsource/cormorant-garamond/400.css";
import "@fontsource/cormorant-garamond/500.css";
import "@fontsource/cormorant-garamond/600.css";
import "@fontsource/cormorant-garamond/400-italic.css";
import "@fontsource/inter/300.css";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";

export const W = 1080;
export const H = 1920;
export const FPS = 30;

/** Palette DOMOVA : noir, blanc, anthracite, bois naturel, noyer, beige. */
export const C = {
  noir: "#0D0D0E",
  anthracite: "#26272A",
  anthraciteClair: "#3A3B3F",
  gris: "#8C8A86",
  blanc: "#F5F3EF",
  beige: "#D8C9B1",
  bois: "#C49A6C",
  noyer: "#5A3A22",
  led: "#FFD9A0",
};

export const F = {
  serif: "'Cormorant Garamond', 'Times New Roman', serif",
  sans: "Inter, 'Helvetica Neue', Arial, sans-serif",
};

/**
 * Zone de sécurité commune TikTok / Reels / Shorts (1080×1920) :
 * - haut : onglets et nom du compte  → rien d'important au-dessus de 230 px
 * - bas  : légende, musique, barre    → rien d'important sous 1460 px
 * - droite : boutons j'aime/commenter/partager → marge 170 px
 */
export const SAFE = { top: 230, bottom: 1460, left: 80, right: W - 170 };
export const SAFE_W = SAFE.right - SAFE.left;
export const SAFE_CX = (SAFE.left + SAFE.right) / 2;
/** Bande des sous-titres : centrale basse, au-dessus des commandes. */
export const SUB = { bottom: 1430, maxWidth: SAFE_W };
