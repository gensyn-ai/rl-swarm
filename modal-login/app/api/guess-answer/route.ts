import { getLatestApiKey, getUser } from "@/app/db";
import { NextResponse } from "next/server";
import { userOperationHandler } from "@/app/lib/userOperationHandler";
import prgContract from "@/app/lib/prg_contract.json";

export async function POST(request: Request) {
  const body: {
    orgId: string;
    gameId: bigint;
    peerId: string;
    clueId: bigint;
    choiceIdx: bigint;
    bet: bigint;
  } = await request.json().catch((err) => {
    console.error(err);
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
    const user = await getUser(body.orgId);
    if (!user) {
      return NextResponse.json(
        { error: "user not found" },
        {
          status: 404,
        },
      );
    }
    const apiKey = await getLatestApiKey(body.orgId);
    if (!apiKey?.activated) {
      return NextResponse.json(
        { error: "api key not found" },
        {
          status: 500,
        },
      );
    }

    const { accountAddress, privateKey, initCode, deferredActionDigest } = apiKey;

    const userOperationResponse = await userOperationHandler({
      accountAddress,
      privateKey,
      deferredActionDigest,
      initCode,
      functionName: "guessAnswer",
      args: [body.gameId, body.peerId, body.clueId, body.choiceIdx, body.bet],
      contract: {
        ...prgContract,
        address: process.env.PRG_CONTRACT_ADDRESS,
      },
    });
    console.log('Guess answer response: ', userOperationResponse);
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
