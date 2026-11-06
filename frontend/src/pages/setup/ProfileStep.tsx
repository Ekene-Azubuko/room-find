import type { ChangeEvent } from "react";
import type { Housing } from "../../api/client";
import { Icon } from "../../components/Icon";
import type { ProfileDraft, UpdateHousing } from "./options";

/** Render the personal details form and photo control. */
export function ProfileStep({
  profile,
  housing,
  photo,
  photoUrl,
  choosePhoto,
  updateProfile,
  updateHousing,
}: {
  profile: ProfileDraft;
  housing: Housing;
  photo: File | null;
  photoUrl: string;
  choosePhoto: (event: ChangeEvent<HTMLInputElement>) => void;
  updateProfile: (key: keyof ProfileDraft, value: string) => void;
  updateHousing: UpdateHousing;
}) {
  return (
    <div className="surface profile-form">
      <div className="photo-field">
        <img
          src={photoUrl}
          alt={photo ? "Your selected profile photo" : "Profile photo"}
        />
        <div>
          <label className="button secondary photo-button">
            Change photo
            <input
              type="file"
              accept="image/jpeg,image/png"
              onChange={choosePhoto}
              aria-label="Change photo"
            />
          </label>
          <span className="field-hint">JPG or PNG · Max 5 MB</span>
        </div>
      </div>
      <div className="profile-fields">
        <label>
          Full name
          <input
            name="full_name"
            autoComplete="name"
            required
            maxLength={100}
            value={profile.full_name}
            onChange={(event) => updateProfile("full_name", event.target.value)}
            placeholder="Your full name"
          />
        </label>
        <label>
          Age
          <input
            name="age"
            type="number"
            min={18}
            max={120}
            required
            value={profile.age}
            onChange={(event) => updateProfile("age", event.target.value)}
            placeholder="Your age"
          />
        </label>
        <label>
          I’m currently a
          <select
            name="life_stage"
            required
            value={profile.life_stage}
            onChange={(event) =>
              updateProfile("life_stage", event.target.value)
            }
          >
            <option value="" disabled>
              Select an option
            </option>
            {[
              "Student",
              "Young professional",
              "Working professional",
              "Other",
            ].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          Occupation or school
          <input
            name="occupation"
            maxLength={100}
            required
            value={profile.occupation}
            onChange={(event) =>
              updateProfile("occupation", event.target.value)
            }
            placeholder="What keeps you busy?"
          />
        </label>
        <label className="span-two">
          Where are you looking?
          <div className="input-icon">
            <Icon name="pin" />
            <input
              name="city"
              required
              maxLength={100}
              value={housing.city || ""}
              onChange={(event) => updateHousing("city", event.target.value)}
              placeholder="City, state"
            />
          </div>
        </label>
        <label className="span-two">
          A little about you
          <textarea
            name="bio"
            maxLength={240}
            rows={3}
            value={profile.bio}
            onChange={(event) => updateProfile("bio", event.target.value)}
            placeholder="A little about you and what makes a place feel like home…"
          />
          <span className="character-count">
            {profile.bio.length} / 240 characters
          </span>
        </label>
      </div>
    </div>
  );
}
