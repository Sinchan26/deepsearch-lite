import { describe, expect, it } from "vitest";
import fixtures from "../../../contracts/public-events.fixture.json";
import { parsePublicEvent } from "./validate";

describe("F04 public protocol", () => {
  it("accepts every event variant validated by Pydantic", () => {
    for (const fixture of fixtures) expect(parsePublicEvent(fixture)).toEqual(fixture);
  });
  it("rejects unknown versions, event kinds, private fields and mismatched payloads", () => {
    const base = fixtures[0];
    for (const bad of [{ ...base, schema_version: 2 }, { ...base, type: "reasoning" },
      { ...base, private_reasoning: "hidden" }, { ...base, payload: { prompt: "secret" } },
      { ...base, seq: 0 }]) expect(() => parsePublicEvent(bad)).toThrow();
  });
});
