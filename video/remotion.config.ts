import { Config } from "@remotion/cli/config";

// Les médias sont lus depuis le dossier /assets à la racine du dépôt.
Config.setPublicDir("../assets");
Config.setVideoImageFormat("jpeg");
Config.setJpegQuality(92);
Config.setCodec("h264");
Config.setPixelFormat("yuv420p");
Config.setCrf(18);
Config.setOverwriteOutput(true);


if (process.env.REMOTION_BROWSER) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER);
}
