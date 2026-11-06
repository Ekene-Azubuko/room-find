import test from "node:test";
import assert from "node:assert/strict";
import { filterRoommates, readFilters } from "../src/pages/discovery.ts";
import type { Roommate } from "../src/api/client.ts";

const roommates: Roommate[] = [
  {
    id: 1,
    full_name: "Maya",
    housing: {
      neighborhood: "Williamsburg",
      budget_min: "1600",
      move_in_date: "2027-01-01",
    },
    lifestyle: {
      smoking: "non_smoker",
      noise: "2",
      sleep_schedule: "early",
      pets: "no_pets",
    },
  },
  {
    id: 2,
    full_name: "Jordan",
    housing: {
      neighborhood: "Greenpoint",
      budget_min: "1700",
      move_in_date: "2027-01-15",
    },
    lifestyle: {
      smoking: "non_smoker",
      noise: "1",
      sleep_schedule: "late",
      pets: "has_pets",
    },
  },
  {
    id: 3,
    full_name: "Priya",
    housing: {
      neighborhood: "Bushwick",
      budget_min: "1300",
      move_in_date: "2027-02-01",
    },
    lifestyle: {
      smoking: "non_smoker",
      noise: "3",
      sleep_schedule: "flexible",
      pets: "okay_with_pets",
    },
  },
  {
    id: 4,
    full_name: "Elena",
    housing: {
      neighborhood: "Astoria",
      budget_min: "1400",
      move_in_date: "2027-02-15",
    },
    lifestyle: {
      smoking: "outside_only",
      noise: "2",
      sleep_schedule: "early",
      pets: "no_pets",
    },
  },
].map((roommate) => ({
  ...roommate,
  age: 25,
  occupation: "Demo occupation",
  life_stage: "Young professional",
  bio: "Demo biography",
  photo_url: "/images/maya.jpg",
  is_demo: true,
  housing: {
    city: "Brooklyn",
    budget_max: "2100",
    lease_months: 12,
    ...roommate.housing,
  },
}));

/** Return visible IDs for a browser filter query. */
function ids(query = "") {
  return filterRoommates(roommates, new URLSearchParams(query)).map(
    (person) => person.id,
  );
}

test("all four roommates appear by default and after resetting", () => {
  assert.deepEqual(ids(), [1, 2, 3, 4]);
  assert.deepEqual(ids("area=Williamsburg&area=Greenpoint"), [1, 2]);
  assert.deepEqual(ids(), [1, 2, 3, 4]);
});

test("filters combine across groups and include exact budget/date boundaries", () => {
  assert.deepEqual(ids("budget=1600"), [1, 3, 4]);
  assert.deepEqual(ids("date=2027-01-15"), [1, 2]);
  assert.deepEqual(
    ids("lifestyle=non_smoker&lifestyle=quiet&lifestyle=early"),
    [1],
  );
  assert.deepEqual(ids("lifestyle=pets"), [2, 3]);
  assert.deepEqual(ids("area=Astoria&lifestyle=non_smoker"), []);
});

test("sorting is explicit and never mutates the server order", () => {
  assert.deepEqual(ids("sort=budget"), [3, 4, 1, 2]);
  assert.deepEqual(ids("sort=name"), [4, 2, 1, 3]);
  assert.deepEqual(ids("sort=move"), [1, 2, 3, 4]);
  assert.deepEqual(ids(), [1, 2, 3, 4]);
});

test("invalid URL values cannot silently hide all results or duplicate active chips", () => {
  assert.deepEqual(
    ids("budget=bad&date=oops&area=unknown&lifestyle=unknown&sort=score"),
    [1, 2, 3, 4],
  );
  const filters = readFilters(new URLSearchParams("area=Astoria&area=Astoria"));
  assert.deepEqual(filters.areas, ["Astoria"]);
});
