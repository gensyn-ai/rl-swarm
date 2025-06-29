import z from "zod";

export const hexSchema = z.custom<`0x${string}`>(
  (val) => typeof val === "string" && /^0x[0-9A-Fa-f]*$/.test(val),
);
