"use client";
import {
  alchemy,
  createAlchemySmartAccountClient,
  gensynTestnet,
} from "@account-kit/infra";
import {
  useAuthModal,
  useLogout,
  useSigner,
  useSignerStatus,
  useUser,
} from "@account-kit/react";
import {
  createModularAccountV2,
  createModularAccountV2Client,
} from "@account-kit/smart-contracts";
import {
  buildDeferredActionDigest,
  PermissionType,
} from "@account-kit/smart-contracts/experimental";
import {
  deferralActions,
  installValidationActions,
  PermissionBuilder,
} from "@account-kit/smart-contracts/experimental";
import { useCallback, useEffect, useState } from "react";

const DAY_IN_MILLISECONDS = 1000 * 60 * 60 * 24;

export default function Home() {
  const user = useUser();
  const { openAuthModal } = useAuthModal();
  const signerStatus = useSignerStatus();
  const { logout } = useLogout();
  const signer = useSigner();

  const [createdApiKey, setCreatedApiKey] = useState(false);
  const [sawDisconnected, setSawDisconnected] = useState(false);
  const [sawConnected, setSawConnected] = useState(false);

  // For some reason, the signer status jumps from disconnected to initializing,
  // which makes keeping track of the status here tricky.
  // Record that we ever saw a disconnected or connected status and make decisions on that.
  useEffect(() => {
    if (signerStatus.status === "DISCONNECTED") {
      setSawDisconnected(true);
    }
    if (signerStatus.status === "CONNECTED") {
      setSawConnected(true);
    }
  }, [signerStatus.status]);

  const handleAll = useCallback(async () => {
    if (!user || !signer) {
      console.log("handleAll: no user or signer");
      return;
    }

    try {
      const whoamiStamp = await signer?.inner.stampWhoami();
      if (!whoamiStamp) {
        console.log("No whoami stamp");
        return;
      }

      const resp = await fetch("/api/get-api-key", {
        method: "POST",
        body: JSON.stringify({ whoamiStamp }),
      });

      const { publicKey } = (await resp.json()) || {};
      if (!publicKey) {
        console.log("No public key");
        return;
      }

      const transport = alchemy({
        apiKey: process.env.NEXT_PUBLIC_ALCHEMY_API_KEY!,
      });

      const account = await createModularAccountV2({
        transport,
        chain: gensynTestnet,
        signer,
      });

      const initCode = await account.getInitCode();

      const client = (
        await createModularAccountV2Client({
          signer,
          signerEntity: account.signerEntity,
          accountAddress: account.address,
          transport,
          chain: gensynTestnet,
        })
      )
        .extend(installValidationActions)
        .extend(deferralActions);

      const { entityId, nonce } = await client.getEntityIdAndNonce({
        // This must be true for the ROOT permission
        isGlobalValidation: true,
      });

      const { typedData, fullPreSignatureDeferredActionDigest } =
        await new PermissionBuilder({
          client,
          key: {
            publicKey,
            type: "secp256k1",
          },
          entityId,
          nonce,
          deadline: 62 * DAY_IN_MILLISECONDS,
        })
          .addPermission({
            permission: {
              type: PermissionType.ROOT,
            },
          })
          .compileDeferred();

      const deferredValidationSig =
        await client.account.signTypedData(typedData);

      const deferredActionDigest = buildDeferredActionDigest({
        fullPreSignatureDeferredActionDigest,
        sig: deferredValidationSig,
      });

      await fetch("/api/set-api-key-activated", {
        method: "POST",
        body: JSON.stringify({
          orgId: user.orgId,
          apiKey: publicKey,
          accountAddress: account.address,
          initCode,
          deferredActionDigest,
        }),
      });

      setCreatedApiKey(true);
    } catch (err) {
      console.error(err);
      window.alert("Error logging in. See console for details.");
    }
  }, [signer, user]);

  useEffect(() => {
    if (sawConnected) {
      handleAll();
    }
  }, [handleAll, sawConnected]);

  // Show alert if crypto.subtle isn't available.
  useEffect(() => {
    if (typeof window === undefined) {
      return;
    }
    try {
      if (typeof window.crypto.subtle !== "object") {
        throw new Error("window.crypto.subtle is not available");
      }
    } catch (err) {
      alert(
        "Crypto api is not available in browser. Please be sure that the app is being accessed via localhost or a secure connection.",
      );
    }
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center gap-4 justify-center text-center">
      {(!sawDisconnected && !sawConnected) || (user && !createdApiKey) ? (
        <>Loading...</>
      ) : user ? (
        <div className="card">
          <div className="flex flex-col gap-2 p-2">
            <p className="text-xl font-bold">
              YOU ARE SUCCESSFULLY LOGGED IN TO THE GENSYN TESTNET
            </p>
            <button className="btn btn-primary mt-6" onClick={() => logout()}>
              Log out
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          <p className="text-xl font-bold">LOGIN TO THE GENSYN TESTNET</p>
          <div className="flex flex-col gap-2 p-2">
            <button className="btn btn-primary mt-6" onClick={openAuthModal}>
              Login
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
