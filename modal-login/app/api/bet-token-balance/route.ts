import { getLatestApiKey, getUser } from "@/app/db";
import { NextResponse } from "next/server";
import { alchemy, gensynTestnet } from "@account-kit/infra";
import { createPublicClient, http } from "viem";
import prgContract from "@/app/lib/prg_contract.json";

export async function POST(request: Request) {
  const body: {
    orgId: string;
    peerId: string;
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

    const transport = alchemy({
      apiKey: process.env.NEXT_PUBLIC_ALCHEMY_API_KEY!,
    });

    const client = createPublicClient({
      chain: gensynTestnet,
      transport,
    });

    // Read the contract state directly since betTokenBalance is a view function
    const result = await client.readContract({
      address: process.env.PRG_CONTRACT_ADDRESS as `0x${string}`,
      abi: prgContract.abi,
      functionName: "betTokenBalance",
      args: [body.peerId],
    });

    const balance = result as bigint

    return NextResponse.json(
      {
        result: balance.toString(),
      },
      {
        status: 200,
      },
    );
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
