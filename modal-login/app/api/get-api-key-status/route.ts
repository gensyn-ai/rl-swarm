import { getLatestApiKey } from "@/app/db";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { orgId } = Object.fromEntries(new URL(request.url).searchParams);
  if (!orgId) {
    return NextResponse.json(
      { json: { error: "bad request" } },
      { status: 400 },
    );
  }

  try {
    const key = await getLatestApiKey(orgId);
    return new NextResponse(`${key?.activated ? "activated" : "pending"}`, {
      status: 200,
    });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ json: { error: "error" } }, { status: 500 });
  }
}