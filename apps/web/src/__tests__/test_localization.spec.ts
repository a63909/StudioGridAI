/**
 * Frontend localization tests.
 * Verifies that EN and RU have identical key sets and no empty values.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import en from "../i18n/en.json";
import ru from "../i18n/ru.json";

function flattenKeys(obj: Record<string, unknown>, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([key, value]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "object" && value !== null) {
      return flattenKeys(value as Record<string, unknown>, fullKey);
    }
    return [fullKey];
  });
}

describe("Localization", () => {
  const enKeys = flattenKeys(en).sort();
  const ruKeys = flattenKeys(ru).sort();

  it("EN and RU have identical key sets", () => {
    expect(enKeys).toEqual(ruKeys);
  });

  it("no empty string values in EN", () => {
    function checkNoEmpty(obj: Record<string, unknown>, path = ""): void {
      for (const [key, value] of Object.entries(obj)) {
        const fullPath = path ? `${path}.${key}` : key;
        if (typeof value === "object" && value !== null) {
          checkNoEmpty(value as Record<string, unknown>, fullPath);
        } else if (typeof value === "string") {
          expect(value, `EN key '${fullPath}' is empty`).not.toBe("");
        }
      }
    }
    checkNoEmpty(en);
  });

  it("no empty string values in RU", () => {
    function checkNoEmpty(obj: Record<string, unknown>, path = ""): void {
      for (const [key, value] of Object.entries(obj)) {
        const fullPath = path ? `${path}.${key}` : key;
        if (typeof value === "object" && value !== null) {
          checkNoEmpty(value as Record<string, unknown>, fullPath);
        } else if (typeof value === "string") {
          expect(value, `RU key '${fullPath}' is empty`).not.toBe("");
        }
      }
    }
    checkNoEmpty(ru);
  });

  it("EN has required navigation keys", () => {
    const navKeys = enKeys.filter((k) => k.startsWith("nav."));
    expect(navKeys).toContain("nav.dashboard");
    expect(navKeys).toContain("nav.schedule");
    expect(navKeys).toContain("nav.continuity");
    expect(navKeys).toContain("nav.coverage");
    expect(navKeys).toContain("nav.report");
  });

  it("devMode.banner is defined in both locales", () => {
    expect(en.devMode?.banner).toBeDefined();
    expect(ru.devMode?.banner).toBeDefined();
    expect(en.devMode?.banner).not.toBe("");
    expect(ru.devMode?.banner).not.toBe("");
  });

  it("the complete cloud golden path is localized in EN and RU", () => {
    const cloudKeys = enKeys.filter((key) => key.startsWith("cloudDemo."));
    expect(cloudKeys.length).toBeGreaterThan(50);
    expect(en.cloudDemo.proposal.approve).toContain("human");
    expect(ru.cloudDemo.proposal.approve).toContain("человек");
    expect(en.cloudDemo.evidence.description).toContain("chain-of-thought");
    expect(ru.cloudDemo.evidence.description).toContain("цепочка рассуждений");
  });

  it("keeps English as the deterministic public default", () => {
    const proxy = readFileSync(join(process.cwd(), "src/proxy.ts"), "utf8");
    expect(proxy).toContain("defaultLocale");
    expect(proxy).toContain("localeDetection: false");
  });
});
