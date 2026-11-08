import type { Housing } from "../../api/client";
import { Icon } from "../../components/Icon";
import type { Detail, ProfileDraft } from "./options";

/** Group the saved preferences and provide links back to their editing steps. */
export function ReviewStep({
  details,
  profile,
  housing,
  photoUrl,
  goToStep,
}: {
  details: Detail[];
  profile: ProfileDraft;
  housing: Housing;
  photoUrl: string;
  goToStep: (step: number) => void;
}) {
  return (
    <>
      <div className="review-columns">
        {[true, false].map((required) => (
          <section
            className={`surface review-card ${required ? "" : "flexible-card"}`}
            key={String(required)}
          >
            <div className="review-title">
              <div>
                <span className="review-badge">
                  {required
                    ? "HARD REQUIREMENTS"
                    : "ANSWERS & FLEXIBLE PREFERENCES"}
                </span>
                <h2>
                  {required
                    ? "Your non-negotiables"
                    : "Your habits and preferences"}
                </h2>
              </div>
              <span>
                {
                  details.filter((detail) => detail.required === required)
                    .length
                }{" "}
                items
              </span>
            </div>
            <div>
              {details
                .filter((detail) => detail.required === required)
                .map((detail) => (
                  <div className="review-item" key={detail.label}>
                    <span className="review-item-icon">
                      <Icon name={required ? "check" : "sparkles"} />
                    </span>
                    <div>
                      <span>{detail.label}</span>
                      <strong>{detail.value}</strong>
                    </div>
                    <button
                      type="button"
                      className="edit-button"
                      aria-label={`Edit ${detail.label}`}
                      onClick={() => goToStep(detail.step)}
                    >
                      <Icon name="edit" />
                      Edit
                    </button>
                  </div>
                ))}
            </div>
          </section>
        ))}
      </div>
      <section className="surface profile-summary">
        <img src={photoUrl} alt="Your profile" />
        <div>
          <h2>
            {profile.full_name || "Your profile"}
            {profile.age && `, ${profile.age}`}
          </h2>
          <p>
            {profile.occupation} · {housing.city}
          </p>
          {profile.bio && <p>{profile.bio}</p>}
        </div>
        <button
          className="edit-button"
          type="button"
          onClick={() => goToStep(1)}
        >
          <Icon name="edit" />
          Edit profile
        </button>
      </section>
    </>
  );
}
