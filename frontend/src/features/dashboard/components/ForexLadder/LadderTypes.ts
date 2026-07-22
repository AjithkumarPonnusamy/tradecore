/**
 * Shared types for the Institutional Liquidity Map & Market Depth Ladder.
 */

export type LevelType =
  | "R5"
  | "R4"
  | "R3"
  | "TC"
  | "P"
  | "PIVOT"
  | "BC"
  | "S3"
  | "S4"
  | "S5"
  | "r5"
  | "r4"
  | "r3"
  | "tc"
  | "pivot"
  | "bc"
  | "s3"
  | "s4"
  | "s5";

export interface PriceLevel {
  label: string;
  name: string;
  price: number;
  type: string;
  description: string;
  probability?: string;
  reactionNote?: string;
  signalZone?: string;
  isCpr?: boolean;
}

export interface ForexPair {
  symbol: string;
  name: string;
  dec: number;
  label?: string;
}

export interface LadderData {
  symbol: string;
  ltp: number;
  bid: number;
  ask: number;
  spread: number;
  atr?: number;
  session?: string;
  source: string;
  dec: number;
  pivot: number;
  tc: number;
  bc: number;
  levels: PriceLevel[];
}
