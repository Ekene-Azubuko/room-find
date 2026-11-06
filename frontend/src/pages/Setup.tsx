import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type FormEvent,
} from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useApi } from "../api/ApiContext";
import { useAuth } from "../api/AuthContext";
import { ApiError, type Answer, type Housing } from "../api/client";
import { Header } from "../components/Header";
import { Icon } from "../components/Icon";
import {
  steps,
  titles,
  descriptions,
  cleanlinessValues,
  cleanlinessLabels,
  noiseLabels,
  sleepOptions,
  petOptions,
  dynamicOptions,
  smokingOptions,
  initialHousing,
  initialChoices,
  type Question,
  type Detail,
  type ProfileDraft,
} from "./setup/options";
import { ProfileStep } from "./setup/ProfileStep";
import { HousingStep } from "./setup/HousingStep";
import { LifestyleStep } from "./setup/LifestyleStep";
import { ReviewStep } from "./setup/ReviewStep";

/** Resolve an option's readable label for the review screen. */
function optionLabel(options: [string, string][], value: string) {
  return options.find(([key]) => key === value)?.[1] || value;
}

/** Guide account owners through four persisted profile-setup steps. */
export function Setup() {
  const api = useApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const step = Math.min(
    4,
    Math.max(1, Math.trunc(Number(params.get("step"))) || 1),
  );
  const heading = useRef<HTMLHeadingElement>(null);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [profile, setProfile] = useState<ProfileDraft>({
    full_name: "",
    age: "",
    life_stage: "",
    occupation: "",
    bio: "",
  });
  const [housing, setHousing] = useState<Housing>(initialHousing);
  const [choices, setChoices] = useState(initialChoices);
  const [requirements, setRequirements] = useState<Record<Question, boolean>>({
    cleanliness: false,
    noise: true,
    sleep_schedule: false,
    pets: false,
    roommate_dynamic: false,
    smoking: false,
  });
  const [photoUrl, setPhotoUrl] = useState("/images/avatar.jpg");
  const [photo, setPhoto] = useState<File | null>(null);

  /** Restore existing answers without replacing saved values with sample people. */
  async function load() {
    setLoading(true);
    setError("");
    try {
      const [person, home, lifestyle] = await Promise.all([
        api.profile(),
        api.housing(),
        api.lifestyle(),
      ]);
      const p = person.profile;
      setProfile({
        full_name: p.full_name || "",
        age: p.age?.toString() || "",
        life_stage: p.life_stage || "",
        occupation: p.occupation || "",
        bio: p.bio || "",
      });
      if (p.photo_url) setPhotoUrl(p.photo_url);
      if (home.housing) setHousing({ ...initialHousing, ...home.housing });
      const savedChoices = { ...initialChoices };
      const savedRequirements = { ...requirements };
      for (const answer of lifestyle.answers) {
        if (answer.question_key in initialChoices && answer.own_answer) {
          const key = answer.question_key as Question;
          savedChoices[key] = answer.own_answer;
          savedRequirements[key] = answer.is_requirement;
        }
      }
      setChoices(savedChoices);
      setRequirements(savedRequirements);
      setLoaded(true);
    } catch (error) {
      handleError(error);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    void load();
  }, [api]);
  useEffect(() => {
    if (!photo) return;
    const url = URL.createObjectURL(photo);
    setPhotoUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);
  useEffect(() => {
    window.scrollTo(0, 0);
    heading.current?.focus();
  }, [step]);

  /** Show write failures and route expired sessions back to login. */
  function handleError(error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      auth.setUser(null);
      navigate("/login", { replace: true });
    } else
      setError(
        error instanceof Error
          ? error.message
          : "Unable to save your answers. Please try again.",
      );
  }
  /** Update a profile field while retaining the rest of the draft. */
  function updateProfile(key: keyof typeof profile, value: string) {
    setProfile((previous) => ({ ...previous, [key]: value }));
  }
  /** Update one housing answer without replacing unrelated fields. */
  function updateHousing<K extends keyof Housing>(key: K, value: Housing[K]) {
    setHousing((previous) => ({ ...previous, [key]: value }));
  }
  /** Update one lifestyle choice. */
  function updateChoice(key: Question, value: string) {
    setChoices((previous) => ({ ...previous, [key]: value }));
  }
  /** Update the selected preference's importance. */
  function updateRequirement(key: Question, value: boolean) {
    setRequirements((previous) => ({ ...previous, [key]: value }));
  }
  /** Validate the chosen upload before displaying its local preview. */
  function choosePhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (
      !["image/jpeg", "image/png"].includes(file.type) ||
      file.size > 5 * 1024 * 1024
    ) {
      setError("Choose a JPG or PNG photo, 5 MB or smaller.");
      event.target.value = "";
      return;
    }
    setError("");
    setPhoto(file);
  }
  /** Map the shared-home controls to the API's own and preferred-roommate answers. */
  function answer(key: Question): Answer {
    const value = choices[key];
    return {
      question_key: key,
      own_answer: value,
      roommate_answer: value === "any" ? "no_preference" : value,
      is_requirement: value === "any" ? false : requirements[key],
    };
  }
  /** Save the current step before advancing, retaining the draft after a failed write. */
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (step === 1) {
        await api.saveProfile({
          ...profile,
          full_name: profile.full_name.trim(),
          age: profile.age ? Number(profile.age) : null,
          life_stage: profile.life_stage || null,
          occupation: profile.occupation || null,
        });
        await api.saveHousing({ city: housing.city?.trim() || null });
        if (photo) {
          await api.uploadPhoto(photo);
          setPhoto(null);
          setPhotoUrl(`/api/profile/photo?v=${Date.now()}`);
        }
      } else if (step === 2) {
        if (Number(housing.budget_min) > Number(housing.budget_max))
          throw new Error(
            "Your minimum budget must not exceed your maximum budget.",
          );
        // Pick editable fields explicitly; GET also includes a read-only updated_at value.
        await api.saveHousing({
          city: housing.city,
          neighborhood: housing.neighborhood?.trim() || null,
          budget_min: housing.budget_min,
          budget_max: housing.budget_max,
          move_in_date: housing.move_in_date,
          lease_months: housing.lease_months,
          city_is_requirement: housing.city_is_requirement,
          neighborhood_is_requirement: housing.neighborhood_is_requirement,
          budget_is_requirement: housing.budget_is_requirement,
          move_in_is_requirement: housing.move_in_is_requirement,
          lease_is_requirement: housing.lease_is_requirement,
        });
        await api.saveAnswer(answer("pets"));
      } else if (step === 3) {
        // Writes are sequential because each CSRF response can update the session cookie.
        for (const key of [
          "cleanliness",
          "noise",
          "sleep_schedule",
          "roommate_dynamic",
          "smoking",
        ] as Question[])
          await api.saveAnswer(answer(key));
      } else {
        await api.complete();
        navigate("/app", { replace: true });
        return;
      }
      setParams({ step: String(step + 1) });
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }
  /** Navigate to a previous step while keeping in-memory drafts. */
  function goToStep(next: number) {
    setError("");
    setParams({ step: String(next) });
  }

  const money = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  const details: Detail[] = [
    {
      label: "Neighborhood",
      value: housing.neighborhood || housing.city || "Not set",
      required: housing.neighborhood_is_requirement,
      step: 2,
    },
    {
      label: "Monthly budget",
      value:
        housing.budget_min && housing.budget_max
          ? `${money.format(Number(housing.budget_min))}–${money.format(Number(housing.budget_max))}`
          : "Not set",
      required: housing.budget_is_requirement,
      step: 2,
    },
    {
      label: "Move-in",
      value: `${housing.move_in_date ? new Date(`${housing.move_in_date}T12:00:00`).toLocaleDateString("en-US", { month: "long", day: "numeric" }) : "Not set"} · ${housing.lease_months || "—"} months`,
      required: housing.move_in_is_requirement || housing.lease_is_requirement,
      step: 2,
    },
    {
      label: "Pets",
      value: optionLabel(petOptions, choices.pets),
      required: requirements.pets,
      step: 2,
    },
    {
      label: "Cleanliness",
      value:
        cleanlinessLabels[cleanlinessValues.indexOf(choices.cleanliness)] ||
        choices.cleanliness,
      required: requirements.cleanliness,
      step: 3,
    },
    {
      label: "Noise at home",
      value: noiseLabels[Number(choices.noise) - 1],
      required: requirements.noise,
      step: 3,
    },
    {
      label: "Sleep schedule",
      value: optionLabel(sleepOptions, choices.sleep_schedule),
      required: requirements.sleep_schedule,
      step: 3,
    },
    {
      label: "Roommate dynamic",
      value: optionLabel(dynamicOptions, choices.roommate_dynamic),
      required: requirements.roommate_dynamic,
      step: 3,
    },
    {
      label: "Smoking",
      value: optionLabel(smokingOptions, choices.smoking),
      required: requirements.smoking,
      step: 3,
    },
  ];

  return (
    <>
      <Header>
        <span className="header-muted">Your answers are private</span>
      </Header>
      {loading ? (
        <main className="status-page" role="status">
          Loading your profile…
        </main>
      ) : !loaded ? (
        <main className="status-page">
          <p role="alert">{error}</p>
          <button className="button primary" onClick={load}>
            Try again
          </button>
        </main>
      ) : (
        <main className="setup-layout">
          <div className="setup-progress">
            <div className="progress-caption">
              <span>Profile setup</span>
              <span>{step} of 4</span>
            </div>
            <div
              className="progress-track"
              role="progressbar"
              aria-label="Profile setup"
              aria-valuenow={step}
              aria-valuemin={0}
              aria-valuemax={4}
            >
              <div style={{ width: `${step * 25}%` }} />
            </div>
            <ol>
              {steps.map((label, index) => (
                <li
                  className={index < step ? "active" : ""}
                  aria-current={index + 1 === step ? "step" : undefined}
                  key={label}
                >
                  {label}
                </li>
              ))}
            </ol>
          </div>
          <div className="setup-heading">
            <span className="step-label">STEP {step}</span>
            <h1 ref={heading} tabIndex={-1}>
              {titles[step - 1]}
            </h1>
            <p>{descriptions[step - 1]}</p>
          </div>
          <form onSubmit={submit}>
            <fieldset disabled={busy}>
              {step === 1 && (
                <ProfileStep
                  profile={profile}
                  housing={housing}
                  photo={photo}
                  photoUrl={photoUrl}
                  choosePhoto={choosePhoto}
                  updateProfile={updateProfile}
                  updateHousing={updateHousing}
                />
              )}
              {step === 2 && (
                <HousingStep
                  housing={housing}
                  choices={choices}
                  requirements={requirements}
                  updateHousing={updateHousing}
                  updateChoice={updateChoice}
                  updateRequirement={updateRequirement}
                />
              )}
              {step === 3 && (
                <LifestyleStep
                  choices={choices}
                  requirements={requirements}
                  updateChoice={updateChoice}
                  updateRequirement={updateRequirement}
                />
              )}
              {step === 4 && (
                <ReviewStep
                  details={details}
                  profile={profile}
                  housing={housing}
                  photoUrl={photoUrl}
                  goToStep={goToStep}
                />
              )}
              {error && (
                <div className="error-message setup-error" role="alert">
                  {error}
                </div>
              )}
              <div className="step-navigation">
                <button
                  className="button secondary"
                  type="button"
                  onClick={() =>
                    step === 1 ? navigate("/app") : goToStep(step - 1)
                  }
                >
                  <Icon name="back" />
                  Back
                </button>
                <button className="button primary" type="submit">
                  {busy
                    ? "Saving…"
                    : step === 4
                      ? "Find my matches"
                      : "Continue"}
                  <Icon name="arrow" />
                </button>
              </div>
            </fieldset>
          </form>
        </main>
      )}
    </>
  );
}
