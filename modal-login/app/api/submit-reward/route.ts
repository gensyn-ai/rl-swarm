import { getLatestApiKey, getUser } from "@/app/db";
import { NextResponse } from "next/server";
import { userOperationHandler } from "@/app/lib/userOperationHandler";

export async function POST(request: Request) {
  const body: {
    orgId: string;
    roundNumber: bigint;
    stageNumber: bigint;
    reward: bigint;
    peerId: string;
  } = await request.json().catch((err) => {
    console.error(err);
    console.log(body);
    return NextResponse.json(
      { error: "bad request generic" },
      {
        status: 400,
      },
    );
  });
  if (!body.orgId) {
    return NextResponse.json(
      { error: "bad request orgID" },
      {
        status: 400,
      },
    );
  }

  try {
    const user = getUser(body.orgId);
    if (!user) {
      return NextResponse.json(
        { error: "user not found" },
        {
          status: 404,
        },
      );
    }
    const apiKey = getLatestApiKey(body.orgId);
    if (!apiKey?.activated) {
      return NextResponse.json(
        { error: "api key not found" },
        {
          status: 500,
        },
      );
    }

    const { accountAddress, privateKey, initCode, deferredActionDigest } =
      apiKey;

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
      {
        error: "An unexpected error occurred",
        original: err,
      },
      {
        status: 500,
      },
    );
  }
}
