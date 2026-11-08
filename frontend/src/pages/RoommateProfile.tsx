import { answerLabel, initialChoices, type Question } from "./setup/options";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { useApi } from "../api/ApiContext";
import { useAuth } from "../api/AuthContext";
import { ApiError, type Answer, type Roommate } from "../api/client";
import { DiscoverHeader } from "../components/DiscoverHeader";
import { Icon, type IconName } from "../components/Icon";
import { budgetLabel, lifestyleLabel, moveInLabel } from "./discovery";

/** Present one saved profile fact without claiming a match to the viewer. */
function ProfileFact({
  icon,
  title,
  children,
}: {
  icon: IconName;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="profile-fact">
      <span className="profile-fact-icon">
        <Icon name={icon} />
      </span>
      <div>
        <h3>{title}</h3>
        <p>{children}</p>
      </div>
    </div>
  );
}

const comparisonTopics: Record<Question, string> = {
  cleanliness: "Cleanliness",
  noise: "Noise at home",
  sleep_schedule: "Sleep schedule",
  pets: "Pets",
  smoking: "Smoking",
  roommate_dynamic: "Roommate dynamic",
  daytime_visitors: "Daytime visitors",
  overnight_guests: "Overnight guests",
};

/** Compare saved habits and expectations with one column per person. */
function AnswerComparison({
  ownAnswers,
  roommate,
  hard,
}: {
  ownAnswers: Answer[];
  roommate: Roommate;
  hard: boolean;
}) {
  const topics = (Object.keys(initialChoices) as Question[]).filter((key) => {
    const you = ownAnswers.find((answer) => answer.question_key === key);
    const them = roommate.answers?.find(
      (answer) => answer.question_key === key,
    );
    return Boolean(you?.is_requirement || them?.is_requirement) === hard;
  });
  const title = hard ? "Hard requirements" : "Shared lifestyle preferences";
  return (
    <section className="profile-panel comparison-panel">
      <div className="profile-panel-heading">
        <span className={`section-symbol${hard ? "" : " lavender"}`}>
          <Icon name={hard ? "check" : "sparkles"} />
        </span>
        <div>
          <h2>{title}</h2>
          <p>
            {hard
              ? "The preferences either of you considers essential"
              : "A closer look at your everyday habits and preferences"}
          </p>
        </div>
      </div>
      {topics.length ? (
        <table className="answer-comparison" aria-label={title}>
          <colgroup>
            <col className="comparison-label-column" />
            <col />
            <col />
          </colgroup>
          <thead>
            <tr>
              <th scope="col">At a glance</th>
              <th scope="col">You</th>
              <th scope="col">{roommate.full_name}</th>
            </tr>
          </thead>
          {topics.map((key) => {
            const answers = [
              ownAnswers.find((answer) => answer.question_key === key),
              roommate.answers?.find((answer) => answer.question_key === key),
            ];
            return (
              <tbody key={key}>
                <tr className="comparison-topic">
                  <th colSpan={3} scope="rowgroup">
                    {comparisonTopics[key]}
                  </th>
                </tr>
                <tr>
                  <th scope="row">Personal habits</th>
                  {answers.map((answer, index) => (
                    <td key={index}>{answerLabel(key, answer?.own_answer)}</td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Roommate preference</th>
                  {answers.map((answer, index) => (
                    <td key={index}>
                      {answerLabel(key, answer?.roommate_answer, true)}
                      {answer?.roommate_answer &&
                        answer.roommate_answer !== "no_preference" && (
                          <span
                            className={`preference-badge${answer.is_requirement ? " essential" : ""}`}
                          >
                            {answer.is_requirement ? "Must-have" : "Flexible"}
                          </span>
                        )}
                    </td>
                  ))}
                </tr>
              </tbody>
            );
          })}
        </table>
      ) : (
        <p className="comparison-empty">
          Neither profile lists a must-have lifestyle preference.
        </p>
      )}
    </section>
  );
}

/** Show a single seeded roommate and keep the viewer's discovery filters on return. */
export function RoommateProfile() {
  const { roommateId = "" } = useParams();
  const location = useLocation();
  const api = useApi();
  const auth = useAuth();
  const navigate = useNavigate();
  const [ownAnswers, setOwnAnswers] = useState<Answer[]>([]);
  const [roommate, setRoommate] = useState<Roommate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    window.scrollTo(0, 0);
    setLoading(true);
    setError("");
    setNotFound(false);
    Promise.all([api.roommate(roommateId), api.lifestyle()])
      .then(([data, own]) => {
        if (active) {
          setRoommate(data.roommate);
          setOwnAnswers(own.answers);
        }
      })
      .catch((error) => {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          auth.setUser(null);
          navigate("/login", { replace: true });
        } else {
          setNotFound(error instanceof ApiError && error.status === 404);
          setError(
            error instanceof Error
              ? error.message
              : "Unable to load this profile.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [api, roommateId, attempt]);
  const firstName = roommate?.full_name.split(" ")[0];
  return (
    <>
      <DiscoverHeader />
      <main className="roommate-detail">
        <Link className="back-to-discovery" to={`/app${location.search}`}>
          <Icon name="back" />
          Back to roommates
        </Link>
        {loading ? (
          <div className="discovery-empty" role="status">
            Opening their profile…
          </div>
        ) : error ? (
          <div className="discovery-empty">
            <h1>
              {notFound
                ? "This profile isn’t available"
                : "We couldn’t load this profile"}
            </h1>
            <p role="alert">{error}</p>
            {!notFound && (
              <button
                className="button primary"
                onClick={() => setAttempt(attempt + 1)}
              >
                Try again
              </button>
            )}
            <Link className="button profile-link" to={`/app${location.search}`}>
              Browse roommates
            </Link>
          </div>
        ) : (
          roommate && (
            <div className="profile-detail-grid">
              <aside
                className="profile-introduction"
                aria-label="Roommate introduction"
              >
                <img
                  className="profile-portrait"
                  src={roommate.photo_url}
                  alt={`Placeholder portrait for ${roommate.full_name}`}
                />
                <div className="profile-identity">
                  <span className="demo-badge">Demo profile</span>
                  <h1>
                    {roommate.full_name}, {roommate.age}
                  </h1>
                  <p>{roommate.occupation}</p>
                </div>
                <div className="profile-summary-facts">
                  <p>
                    <Icon name="pin" />
                    {roommate.housing?.city} · {roommate.housing?.neighborhood}
                  </p>
                  <p>
                    <Icon name="money" />
                    {budgetLabel(roommate)} / month
                  </p>
                  <p>
                    <Icon name="calendar" />
                    Move-in {moveInLabel(roommate.housing?.move_in_date)}
                  </p>
                </div>
                <p className="profile-bio">
                  {roommate.bio || "A little more about them is coming soon."}
                </p>
                <button
                  className="button primary interest-button"
                  disabled
                  aria-describedby="interest-note"
                >
                  <Icon name="heart" />
                  Express interest
                </button>
                <p id="interest-note" className="interest-note">
                  Connections are coming soon.
                </p>
              </aside>
              <div className="profile-sections">
                <section className="profile-overview profile-panel">
                  <div>
                    <p className="discovery-eyebrow">ROOMMATE PROFILE</p>
                    <h2>Get to know {firstName}</h2>
                    <p>
                      A closer look at their idea of home. Compatibility hasn’t
                      been calculated yet.
                    </p>
                  </div>
                  <div className="profile-emblem" aria-hidden="true">
                    <Icon name="home" />
                  </div>
                </section>
                <section className="profile-panel">
                  <div className="profile-panel-heading">
                    <span className="section-symbol">
                      <Icon name="home" />
                    </span>
                    <div>
                      <h2>Housing preferences</h2>
                      <p>Where and when they’re hoping to make a home</p>
                    </div>
                  </div>
                  <ProfileFact icon="pin" title="Neighborhood">
                    {roommate.housing?.neighborhood || "Not provided"} ·{" "}
                    {roommate.housing?.city || "Not provided"}
                  </ProfileFact>
                  <ProfileFact icon="money" title="Monthly budget">
                    {budgetLabel(roommate)} for their share of rent
                  </ProfileFact>
                  <ProfileFact icon="calendar" title="Move-in & lease">
                    {moveInLabel(roommate.housing?.move_in_date)} ·{" "}
                    {roommate.housing?.lease_months
                      ? `${roommate.housing.lease_months}-month lease`
                      : "Not provided"}
                  </ProfileFact>
                </section>
                <section className="profile-panel">
                  <div className="profile-panel-heading">
                    <span className="section-symbol lavender">
                      <Icon name="sparkles" />
                    </span>
                    <div>
                      <h2>Lifestyle at home</h2>
                      <p>The everyday things that make a space feel right</p>
                    </div>
                  </div>
                  <dl className="lifestyle-detail-grid">
                    {[
                      { key: "cleanliness", label: "Cleanliness" },
                      { key: "roommate_dynamic", label: "Social style" },
                      { key: "smoking", label: "Smoking" },
                      {
                        key: "daytime_visitors",
                        label: "Daytime visitors (days/week)",
                      },
                      {
                        key: "overnight_guests",
                        label: "Overnight guests (nights/week)",
                      },
                    ].map(({ key, label }) => (
                      <div key={key}>
                        <dt>{label}</dt>
                        <dd>
                          {lifestyleLabel(key, roommate.lifestyle[key], true)}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </section>
                <section className="profile-panel">
                  <div className="profile-panel-heading">
                    <span className="section-symbol amber">
                      <Icon name="sparkles" />
                    </span>
                    <div>
                      <h2>Worth talking about</h2>
                      <p>A good home starts with a conversation</p>
                    </div>
                  </div>
                  <ProfileFact icon="calendar" title="Daily routine">
                    {lifestyleLabel(
                      "sleep_schedule",
                      roommate.lifestyle.sleep_schedule,
                    )}{" "}
                    · {lifestyleLabel("noise", roommate.lifestyle.noise)}
                  </ProfileFact>
                  <ProfileFact icon="heart" title="Pets">
                    {lifestyleLabel("pets", roommate.lifestyle.pets)}
                  </ProfileFact>
                  <ProfileFact icon="home" title="Work from home">
                    Their work-from-home schedule hasn’t been added.
                  </ProfileFact>
                </section>
                {[true, false].map((hard) => (
                  <AnswerComparison
                    key={String(hard)}
                    ownAnswers={ownAnswers}
                    roommate={roommate}
                    hard={hard}
                  />
                ))}
                <p className="profile-demo-note">
                  This is a fictional demo roommate with a placeholder portrait.
                </p>
              </div>
            </div>
          )
        )}
      </main>
    </>
  );
}
