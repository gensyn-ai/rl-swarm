import { UserOperationRequest } from "@aa-sdk/core";
import { Hex } from "viem";
import { SendUserOperationErrorType } from "viem/account-abstraction";

type SendUserOperationResult =
  | SendUserOperationSuccess
  | MaxReplacementsExceededException
  | UserOperationException;

const MAX_USER_OPERATIONS_REPLACEMENTS = 2;

type BaseOperationResult = { hash: Hex; request: UserOperationRequest };

type SendUserOperationParams<Res extends BaseOperationResult> = {
  /**
   * Callback to execute the initial user operation. On a failure
   * it is expected to return viem's `SendUserOperationErrorType`.
   */
  execute: () => Promise<Res>;
  /**
   * Callback to watch the chain for the result of the user operation
   * that was sent by `execute`. It is passed `execute`'s resolved return value.
   */
  watch: (res: Res) => Promise<Hex>;
  /**
   * Callback to replace the initial user operation in the event it gets stuck
   * in the bundler. It is passed `request` property from `execute`'s resolved
   * return value.
   */
  replace: (res: Res) => Promise<Res>;
};

/**
 * `sendUserOperation` is a wrapper function to "retry" user operations. If the
 * gas price is fluctuating, a user operation may not get mined in a reasonable
 * amount of time if its initial gas price is too low. This can cause further
 * issues later on if another user operation is sent while the first is still
 * pending: both user operations will have the same nonce and the later
 * transaction will be interpreted as a replacement of the other.
 *
 * `sendUserOperation` will send the user operation to the chain and watch
 * for its inclusion in a block. If watching times out, it will be replace
 * with the `replace` callback 2 times before failing with
 * `MaxReplacementsExceededException`
 *
 * @example
 * ```
 *  const userOperationResult = await sendUserOperation({
 *    execute: () =>
 *      client.sendUserOperation({
 *        uo: {
 *          target: contractAdrr,
 *          data: encodeFunctionData({
 *            abi: contract.abi,
 *            functionName: "registerPeer",
 *            args: [body.peerId],
 *          }),
 *        },
 *      }),
 *    watch: client.waitForUserOperationTransaction,
 *    replace: (res) =>
 *      client.dropAndReplaceUserOperation({ uoToDrop: res.request }),
 *  });
 *
 *  switch (userOperationResult.type) {
 *    case "SendUserOperationSuccess": {
 *      // Handle success.
 *    }
 *
 *    case "MaxReplacementsExceededException": {
 *      // Handle max replacements.
 *    }
 *
 *    case "UserOperationException": {
 *      // Handle failures with the user operation itself.
 *    }
 * ```
 */
export async function sendUserOperation<Res extends BaseOperationResult>({
  execute,
  watch,
  replace,
}: SendUserOperationParams<Res>): Promise<SendUserOperationResult> {
  let futureResult = execute();

  for (let i = 0; i < MAX_USER_OPERATIONS_REPLACEMENTS; i++) {
    try {
      const res = await futureResult;

      try {
        await watch(res);
        return { type: "SendUserOperationSuccess", hash: res.hash };
      } catch (watchErr) {
        console.warn(
          "Failed to find transaction on chain, replacing user operation. Failed due to the following:",
        );
        console.warn(watchErr);
        futureResult = replace(res);
        continue;
      }
    } catch (err) {
      // Casting is not ideal but is canonical way of handling errors as per the
      // viem docs.
      //
      // See: https://viem.sh/docs/error-handling#error-handling
      return UserOperationException.of(err as SendUserOperationErrorType);
    }
  }

  return MaxReplacementsExceededException.of();
}

type SendUserOperationSuccess = {
  type: "SendUserOperationSuccess";
  hash: Hex;
};

class UserOperationException extends Error {
  readonly type = "UserOperationException";
  private constructor(readonly operationError: SendUserOperationErrorType) {
    super(
      `Failed to send user operation with the following reason: ${operationError.name}`,
    );
  }

  static of(operationError: SendUserOperationErrorType) {
    return new UserOperationException(operationError);
  }
}

class MaxReplacementsExceededException extends Error {
  readonly type = "MaxReplacementsExceededException";
  readonly replacements = MAX_USER_OPERATIONS_REPLACEMENTS;
  private constructor() {
    super(
      `Failed to send user operation after attempting ${MAX_USER_OPERATIONS_REPLACEMENTS} replacements`,
    );
  }

  static of() {
    return new MaxReplacementsExceededException();
  }
}
