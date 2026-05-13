import { NextResponse } from "next/server";
import { buildHRWorkbook } from "@/lib/excel";

export const dynamic = "force-dynamic";

export async function GET() {
  const buf = await buildHRWorkbook();
  const filename = `Meridian_HR_Dashboard_${new Date().toISOString().slice(0, 10)}.xlsx`;

  // Buffer is valid BodyInit at runtime; cast to satisfy strict TS types.
  return new NextResponse(buf as unknown as BodyInit, {
    status: 200,
    headers: {
      "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Content-Length": buf.byteLength.toString(),
      "Cache-Control": "no-store",
    },
  });
}
