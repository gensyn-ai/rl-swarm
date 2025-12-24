import { getLatestApiKey, getUser } from "@/app/db";
import { NextResponse } from "next/server";
import { userOperationHandler } from "@/app/lib/userOperationHandler";

export async function POST(request: Request) {
// Parse and validate JSON; catch parse errors early
let body: {
  orgId: string;
  roundNumber: bigint;
  stageNumber: bigint;
  reward: bigint;
  peerId: string;
};
try {
  body = await request.json();
} catch (err) {
  console.error("failed to parse json", err);
  return NextResponse.json({ error: "bad request generic" }, { status: 400 });
}
// Validate orgId immediately after parsing
if (!body?.orgId) {
  return NextResponse.json({ error: "bad request orgID" }, { status: 400 });
}

try {
  // Ensure the organisation exists
  const user = getUser(body.orgId);
  if (!user) {
    return NextResponse.json({ error: "user not found" }, { status: 404 });
  }

  // Wait for API key activation to avoid race conditions with key issuance
  let apiKey = getLatestApiKey(body.orgId);
  const maxAttempts = 5;
  let attempts = 0;

  while (apiKey && !apiKey.activated && attempts < maxAttempts) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    apiKey = getLatestApiKey(body.orgId);
    attempts++;
  }

  if (!apiKey || !apiKey.activated) {
    return NextResponse.json(
      { error: "api key not activated" },
      { status: 503 },
    );
  }

  const { accountAddress, privateKey, initCode, deferredActionDigest } = apiKey;

  const userOperationResponse = await userOperationHandler({
    accountAddress,
    privateKey,
    deferredActionDigest,
    initCode,
    functionName: "submitReward",
    args: [body.roundNumber, body.stageNumber, body.reward, body.peerId],
  });

  return userOperationResponse;
} catch (err) {
  console.error(err);
  return NextResponse.json(
    { error: "An unexpected error occurred", original: err },
    { status: 500 },
  );
}
