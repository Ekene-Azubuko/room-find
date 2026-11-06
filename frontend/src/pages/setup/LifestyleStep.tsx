import {
  Choices,
  Requirement,
  Scale,
} from "../../components/PreferenceControls";
import {
  cleanlinessValues,
  sleepOptions,
  dynamicOptions,
  smokingOptions,
  type Question,
  type UpdateChoice,
  type UpdateRequirement,
} from "./options";

/** Render shared-home lifestyle choices and importance controls. */
export function LifestyleStep({
  choices,
  requirements,
  updateChoice,
  updateRequirement,
}: {
  choices: Record<Question, string>;
  requirements: Record<Question, boolean>;
  updateChoice: UpdateChoice;
  updateRequirement: UpdateRequirement;
}) {
  return (
    <div className="surface lifestyle-form">
      <Scale
        title="Cleanliness & organization"
        description="How tidy do you like shared spaces?"
        ends={["Relaxed", "Very tidy"]}
        value={String(cleanlinessValues.indexOf(choices.cleanliness) + 1)}
        onChange={(value) =>
          updateChoice("cleanliness", cleanlinessValues[Number(value) - 1])
        }
        required={requirements.cleanliness}
        onRequirement={(value) => updateRequirement("cleanliness", value)}
      />
      <Scale
        title="Noise at home"
        description="What level feels comfortable on weeknights?"
        ends={["Very quiet", "Lively"]}
        value={choices.noise}
        onChange={(value) => updateChoice("noise", value)}
        required={requirements.noise}
        onRequirement={(value) => updateRequirement("noise", value)}
      />
      <section className="lifestyle-section">
        <div className="section-title">
          <div>
            <h2>Your usual sleep schedule</h2>
            <p>Choose the option that’s closest most days.</p>
          </div>
          <Requirement
            label="Sleep schedule"
            value={requirements.sleep_schedule}
            onChange={(value) => updateRequirement("sleep_schedule", value)}
          />
        </div>
        <Choices
          name="Sleep schedule"
          value={choices.sleep_schedule}
          options={sleepOptions}
          onChange={(value) => updateChoice("sleep_schedule", value)}
        />
      </section>
      <section className="lifestyle-section inline-section">
        <div>
          <h2>Roommate dynamic</h2>
          <p>How social would you like home to feel?</p>
        </div>
        <Choices
          name="Roommate dynamic"
          value={choices.roommate_dynamic}
          options={dynamicOptions}
          onChange={(value) => updateChoice("roommate_dynamic", value)}
        />
      </section>
      <section className="lifestyle-section inline-section">
        <div>
          <h2>Smoking</h2>
          <p>Inside or around the home.</p>
        </div>
        <Choices
          name="Smoking"
          value={choices.smoking}
          options={smokingOptions}
          onChange={(value) => updateChoice("smoking", value)}
        />
      </section>
    </div>
  );
}
