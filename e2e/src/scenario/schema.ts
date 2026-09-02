import { z } from 'zod';

const UrlType = z.enum(['auto', 'regular', 'zeronet']);

export const ScrapeSourceSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  url: z.string().url(),
  /** URL the containerised app should use instead (docker network names). */
  dockerUrl: z.string().url().optional(),
  /** Public-gateway alternative used when the primary URL cannot be reached. */
  fallbackUrl: z.string().url().optional(),
  urlType: UrlType.default('auto'),
  expectMinChannels: z.number().int().nonnegative().default(1),
  scrapeTimeoutMs: z.number().int().positive().default(180_000),
});

export const SearchQuerySchema = z.object({
  query: z.string().min(1),
  category: z.string().optional(),
  expectMinResults: z.number().int().nonnegative().default(1),
  /** How many of the returned rows to add as channels through the UI. */
  addFirst: z.number().int().nonnegative().default(1),
});

export const EpgSourceSchema = z.object({
  name: z.string().min(1),
  url: z.string().url(),
  expectMinChannels: z.number().int().nonnegative().default(1),
  refreshTimeoutMs: z.number().int().positive().default(600_000),
});

export const TvChannelSchema = z.object({
  name: z.string().min(1),
  category: z.string().optional(),
  /** Engine search query used to find a stream to attach. */
  streamSearchQuery: z.string().min(1),
  /** EPG channel (xml id) to map to this TV channel. */
  epgXmlId: z.string().min(1).optional(),
});

export const ScenarioSchema = z.object({
  name: z.string().min(1),
  description: z.string().default(''),
  stack: z.object({
    engineUrl: z.string().url(),
    acexyUrl: z.string().url(),
    ipfsGateway: z.string().url().optional(),
  }),
  scrape: z.object({ sources: z.array(ScrapeSourceSchema).min(1) }),
  search: z.object({ queries: z.array(SearchQuerySchema).min(1) }),
  epg: z.object({
    sources: z.array(EpgSourceSchema).min(1),
    targetChannel: z.object({
      xmlId: z.string().min(1),
      displayNameContains: z.string().min(1),
    }),
  }),
  tv: z.object({ channels: z.array(TvChannelSchema).min(1) }),
  playlist: z.object({
    baseUrlName: z.string().min(1),
    baseUrlPattern: z.string().min(1),
  }),
  errors: z
    .object({
      allowedApiErrorPatterns: z.array(z.string()).default([]),
      allowedConsolePatterns: z.array(z.string()).default([]),
    })
    .default({ allowedApiErrorPatterns: [], allowedConsolePatterns: [] }),
});

export type Scenario = z.infer<typeof ScenarioSchema>;
export type ScrapeSource = z.infer<typeof ScrapeSourceSchema>;
export type SearchQuery = z.infer<typeof SearchQuerySchema>;
export type EpgSource = z.infer<typeof EpgSourceSchema>;
export type TvChannelSpec = z.infer<typeof TvChannelSchema>;
