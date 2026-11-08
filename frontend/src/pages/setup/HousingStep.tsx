import type { Housing } from "../../api/client";
import { Icon } from "../../components/Icon";
import {
  PreferenceRow,
  Requirement,
} from "../../components/PreferenceControls";
import { type UpdateHousing } from "./options";

/** Render housing, move-in, and budget preferences. */
export function HousingStep({
  housing,
  updateHousing,
}: {
  housing: Housing;
  updateHousing: UpdateHousing;
}) {
  return (
    <>
      <aside className="info-banner">
        <Icon name="sparkles" />
        <div>
          <strong>Must-have vs. Flexible</strong>
          <p>
            Must-have means non-negotiable. Flexible means you would consider
            alternatives. Compatibility is not calculated in this demo.
          </p>
        </div>
      </aside>
      <div className="surface housing-form">
        <PreferenceRow
          icon="pin"
          title="Preferred neighborhood"
          description="Where would you like to live?"
        >
          <input
            aria-label="Preferred neighborhood"
            placeholder="Your preferred neighborhoods"
            maxLength={200}
            required
            value={housing.neighborhood || ""}
            onChange={(event) =>
              updateHousing("neighborhood", event.target.value)
            }
          />
          <Requirement
            label="Neighborhood"
            value={housing.neighborhood_is_requirement}
            onChange={(value) =>
              updateHousing("neighborhood_is_requirement", value)
            }
          />
        </PreferenceRow>
        <PreferenceRow
          icon="money"
          title="Monthly budget"
          description="Your share of rent, before utilities."
        >
          <div className="budget-fields">
            <div className="currency-input">
              <span>$</span>
              <input
                aria-label="Minimum monthly budget"
                type="number"
                min={0}
                max={99999999.99}
                step="0.01"
                required
                placeholder="1,500"
                value={housing.budget_min || ""}
                onChange={(event) =>
                  updateHousing("budget_min", event.target.value)
                }
              />
            </div>
            <span>to</span>
            <div className="currency-input">
              <span>$</span>
              <input
                aria-label="Maximum monthly budget"
                type="number"
                min={0}
                max={99999999.99}
                step="0.01"
                required
                placeholder="1,900"
                value={housing.budget_max || ""}
                onChange={(event) =>
                  updateHousing("budget_max", event.target.value)
                }
              />
            </div>
          </div>
          <Requirement
            label="Monthly budget"
            value={housing.budget_is_requirement}
            onChange={(value) => updateHousing("budget_is_requirement", value)}
          />
        </PreferenceRow>
        <PreferenceRow
          icon="calendar"
          title="Move-in & length of stay"
          description="We’ll show people on a similar timeline."
        >
          <div className="date-fields">
            <input
              aria-label="Move-in date"
              type="date"
              required
              value={housing.move_in_date || ""}
              onChange={(event) =>
                updateHousing("move_in_date", event.target.value)
              }
            />
            <select
              aria-label="Length of stay"
              value={housing.lease_months || 12}
              onChange={(event) =>
                updateHousing("lease_months", Number(event.target.value))
              }
            >
              {Array.from(
                new Set([3, 6, 9, 12, 18, 24, housing.lease_months || 12]),
              )
                .sort((a, b) => a - b)
                .map((months) => (
                  <option value={months} key={months}>
                    {months} months
                  </option>
                ))}
            </select>
          </div>
        </PreferenceRow>
      </div>
    </>
  );
}
