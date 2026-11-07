import { Composition } from "remotion";
import { Assembly, TITLE } from "./Assembly";
import F from "../../frames.json";

export const Root = () => (
  <Composition id="Assembly" component={Assembly} width={1920} height={1080} fps={F.fps} durationInFrames={TITLE + F.frames} />
);
