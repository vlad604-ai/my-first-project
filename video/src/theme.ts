import "@fontsource/jost/300.css";
import "@fontsource/jost/400.css";
import "@fontsource/jost/500.css";
import "@fontsource/jost/600.css";

export const W = 1080;
export const H = 1920;
export const FPS = 30;

/** Charte DOMOVA : bordeaux, crème, or (relevés sur les visuels de la marque). */
export const C = {
  bordeaux: "#4A1420",
  bordeauxFonce: "#2B0C13",
  bordeauxNuit: "#1C070C",
  arche: "#5E2A30", // trait fin des arches décoratives
  creme: "#F3E9DC",
  or: "#C9A46A",
  // alias utilisés dans les scènes
  noir: "#1C070C",
  anthracite: "#2B0C13",
  anthraciteClair: "#4A1420",
  gris: "#8C7F78",
  blanc: "#F3E9DC",
  beige: "#C9A46A",
  bois: "#C49A6C",
  noyer: "#5A3A22",
  led: "#C9A46A",
};

/** Typographie de la marque : géométrique (Jost), capitales très espacées. */
export const F = {
  serif: "Jost, 'Futura', 'Century Gothic', sans-serif",
  sans: "Jost, 'Futura', 'Century Gothic', sans-serif",
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
