import { NextResponse } from "next/server";
import { meta } from "@/lib/queries";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    return NextResponse.json(await meta());
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
