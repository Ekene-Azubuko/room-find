import type { Housing } from "../../api/client";

export const steps = ["Your profile", "Housing", "Lifestyle", "Review"];
export const titles = [
  "First, tell us about yourself",
  "What kind of home are you looking for?",
  "Now, let’s talk lifestyle",
  "Review your preferences",
];
export const descriptions = [
  "Help potential roommates get to know the person behind the profile.",
  "Set your housing needs. You can always fine-tune these later.",
  "There are no right answers—honesty makes for better matches.",
  "Make sure everything looks right before we find your matches.",
];
export const cleanlinessValues = [
  "relaxed",
  "mostly_relaxed",
  "moderately_tidy",
  "tidy",
  "very_tidy",
];
export const cleanlinessLabels = [
  "1. Relaxed: Some clutter and less frequent cleaning are acceptable.",
  "2. Mostly relaxed: Occasional clutter is fine, with periodic cleaning.",
  "3. Moderate: Shared spaces are cleaned regularly, with some clutter acceptable.",
  "4. Tidy: Shared spaces are usually tidy, with mess cleaned up promptly.",
  "5. Very tidy: Shared spaces are kept tidy daily, with mess cleaned up immediately.",
];
export const noiseLabels = [
  "Very quiet",
  "Quiet on weeknights",
  "A little of both",
  "Sociable",
  "Lively",
];
export const sleepOptions: [string, string][] = [
  ["early", "Early riser"],
  ["flexible", "Flexible"],
  ["late", "Night owl"],
];
export const dynamicOptions: [string, string][] = [
  ["independent", "Mostly independent"],
  ["friendly", "Friendly, with personal space"],
  ["close_friends", "Close friends"],
];
export const initialHousing: Housing = {
  city: "",
  neighborhood: "",
  budget_min: "",
  budget_max: "",
  move_in_date: "",
  lease_months: 12,
  city_is_requirement: false,
  neighborhood_is_requirement: false,
  budget_is_requirement: false,
  move_in_is_requirement: false,
  lease_is_requirement: false,
};
export const initialChoices = {
  cleanliness: "",
  noise: "",
  sleep_schedule: "",
  pets: "",
  roommate_dynamic: "",
  smoking: "",
  daytime_visitors: "",
  overnight_guests: "",
};
export type Question = keyof typeof initialChoices;
export type Detail = {
  label: string;
  value: string;
  required: boolean;
  step: number;
};

export type ProfileDraft = {
  full_name: string;
  age: string;
  life_stage: string;
  occupation: string;
  bio: string;
};
export type UpdateHousing = <K extends keyof Housing>(
  key: K,
  value: Housing[K],
) => void;
export type UpdateChoice = (key: Question, value: string) => void;
export type UpdateRequirement = (key: Question, value: boolean) => void;

/** Describe a frequency using an explicit weekly unit. */
export function frequencyOptions(
  unit: string,
  maximum = false,
): [string, string][] {
  if (maximum)
    return [
      ["never", `No ${unit} per week (never)`],
      ["less_than_weekly", "Less than once a week"],
      ["1_2", `Up to 2 ${unit} per week`],
      ["3_4", `Up to 4 ${unit} per week`],
      ["5_7", `Up to 7 ${unit} per week`],
    ];
  return [
    ["never", "Never"],
    ["less_than_weekly", "Less than once a week"],
    ["1_2", `1–2 ${unit} a week`],
    ["3_4", `3–4 ${unit} a week`],
    ["5_7", `5–7 ${unit} a week`],
  ];
}
export const questionTitles: Record<Question, string> = {
  cleanliness: "How do you usually keep shared spaces?",
  noise: "Noise at home",
  sleep_schedule: "Your usual sleep schedule",
  roommate_dynamic: "Roommate dynamic",
  pets: "Do you have pets?",
  smoking: "Do you smoke?",
  daytime_visitors: "How often do you have daytime visitors?",
  overnight_guests: "How often do you have overnight guests?",
};
/** Supply distinct personal facts and acceptable roommate choices. */
export function questionOptions(
  key: Question,
  expectation = false,
): [string, string][] {
  let options: [string, string][];
  if (key === "cleanliness")
    options = cleanlinessValues.map((value, i) => [
      value,
      cleanlinessLabels[i],
    ]);
  else if (key === "pets")
    options = expectation
      ? [["no_pets", "No, no roommate pets"]]
      : [
          ["has_pets", "Yes, I have pets"],
          ["no_pets", "No, I do not have pets"],
        ];
  else if (key === "smoking")
    options = expectation
      ? [
          ["non_smoker", "No, a non-smoking roommate"],
          ["outside_only", "Only if they smoke outside"],
        ]
      : [
          ["non_smoker", "No, I do not smoke"],
          ["smoker", "Yes, I smoke"],
          ["outside_only", "Yes, outside only"],
        ];
  else if (key === "daytime_visitors" || key === "overnight_guests")
    options = frequencyOptions(
      key === "daytime_visitors" ? "days" : "nights",
      expectation,
    );
  else if (key === "sleep_schedule") options = sleepOptions;
  else if (key === "noise")
    options = noiseLabels.map((label, i) => [String(i + 1), label]);
  else options = dynamicOptions;
  return expectation
    ? [
        ...options,
        [
          "no_preference",
          ["pets", "smoking"].includes(key)
            ? "Yes, comfortable either way"
            : "No preference",
        ],
      ]
    : options;
}
/** Label an answer without interpreting missing data as agreement. */
export function answerLabel(
  key: Question,
  value: string | null | undefined,
  expectation = false,
) {
  return (
    questionOptions(key, expectation).find(
      ([option]) => option === value,
    )?.[1] || "Not provided"
  );
}
