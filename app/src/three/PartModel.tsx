import type { BracketDesign, CheckReport, FinDesign, PartId } from "../types";
import { BracketModel, bracketCentreY, bracketSize } from "./BracketModel";
import { FinModel, finCentreY, finSize } from "./FinModel";
import { PadeyeModel, padeyeFrame } from "./PadeyeModel";

/** Size and centre of the viewer for a part's design. */
export function partFrame(part: PartId, design: CheckReport["design"]): { size: number; centreY: number } {
  if (part === "pipe-bracket") {
    const d = design as unknown as BracketDesign;
    return { size: bracketSize(d), centreY: bracketCentreY(d) };
  }
  if (part === "stabilizer") {
    const d = design as unknown as FinDesign;
    return { size: finSize(d), centreY: finCentreY(d) };
  }
  return padeyeFrame(design);
}

/** The 3D model of any part. Check highlighting and the shackle are padeye-only. */
export function PartModel({
  part,
  report,
  slingAngleDeg = 60,
  showExtras = true,
  highlight = null,
}: {
  part: PartId;
  report: Pick<CheckReport, "design" | "shackle">;
  slingAngleDeg?: number;
  showExtras?: boolean;
  highlight?: string | null;
}) {
  if (part === "pipe-bracket") return <BracketModel design={report.design as unknown as BracketDesign} showPipe={showExtras} />;
  if (part === "stabilizer") return <FinModel design={report.design as unknown as FinDesign} />;
  return (
    <PadeyeModel
      design={report.design}
      pinDiameter={report.shackle?.pin_diameter_mm}
      jawWidth={report.shackle?.jaw_width_mm}
      slingAngleDeg={slingAngleDeg}
      showShackle={showExtras}
      highlight={highlight}
    />
  );
}

export const PART_NAMES: Record<PartId, { title: string; noun: string; plural: string }> = {
  padeye: { title: "Lifting padeye", noun: "padeye", plural: "padeyes" },
  "pipe-bracket": { title: "Pipe support bracket", noun: "bracket", plural: "brackets" },
  stabilizer: { title: "Stabilizer fin", noun: "fin", plural: "fins" },
};
