// Basic mock database implementation that simplify reads and writes from json files.
// Should be replaced by a real database.

import fs from "fs";
import path from "path";
import { z, ZodSchema } from "zod";
import { hexSchema } from "./lib/schemas";
import { Hex } from "viem";

const userDataPath = path.join(process.cwd(), "./temp-data/userData.json");
const apiKeyPath = path.join(process.cwd(), "./temp-data/userApiKey.json");

function readJson<T extends ZodSchema>(
  filePath: string,
  schema: T,
): z.infer<T> {
  if (!fs.existsSync(filePath)) {
    return {};
  }
  const fileData = fs.readFileSync(filePath, "utf-8");
  const raw = JSON.parse(fileData);

  return schema.parse(raw);
}

const writeJson = (filePath: string, data: ApiKeyRecord | UserDataRecord) => {
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
};

const userDataSchema = z.object({
  orgId: z.string(),
  address: z.string(),
  userId: z.string(),
  email: z.optional(z.string()),
});
const userDataRecordSchema = z.record(userDataSchema);

export type UserData = z.infer<typeof userDataSchema>;
type UserDataRecord = z.infer<typeof userDataRecordSchema>;

export const userApiKeySchema = z.discriminatedUnion("activated", [
  z.object({
    publicKey: hexSchema,
    privateKey: hexSchema,
    createdAt: z.coerce.date(),
    deferredActionDigest: hexSchema,
    accountAddress: hexSchema,
    initCode: hexSchema,
    activated: z.literal(true),
  }),
  z.object({
    publicKey: hexSchema,
    privateKey: hexSchema,
    createdAt: z.coerce.date(),
    activated: z.literal(false),
  }),
]);
export const apiKeyRecordSchema = z.record(z.array(userApiKeySchema));

export type UserApiKey = z.infer<typeof userApiKeySchema>;
type ApiKeyRecord = z.infer<typeof apiKeyRecordSchema>;

/**
 * Upsert a user's data and their API key. Removes all other users
 * from the database file to avoid any potential conflicts when
 * it's read by another process.
 *
 * Reads the current database from disk, updates the data,
 * and writes the new state back to disk.
 */
export const upsertUser = (data: UserData, apiKey: UserApiKey) => {
  // Read from disk.
  const usersData = readJson(userDataPath, userDataRecordSchema);
  const apiKeyData = readJson(apiKeyPath, apiKeyRecordSchema);

  // Update data.
  usersData[data.orgId] = data;
  const existingKeys = apiKeyData[data.orgId] || [];
  apiKeyData[data.orgId] = [...existingKeys, apiKey];

  // Remove any users other than the current user.
  Object.keys(usersData).forEach((key) => {
    if (key !== data.orgId) {
      delete usersData[key];
    }
  });

  // Write back to disk.
  writeJson(userDataPath, usersData);
  writeJson(apiKeyPath, apiKeyData);
};

/**
 * Retrieve user data for a given organization id.
 */
export const getUser = (orgId: string): UserData | null => {
  const userData = readJson(userDataPath, userDataRecordSchema);
  return userData[orgId] ?? null;
};

/**
 * Get the latest API key for a given organization id.
 */
export const getLatestApiKey = (orgId: string): UserApiKey | null => {
  const apiKeyData = readJson(apiKeyPath, apiKeyRecordSchema);
  const keys: UserApiKey[] = apiKeyData[orgId];
  return keys?.[keys.length - 1] ?? null;
};

export const setApiKeyActivated = (
  orgId: string,
  apiKey: Hex,
  deferredActionDigest: Hex,
  accountAddress: Hex,
  initCode: Hex,
): void => {
  const apiKeyData = readJson(apiKeyPath, apiKeyRecordSchema);
  const keys = apiKeyData[orgId];
  const key = keys.find((k) => k.publicKey === apiKey);
  if (!key) {
    throw new Error("API key not found");
  }
  const updatedData: ApiKeyRecord = {
    ...apiKeyData,
    [orgId]: keys.map((k) =>
      k.publicKey === apiKey
        ? {
            ...k,
            activated: true,
            deferredActionDigest,
            accountAddress,
            initCode,
          }
        : k,
    ),
  };
  writeJson(apiKeyPath, updatedData);
};