import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

/** Switch between filtering requirements and flexible preferences. */
export function Requirement({
  value,
  onChange,
  label,
}: {
  value: boolean;
  onChange: (value: boolean) => void;
  label: string;
}) {
  return (
    <div
      className="requirement"
      role="group"
      aria-label={`${label} importance`}
    >
      <button
        type="button"
        aria-pressed={value}
        className={value ? "selected" : ""}
        onClick={() => onChange(true)}
      >
        Must-have
      </button>
      <button
        type="button"
        aria-pressed={!value}
        className={!value ? "selected" : ""}
        onClick={() => onChange(false)}
      >
        Flexible
      </button>
    </div>
  );
}

/** Render native radio inputs in the reference's outlined choice cards. */
export function Choices({
  name,
  value,
  options,
  onChange,
}: {
  name: string;
  value: string;
  options: [string, string][];
  onChange: (value: string) => void;
}) {
  return (
    <div className="choices" role="group" aria-label={name}>
      {options.map(([key, label]) => (
        <label
          key={key}
          className={`choice ${value === key ? "selected" : ""}`}
        >
          <input
            type="radio"
            name={name}
            value={key}
            checked={value === key}
            onChange={() => onChange(key)}
          />
          <span>{label}</span>
        </label>
      ))}
    </div>
  );
}

/** Pair a housing preference description with its editable controls. */
export function PreferenceRow({
  icon,
  title,
  description,
  children,
}: {
  icon: IconName;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="preference-row">
      <div className="preference-description">
        <span className="preference-icon">
          <Icon name={icon} />
        </span>
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      <div className="preference-inputs">{children}</div>
    </section>
  );
}

/** Render an accessible five-point scale with a requirement toggle. */
export function Scale({
  title,
  description,
  ends,
  value,
  onChange,
  required,
  onRequirement,
}: {
  title: string;
  description: string;
  ends: [string, string];
  value: string;
  onChange: (value: string) => void;
  required: boolean;
  onRequirement: (value: boolean) => void;
}) {
  return (
    <section className="lifestyle-section">
      <div className="section-title">
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
        <Requirement label={title} value={required} onChange={onRequirement} />
      </div>
      <div className="scale-ends">
        <span>{ends[0]}</span>
        <span>{ends[1]}</span>
      </div>
      <div className="scale" role="group" aria-label={title}>
        {[1, 2, 3, 4, 5].map((number) => (
          <label
            className={value === String(number) ? "selected" : ""}
            key={number}
          >
            <input
              type="radio"
              name={title}
              value={number}
              checked={value === String(number)}
              onChange={() => onChange(String(number))}
            />
            <span>{number}</span>
          </label>
        ))}
      </div>
    </section>
  );
}
