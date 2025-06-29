import { setApiKeyActivated } from "@/app/db";
import { hexSchema } from "@/app/lib/schemas";
import { NextResponse } from "next/server";
import z from "zod";

const bodySchema = z.object({
  orgId: z.string(),
  apiKey: hexSchema,
  deferredActionDigest: hexSchema,
  accountAddress: hexSchema,
  initCode: hexSchema,
});

export async function POST(request: Request) {
  const rawBody: {
    orgId: string;
    apiKey: string;
    deferredActionDigest: string;
    accountAddress: string;
    initCode: string;
  } = await request.json().catch((err) => {
    console.error(err);
    return NextResponse.json(
      { json: { error: "bad request" } },
      { status: 400 },
    );
  });

  const bodyResult = bodySchema.safeParse(rawBody);

  if (!bodyResult.success) {
    console.error(bodyResult.error);
    return NextResponse.json(
      { json: { error: "bad request", details: bodyResult.error } },
      { status: 400 },
    );
  }

  const body = bodyResult.data;

  try {
    setApiKeyActivated(
      body.orgId,
      body.apiKey,
      body.deferredActionDigest,
      body.accountAddress,
      body.initCode,
    );
    return NextResponse.json({ activated: true }, { status: 200 });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ json: { error: "error" } }, { status: 500 });
  }
}
