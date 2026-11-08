import { Requirement, Scale } from "../../components/PreferenceControls";
import {
  cleanlinessValues,
  initialChoices,
  questionOptions,
  questionTitles,
  type Question,
  type UpdateChoice,
  type UpdateRequirement,
} from "./options";

/** Render independent habits and expectations with importance only on restrictions. */
export function LifestyleStep({
  choices,
  expectations,
  requirements,
  updateChoice,
  updateExpectation,
  updateRequirement,
}: {
  choices: Record<Question, string>;
  expectations: Record<Question, string>;
  requirements: Record<Question, boolean>;
  updateChoice: UpdateChoice;
  updateExpectation: UpdateChoice;
  updateRequirement: UpdateRequirement;
}) {
  return (
    <div className="surface lifestyle-form">
      <p>
        Personal answers describe you. Must-have means a roommate expectation is
        non-negotiable; Flexible means you would consider someone who does not
        meet it.
      </p>
      {(Object.keys(initialChoices) as Question[]).map((key) => (
        <section className="lifestyle-section" key={key}>
          <h2>{questionTitles[key]}</h2>
          {key === "cleanliness" && (
            <p>
              Rate your own habits on the 1–5 scale. Your roommate expectation
              is a separate answer below.
            </p>
          )}
          {key === "cleanliness" ? (
            <Scale
              title="Your cleanliness habits (1–5)"
              description="How do you usually keep shared spaces?"
              ends={["Relaxed", "Very tidy"]}
              value={String(cleanlinessValues.indexOf(choices[key]) + 1)}
              onChange={(value) =>
                updateChoice(key, cleanlinessValues[Number(value) - 1])
              }
            />
          ) : (
            <label>
              Your answer
              <select
                aria-label={questionTitles[key]}
                value={choices[key]}
                onChange={(event) => updateChoice(key, event.target.value)}
              >
                <option value="">Not provided</option>
                {questionOptions(key).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <label>
            {key === "pets"
              ? "Are you comfortable living with a roommate who has pets?"
              : key === "smoking"
                ? "Are you comfortable living with a roommate who smokes?"
                : key === "daytime_visitors"
                  ? "How often are you comfortable with a roommate having daytime visitors?"
                  : key === "overnight_guests"
                    ? "How often are you comfortable with a roommate having overnight guests?"
                    : "Your roommate expectation"}
            <select
              aria-label={`${key} roommate expectation`}
              value={expectations[key]}
              onChange={(event) => updateExpectation(key, event.target.value)}
            >
              <option value="">Not provided</option>
              {questionOptions(key, true).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          {key === "cleanliness" && (
            <ol>
              {questionOptions(key).map(([value, label]) => (
                <li key={value}>{label.replace(/^\d\. /, "")}</li>
              ))}
            </ol>
          )}
          {expectations[key] && expectations[key] !== "no_preference" && (
            <Requirement
              label={`${key} roommate expectation`}
              value={requirements[key]}
              onChange={(value) => updateRequirement(key, value)}
            />
          )}
        </section>
      ))}
    </div>
  );
}
