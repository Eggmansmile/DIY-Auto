import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Same house style as the HTL laser video
export const C = { paper: "#F1F0EC", ink: "#171717", graphite: "#5B5C55", rule: "#D8D7D1", orange: "#EF8D08" };
export const FONT = "Schibsted Grotesk";
loadFont({ family: FONT, url: staticFile("SchibstedGrotesk.ttf"), weight: "100 900" });
