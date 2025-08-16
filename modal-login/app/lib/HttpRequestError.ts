import { z } from "zod";

/**
  * HttpRequestErrorType from viem includes a details property. Its format is
  * not guaranteed but in practice it contains a stringified JSON with 
  * a `revertData` hex string that is useful for debugging. The runtime schemas
  * below parse a string into a JSON object matching the observed shape
  * of the details object.
  *
  * Call `safeParse` on the schemas to check at runtime if the `revertData` is
  * available for decoding and fallback gracefully if not present.
  */
const httpRequestErrorDetailsSchema = z.object({
  code: z.number(),
  message: z.string(),
  data: z.object({
    revertData: z.custom<`0x${string}`>(
      (val) => typeof val === 'string' && /^0x[0-9A-Fa-f]{8}$/.test(val)
    )
  })
})

const literalSchema = z.union([z.string(), z.number(), z.boolean(), z.null()]);
type Literal = z.infer<typeof literalSchema>;
type Json = Literal | { [key: string]: Json } | Json[];
const jsonSchema: z.ZodType<Json> = z.lazy(() =>
  z.union([literalSchema, z.array(jsonSchema), z.record(jsonSchema)])
);

const stringToJSONSchema = z.string()
    .transform((str, ctx): z.infer<typeof jsonSchema> => {
        try {
            return JSON.parse(str)
        } catch (e) {
            ctx.addIssue({ code: 'custom', message: 'Invalid JSON' })
            return z.NEVER
        }
    })

export const httpRequestErroDetailsStringSchema = stringToJSONSchema.pipe(httpRequestErrorDetailsSchema)
