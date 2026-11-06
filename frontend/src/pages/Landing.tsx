import { Link } from "react-router-dom";
import { Header } from "../components/Header";
import { Icon } from "../components/Icon";

/** Reproduce the landing reference with local, replaceable portrait assets. */
export function Landing() {
  return (
    <div className="landing-page">
      <Header>
        <Link className="sign-in" to="/login">
          Sign in
        </Link>
      </Header>
      <main className="landing-layout">
        <section className="hero-copy">
          <div className="eyebrow-pill">
            <Icon name="sparkles" />
            Roommates, thoughtfully matched
          </div>
          <h1>
            Find a roommate
            <br />
            who feels like a<br />
            good fit.
          </h1>
          <p className="hero-description">
            Match on the things that matter—from budget and move-in dates to
            quiet hours and cleaning habits.
          </p>
          <Link className="button primary hero-cta" to="/register">
            Create your profile
            <Icon name="arrow" />
          </Link>
          <div className="social-proof">
            <div className="avatar-stack">
              <img src="/images/maya.jpg" alt="" />
              <img src="/images/jordan.jpg" alt="" />
              <img src="/images/avatar.jpg" alt="" />
            </div>
            <span>Join 2,400+ people finding better roommate matches</span>
          </div>
        </section>
        <div
          className="hero-art"
          aria-label="Example roommate profiles and compatibility highlights"
        >
          <div className="portrait-halo" />
          <article className="roommate-card back-card">
            <img
              className="portrait"
              src="/images/jordan.jpg"
              alt="Example roommate Jordan"
            />
            <span className="match-badge">89% match</span>
            <h2>Jordan, 25</h2>
            <p>Graduate student</p>
            <div className="tags">
              <span>Greenpoint</span>
              <span>Easygoing</span>
            </div>
          </article>
          <article className="roommate-card front-card">
            <div className="portrait-wrap">
              <img
                className="portrait"
                src="/images/maya.jpg"
                alt="Example roommate Maya"
              />
              <span className="online-dot" />
            </div>
            <span className="match-badge">94% match</span>
            <h2>Maya, 24</h2>
            <p>Product design intern</p>
            <div className="tags">
              <span>Williamsburg</span>
              <span>Early riser</span>
              <span>Tidy</span>
            </div>
          </article>
          <div className="floating-note budget-note">
            <Icon name="check" />
            <div>
              <strong>Budget aligns</strong>
              <span>$1,600–$1,900</span>
            </div>
          </div>
          <div className="floating-note lifestyle-note">
            <Icon name="sparkles" />
            <div>
              <strong>Great lifestyle fit</strong>
              <span>6 shared preferences</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
