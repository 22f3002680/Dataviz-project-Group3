import { NextRequest, NextResponse } from "next/server";
import { seller } from "@/lib/queries";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const sp = req.nextUrl.searchParams;
  const week = sp.get("week") ?? "2018-08-13";
  const state = sp.get("state") || null;
  try {
    return NextResponse.json(await seller(week, state));
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
