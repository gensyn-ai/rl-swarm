"use client";
import {
  useAuthModal,
  useLogout,
  useSigner,
  useSignerStatus,
  useUser,
} from "@account-kit/react";
import { useCallback, useEffect, useState } from "react";

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

      const { publicKey } = await resp.json() || {};
      if (!publicKey) {
        console.log("No public key");
        return;
      }

      await signer?.inner.experimental_createApiKey({
        name: `server-signer-${new Date().getTime()}`,
        publicKey,
        expirationSec: 60 * 60 * 24 * 62, // 62 days
      });

      await fetch("/api/set-api-key-activated", {
        method: "POST",
        body: JSON.stringify({ orgId: user.orgId, apiKey: publicKey }),
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

  useEffect(() => {
  if (!user && !signerStatus.isInitializing) {
    openAuthModal(); 
  }
}, [user, signerStatus.isInitializing]);

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
