import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useApi } from "../api/ApiContext";
import { useAuth } from "../api/AuthContext";
import { ApiError, type Roommate } from "../api/client";
import { DiscoverHeader } from "../components/DiscoverHeader";
import { Icon } from "../components/Icon";
import {
  budgetLabel,
  filterRoommates,
  lifestyleFilters,
  lifestyleLabel,
  moveInLabel,
  neighborhoods,
  readFilters,
} from "./discovery";

/** Browse all four database-backed demo roommates with optional local filters. */
export function Home() {
  const api = useApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [roommates, setRoommates] = useState<Roommate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const filters = readFilters(params);
  const count =
    filters.areas.length +
    filters.lifestyle.length +
    Number(filters.budget < 2500) +
    Number(Boolean(filters.date));
  const results = filterRoommates(roommates, params);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    api
      .roommates()
      .then((data) => {
        if (active) setRoommates(data.roommates);
      })
      .catch((error) => {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          auth.setUser(null);
          navigate("/login", { replace: true });
        } else
          setError(
            error instanceof Error
              ? error.message
              : "Unable to load roommates.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [api, attempt]);
  /** Replace one single-value filter while retaining all other selections. */
  function setFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    next.delete(key);
    if (value) next.set(key, value);
    setParams(next, { replace: true });
  }
  /** Toggle one choice in a multi-select filter group. */
  function toggleFilter(key: string, value: string) {
    const next = new URLSearchParams(params);
    const selected = next.getAll(key);
    next.delete(key);
    for (const item of selected.filter((item) => item !== value))
      next.append(key, item);
    if (!selected.includes(value)) next.append(key, value);
    setParams(next, { replace: true });
  }
  const chips = [
    ...filters.areas.map((area) => ({ key: "area", value: area, label: area })),
    ...filters.lifestyle.map((value) => ({
      key: "lifestyle",
      value,
      label: lifestyleFilters.find((filter) => filter.key === value)!.label,
    })),
    ...(filters.budget < 2500
      ? [
          {
            key: "budget",
            value: "",
            label: `Up to $${filters.budget.toLocaleString("en-US")}`,
          },
        ]
      : []),
    ...(filters.date
      ? [{ key: "date", value: "", label: `By ${moveInLabel(filters.date)}` }]
      : []),
  ];
  return (
    <>
      <DiscoverHeader />
      <div className="discovery-layout">
        <button
          className="button filter-toggle"
          aria-expanded={filtersOpen}
          aria-controls="discovery-filters"
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          Filters {count > 0 && `(${count})`} <span aria-hidden="true">⌄</span>
        </button>
        <aside
          id="discovery-filters"
          className={`discovery-filters ${filtersOpen ? "is-open" : ""}`}
          aria-label="Roommate filters"
        >
          <div className="filter-heading">
            <h2>Filters</h2>
            <span className="demo-badge">{count} active</span>
            <button className="text-button" onClick={() => setParams({})}>
              Reset
            </button>
          </div>
          <fieldset>
            <legend>Location</legend>
            {neighborhoods.map((area) => (
              <label className="filter-check" key={area}>
                <input
                  type="checkbox"
                  checked={filters.areas.includes(area)}
                  onChange={() => toggleFilter("area", area)}
                />
                {area}
              </label>
            ))}
          </fieldset>
          <fieldset>
            <legend>Monthly budget</legend>
            <label className="budget-caption" htmlFor="budget-cap">
              {filters.budget === 2500
                ? "Any budget"
                : `Up to $${filters.budget.toLocaleString("en-US")}`}
            </label>
            <input
              id="budget-cap"
              aria-label="Maximum monthly budget"
              type="range"
              min="1000"
              max="2500"
              step="50"
              value={filters.budget}
              onChange={(event) =>
                setFilter(
                  "budget",
                  event.target.value === "2500" ? "" : event.target.value,
                )
              }
            />
            <div className="budget-endpoints">
              <span>$1,000</span>
              <span>Any</span>
            </div>
            <p className="filter-hint">
              Includes rent ranges that overlap your cap.
            </p>
          </fieldset>
          <fieldset>
            <legend>Move-in date</legend>
            <select
              aria-label="Move in by"
              value={filters.date}
              onChange={(event) => setFilter("date", event.target.value)}
            >
              <option value="">Any date</option>
              <option value="2027-01-15">By Jan 15, 2027</option>
              <option value="2027-02-01">By Feb 1, 2027</option>
              <option value="2027-02-15">By Feb 15, 2027</option>
            </select>
          </fieldset>
          <fieldset>
            <legend>Lifestyle</legend>
            {lifestyleFilters.map((filter) => (
              <label className="filter-check" key={filter.key}>
                <input
                  type="checkbox"
                  checked={filters.lifestyle.includes(filter.key)}
                  onChange={() => toggleFilter("lifestyle", filter.key)}
                />
                {filter.label}
              </label>
            ))}
          </fieldset>
          <Link className="edit-preferences" to="/setup">
            Edit all preferences <Icon name="arrow" />
          </Link>
        </aside>
        <main className="discovery-main">
          <p className="discovery-eyebrow">FIND YOUR PEOPLE</p>
          <div className="discovery-title">
            <div>
              <h1>Roommates you may click with</h1>
              <p>
                Meet our four demo roommates. Explore their profiles and find
                your kind of home.
              </p>
            </div>
            <label className="sort-label">
              Sort by
              <select
                aria-label="Sort roommates"
                value={filters.sort}
                onChange={(event) => setFilter("sort", event.target.value)}
              >
                <option value="default">All roommates</option>
                <option value="name">Name</option>
                <option value="budget">Lowest budget</option>
                <option value="move">Earliest move-in</option>
              </select>
            </label>
          </div>
          <p className="discovery-note">
            Compatibility scores aren’t available yet. Everyone is shown until
            you apply filters.
          </p>
          <div className="filter-chips">
            {chips.map((chip) => (
              <button
                key={`${chip.key}-${chip.value}`}
                onClick={() =>
                  chip.value
                    ? toggleFilter(chip.key, chip.value)
                    : setFilter(chip.key, "")
                }
                aria-label={`Remove ${chip.label} filter`}
              >
                {chip.label}
                <Icon name="close" />
              </button>
            ))}
          </div>
          {loading ? (
            <div className="discovery-empty" role="status">
              Finding your people…
            </div>
          ) : error ? (
            <div className="discovery-empty">
              <p role="alert">{error}</p>
              <button
                className="button primary"
                onClick={() => setAttempt(attempt + 1)}
              >
                Try again
              </button>
            </div>
          ) : (
            <>
              <p className="result-count" role="status">
                Showing {results.length} of {roommates.length} roommates
              </p>
              {!results.length && (
                <div className="discovery-empty">
                  <Icon name="search" />
                  <h2>
                    {roommates.length
                      ? "A little more room to explore"
                      : "No roommates to show yet"}
                  </h2>
                  <p>
                    {roommates.length
                      ? "Try widening your filters to meet more people."
                      : "Demo profiles haven’t been added yet. Check back soon."}
                  </p>
                  {count > 0 && (
                    <button
                      className="button primary"
                      onClick={() => setParams({})}
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              )}
              <div className="roommate-grid">
                {results.map((roommate) => (
                  <article className="discovery-card" key={roommate.id}>
                    <Link
                      className="roommate-photo"
                      to={`/app/roommates/${roommate.id}${params.size ? `?${params}` : ""}`}
                      aria-label={`View ${roommate.full_name}'s profile`}
                    >
                      <img
                        src={roommate.photo_url}
                        alt={`Placeholder portrait for ${roommate.full_name}`}
                      />
                      <span className="demo-badge">Demo profile</span>
                    </Link>
                    <div className="roommate-body">
                      <h2>
                        <Link
                          to={`/app/roommates/${roommate.id}${params.size ? `?${params}` : ""}`}
                        >
                          {roommate.full_name}, {roommate.age}
                        </Link>
                      </h2>
                      <p className="roommate-occupation">
                        {roommate.occupation}
                      </p>
                      <div className="roommate-facts">
                        <span>
                          <Icon name="pin" />
                          {roommate.housing?.city} ·{" "}
                          {roommate.housing?.neighborhood}
                        </span>
                        <span>
                          <Icon name="money" />
                          {budgetLabel(roommate)} / mo
                        </span>
                      </div>
                      <p className="roommate-routine">
                        {["sleep_schedule", "cleanliness", "roommate_dynamic"]
                          .map((key) =>
                            lifestyleLabel(key, roommate.lifestyle[key]),
                          )
                          .join(" · ")}
                      </p>
                      <div className="roommate-tags">
                        <span>
                          {lifestyleLabel(
                            "smoking",
                            roommate.lifestyle.smoking,
                          )}
                        </span>
                        <span>
                          {lifestyleLabel("pets", roommate.lifestyle.pets)}
                        </span>
                        <span>
                          Move-in {moveInLabel(roommate.housing?.move_in_date)}
                        </span>
                      </div>
                      <Link
                        className="button profile-link"
                        to={`/app/roommates/${roommate.id}${params.size ? `?${params}` : ""}`}
                      >
                        View profile <Icon name="arrow" />
                      </Link>
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}
        </main>
      </div>
    </>
  );
}
