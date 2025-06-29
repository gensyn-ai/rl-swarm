import { NextResponse } from "next/server";
import {
  alchemy,
  createAlchemySmartAccountClient,
  gensynTestnet,
} from "@account-kit/infra";
import { LocalAccountSigner } from "@aa-sdk/core";
import { createModularAccountV2 } from "@account-kit/smart-contracts";
import { sendUserOperation } from "@/app/lib/sendUserOperation";
import { encodeFunctionData, decodeErrorResult, Hex } from "viem";
import contract from "@/app/lib/contract.json";
import { httpRequestErroDetailsStringSchema } from "./HttpRequestError";

type UserOperationHandlerRequest = {
  accountAddress: Hex;
  privateKey: Hex;
  deferredActionDigest: Hex;
  initCode: Hex;
  functionName: string;
  args: unknown[];
};

/**
 * `userOperationHandler` is a shared handler for nextjs routes implementing
 * some of the common boiler plate used to send user operations to the chain.
 */
export async function userOperationHandler({
  accountAddress,
  privateKey,
  deferredActionDigest,
  initCode,
  functionName,
  args,
}: UserOperationHandlerRequest): Promise<NextResponse> {
  const transport = alchemy({
    apiKey: process.env.NEXT_PUBLIC_ALCHEMY_API_KEY!,
  });

  const account = await createModularAccountV2({
    transport,
    chain: gensynTestnet,
    accountAddress,
    signer: LocalAccountSigner.privateKeyToAccountSigner(privateKey),
    deferredAction: deferredActionDigest,
    initCode,
  });

  const client = createAlchemySmartAccountClient({
    account,
    chain: gensynTestnet,
    transport,
    policyId: process.env.NEXT_PUBLIC_PAYMASTER_POLICY_ID!,
  });

  const contractAddress = process.env.SMART_CONTRACT_ADDRESS! as `0x${string}`;

  console.log(contractAddress);

  const userOperationResult = await sendUserOperation({
    execute: () =>
      client.sendUserOperation({
        uo: {
          target: contractAddress,
          data: encodeFunctionData({
            abi: contract.abi,
            functionName,
            args,
          }),
        },
      }),
    watch: client.waitForUserOperationTransaction,
    replace: (res) =>
      client.dropAndReplaceUserOperation({ uoToDrop: res.request }),
  });

  switch (userOperationResult.type) {
    case "SendUserOperationSuccess": {
      return NextResponse.json(
        {
          hash: userOperationResult.hash,
        },
        {
          status: 200,
        },
      );
    }

    case "MaxReplacementsExceededException": {
      return NextResponse.json(
        {
          error: `The call to ${functionName} failed after ${userOperationResult.replacements} replacements`,
        },
        {
          status: 500,
        },
      );
    }

    case "UserOperationException": {
      const error = userOperationResult.operationError;

      if (error.name !== "HttpRequestError") {
        return NextResponse.json(
          {
            error: "An unexpected error occurred",
            errorName: error.name,
            original: error,
          },
          {
            status: 500,
          },
        );
      }

      const parsedDetailsResult = httpRequestErroDetailsStringSchema.safeParse(
        error.details,
      );

      if (!parsedDetailsResult.success) {
        console.error(`Failed to parse details of request error.`);
        console.error(error.details);
        return NextResponse.json(
          {
            error: "An unexpected error occurred getting request details",
            parseError: parsedDetailsResult.error,
            original: error.details,
          },
          {
            status: 500,
          },
        );
      }

      const {
        data: {
          data: { revertData },
        },
      } = parsedDetailsResult;

      // Attempt to decode the the error result on a best-effort basis
      try {
        const decodedError = decodeErrorResult({
          data: revertData,
          abi: contract.abi,
        });

        console.error(
          `Failed to call ${functionName}: ${decodedError.errorName}`,
        );

        return NextResponse.json(
          {
            error: decodedError.errorName,
            metaMessages: error.metaMessages,
          },
          {
            status: 400,
          },
        );
      } catch {
        console.error(
          `Failed to call ${functionName} with an unexpected error`,
        );

        return NextResponse.json(
          {
            error,
          },
          {
            status: 500,
          },
        );
      }
    }
  }
}
