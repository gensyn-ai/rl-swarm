import { upsertUser } from "@/app/db";
import crypto from "crypto";
import { NextResponse } from "next/server";
import { TSignedRequest } from "@turnkey/http";
import { generatePrivateKey, privateKeyToAccount } from "viem/accounts";

const ALCHEMY_BASE_URL = "https://api.g.alchemy.com";

export async function POST(request: Request) {
  const body: {
    whoamiStamp: TSignedRequest;
  } = await request.json().catch((err) => {
    console.error(err);
    return NextResponse.json(
      { json: { error: "bad request" } },
      { status: 400 },
    );
  });

  try {
    const alchemyResp = await fetch(`${ALCHEMY_BASE_URL}/signer/v1/whoami`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.NEXT_PUBLIC_ALCHEMY_API_KEY}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        stampedRequest: body.whoamiStamp,
      }),
    });

    if (!alchemyResp.ok) {
      console.error(await alchemyResp.text());
      throw new Error("Alchemy whoami request failed");
    }

    const userData: {
      userId: string;
      orgId: string;
      address: string;
      email?: string; // Only exists if using email auth flow
    } = await alchemyResp.json();

    // Generate & store a key.
    const { publicKey, privateKey } = await generateKeyPair();
    upsertUser(userData, {
      privateKey,
      publicKey,
      createdAt: new Date(),
      activated: false,
    });

    return NextResponse.json({ publicKey }, { status: 200 });
  } catch (err) {
    console.error(err);
    return NextResponse.json({ json: { error: "error" } }, { status: 500 });
  }
}

async function generateKeyPair() {
  const privateKey = generatePrivateKey();
  const account = privateKeyToAccount(privateKey);

  // `account` has a `publicKey` field but Alchemy team mentions this should
  // be the `address`
  const publicKey = account.address;

  return {
    publicKey,
    privateKey,
  };
}
