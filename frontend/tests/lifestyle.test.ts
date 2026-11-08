import test from "node:test";
import assert from "node:assert/strict";
import {
  answerLabel,
  questionOptions,
  initialChoices,
} from "../src/pages/setup/options.ts";
import { lifestyleLabel } from "../src/pages/discovery.ts";

test("unanswered habits remain unknown instead of sample defaults", () => {
  assert.ok(Object.values(initialChoices).every((value) => value === ""));
  for (const key of [
    "pets",
    "smoking",
    "daytime_visitors",
    "overnight_guests",
  ] as const) {
    assert.equal(answerLabel(key, null), "Not provided");
    assert.equal(answerLabel(key, undefined, true), "Not provided");
  }
});

test("comfortable pet and smoking choices never request those habits", () => {
  assert.deepEqual(
    questionOptions("pets", true).map(([key]) => key),
    ["no_pets", "no_preference"],
  );
  assert.ok(
    !questionOptions("smoking", true).some(([key]) => key === "smoker"),
  );
  assert.equal(answerLabel("pets", "okay_with_pets"), "Not provided");
});

test("guest expectations state a maximum using the correct unit", () => {
  assert.equal(
    answerLabel("daytime_visitors", "1_2", true),
    "Up to 2 days per week",
  );
  assert.equal(
    answerLabel("overnight_guests", "3_4", true),
    "Up to 4 nights per week",
  );
  assert.equal(
    answerLabel("overnight_guests", "no_preference", true),
    "No preference",
  );
});

test("detailed cleanliness labels match review while discovery stays concise", () => {
  assert.equal(
    lifestyleLabel("cleanliness", "tidy", true),
    answerLabel("cleanliness", "tidy"),
  );
  assert.equal(lifestyleLabel("cleanliness", "tidy"), "Tidy");
});
