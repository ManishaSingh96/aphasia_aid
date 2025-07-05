import { describe, it, expect } from "vitest";
import { sum } from "../src/lib/sum";

describe("sum", () => {
  it("should add two numbers correctly", () => {
    expect(sum(1, 2)).toBe(3);
    expect(sum(0, 0)).toBe(0);
    expect(sum(-1, 1)).toBe(0);
    expect(sum(10, -5)).toBe(5);
  });
});
