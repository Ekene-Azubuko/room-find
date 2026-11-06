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
  "Relaxed",
  "Mostly relaxed",
  "Moderately tidy",
  "Tidy, but not perfect",
  "Very tidy",
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
export const petOptions: [string, string][] = [
  ["okay_with_pets", "Okay with pets"],
  ["no_pets", "No pets"],
  ["has_pets", "I have a pet"],
];
export const dynamicOptions: [string, string][] = [
  ["independent", "Mostly independent"],
  ["friendly", "Friendly, with personal space"],
  ["close_friends", "Close friends"],
];
export const smokingOptions: [string, string][] = [
  ["non_smoker", "No smoking"],
  ["outside_only", "Outside only"],
  ["any", "No preference"],
];
export const initialHousing: Housing = {
  city: "",
  neighborhood: "",
  budget_min: "",
  budget_max: "",
  move_in_date: "",
  lease_months: 12,
  city_is_requirement: false,
  neighborhood_is_requirement: true,
  budget_is_requirement: true,
  move_in_is_requirement: false,
  lease_is_requirement: false,
};
export const initialChoices = {
  cleanliness: "tidy",
  noise: "2",
  sleep_schedule: "early",
  pets: "okay_with_pets",
  roommate_dynamic: "friendly",
  smoking: "non_smoker",
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
