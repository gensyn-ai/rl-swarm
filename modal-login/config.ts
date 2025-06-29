import {
  AlchemyAccountsUIConfig,
  cookieStorage,
  createConfig,
} from "@account-kit/react";
import { alchemy, sepolia } from "@account-kit/infra";
import { QueryClient } from "@tanstack/react-query";


const uiConfig: AlchemyAccountsUIConfig = {
  illustrationStyle: "outline",
  auth: {
    sections: [
      [{ type: "email" }],
      [
        { type: "passkey" },
        { type: "social", authProviderId: "google", mode: "popup" },
        { type: "social", authProviderId: "facebook", mode: "popup" },
      ],
    ],
    addPasskeyOnSignup: false,
    //header: <img src="logo.png"/>,
  },
};

export const config = createConfig(
  {
    transport: alchemy({ apiKey: process.env.NEXT_PUBLIC_ALCHEMY_API_KEY! }),
    chain: sepolia,
    ssr: true, // more about ssr: https://accountkit.alchemy.com/react/ssr
    //storage: cookieStorage, // more about persisting state with cookies: https://accountkit.alchemy.com/react/ssr#persisting-the-account-state
    enablePopupOauth: true, // must be set to "true" if you plan on using popup rather than redirect in the social login flow
    sessionConfig: {
      // If using sever-side signing, ideally this duration is <= the MIN_KEY_DURATION_REMAINING_MS defined on the server.
      expirationTimeMs: 1000 * 60 * 60 * 24 * 30, // 7 days
    },
  },
  uiConfig,
);

export const queryClient = new QueryClient();
