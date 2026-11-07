import type { Roommate } from "../api/client.ts";

export const neighborhoods = [
  "Williamsburg",
  "Greenpoint",
  "Bushwick",
  "Astoria",
];
export const lifestyleFilters = [
  { key: "non_smoker", label: "Non-smoker" },
  { key: "quiet", label: "Quiet on weeknights" },
  { key: "early", label: "Early riser" },
  { key: "pets", label: "Pet-friendly" },
];
export const lifestyleLabels: Record<string, Record<string, string>> = {
  sleep_schedule: {
    early: "Early riser",
    late: "Night owl",
    flexible: "Flexible routine",
  },
  cleanliness: {
    relaxed: "Relaxed",
    mostly_relaxed: "Mostly relaxed",
    moderately_tidy: "Moderately tidy",
    tidy: "Tidy",
    very_tidy: "Very tidy",
  },
  smoking: {
    non_smoker: "Non-smoker",
    smoker: "Smoker",
    outside_only: "Smokes outside only",
    any: "No smoking preference",
  },
  pets: {
    no_pets: "No pets",
    has_pets: "Has pets",
    okay_with_pets: "Pet-friendly",
  },
  noise: {
    "1": "Very quiet home",
    "2": "Quiet on weeknights",
    "3": "Some background noise",
    "4": "Lively home",
    "5": "Very lively home",
  },
  guests: {
    rarely: "Rare visitors",
    sometimes: "Occasional visitors",
    often: "Frequent visitors",
  },
  roommate_dynamic: {
    independent: "Independent",
    friendly: "Friendly, with personal space",
    close_friends: "Hoping to become friends",
  },
};

/** Translate stored preference choices into readable profile details. */
export function lifestyleLabel(key: string, value: string | null | undefined) {
  return value ? lifestyleLabels[key]?.[value] || "Not added" : "Not added";
}

/** Format a date-only value without shifting it across time zones. */
export function moveInLabel(value: string | null | undefined) {
  return value
    ? new Date(`${value}T12:00:00`).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "Flexible move-in";
}

/** Format the roommate's monthly share of rent. */
export function budgetLabel(roommate: Roommate) {
  const housing = roommate.housing;
  if (housing?.budget_min == null || housing.budget_max == null)
    return "Budget not added";
  return `$${Number(housing.budget_min).toLocaleString("en-US")}–$${Number(housing.budget_max).toLocaleString("en-US")}`;
}

/** Read only supported filter values from shareable discovery URLs. */
export function readFilters(params: URLSearchParams) {
  const amount = Number(params.get("budget"));
  const date = params.get("date") || "";
  const sort = params.get("sort") || "default";
  return {
    areas: [
      ...new Set(
        params.getAll("area").filter((area) => neighborhoods.includes(area)),
      ),
    ],
    budget: amount >= 1000 && amount <= 2500 ? amount : 2500,
    date: ["2027-01-15", "2027-02-01", "2027-02-15"].includes(date) ? date : "",
    lifestyle: [
      ...new Set(
        params
          .getAll("lifestyle")
          .filter((key) =>
            lifestyleFilters.some((filter) => filter.key === key),
          ),
      ),
    ],
    sort: ["name", "budget", "move"].includes(sort) ? sort : "default",
  };
}

/** Apply explicit browsing filters without assigning compatibility or rank. */
export function filterRoommates(
  roommates: Roommate[],
  params: URLSearchParams,
) {
  const filters = readFilters(params);
  const results = roommates.filter((roommate) => {
    const housing = roommate.housing;
    const answers = roommate.lifestyle;
    if (
      filters.areas.length &&
      !filters.areas.includes(housing?.neighborhood || "")
    )
      return false;
    // A candidate fits the cap if some part of their stated rent range fits it.
    if (
      filters.budget < 2500 &&
      (housing?.budget_min == null ||
        Number(housing.budget_min) > filters.budget)
    )
      return false;
    if (
      filters.date &&
      (!housing?.move_in_date || housing.move_in_date > filters.date)
    )
      return false;
    return filters.lifestyle.every((key) => {
      if (key === "non_smoker") return answers.smoking === "non_smoker";
      if (key === "quiet") return ["1", "2"].includes(answers.noise || "");
      if (key === "early") return answers.sleep_schedule === "early";
      return ["has_pets", "okay_with_pets"].includes(answers.pets || "");
    });
  });
  if (filters.sort === "name")
    results.sort((a, b) => a.full_name.localeCompare(b.full_name));
  if (filters.sort === "budget")
    results.sort(
      (a, b) =>
        Number(a.housing?.budget_min ?? Infinity) -
        Number(b.housing?.budget_min ?? Infinity),
    );
  if (filters.sort === "move")
    results.sort((a, b) =>
      (a.housing?.move_in_date || "9999").localeCompare(
        b.housing?.move_in_date || "9999",
      ),
    );
  return results;
}
