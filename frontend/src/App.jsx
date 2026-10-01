import { useEffect, useState } from "react";

import {
  matchCandidates,
  getCandidate,
} from "./services/api";


function App() {
  const [companyId, setCompanyId] = useState("company_001");
  const [jdFile, setJdFile] = useState(null);
  const [topK, setTopK] = useState(5);

  const [loading, setLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);

  const [error, setError] = useState("");
  const [detailsError, setDetailsError] = useState("");

  const [result, setResult] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  const [theme, setTheme] = useState(() => {
    return localStorage.getItem("theme") || "dark";
  });


  // =========================================================
  // Theme
  // =========================================================

  useEffect(() => {
    document.documentElement.setAttribute(
      "data-theme",
      theme
    );

    localStorage.setItem("theme", theme);
  }, [theme]);


  // =========================================================
  // Escape key
  // =========================================================

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setSelectedCandidate(null);
        setDetailsError("");
      }
    };

    window.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, []);


  // =========================================================
  // Submit matching
  // =========================================================

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setDetailsError("");
    setResult(null);
    setSelectedCandidate(null);

    if (!companyId.trim()) {
      setError("Company ID is required.");
      return;
    }

    if (!jdFile) {
      setError(
        "Please upload a Job Description PDF."
      );
      return;
    }

    try {
      setLoading(true);

      const data = await matchCandidates({
        companyId,
        file: jdFile,
        topK,
      });

      setResult(data);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Candidate matching failed."
      );

    } finally {
      setLoading(false);
    }
  };


  // =========================================================
  // Candidate details
  // =========================================================

  const handleCandidateClick = async (
    candidateId
  ) => {
    setDetailsError("");

    setSelectedCandidate({
      loading: true,
      candidate_id: candidateId,
    });

    try {
      setDetailsLoading(true);

      const data = await getCandidate({
        companyId,
        candidateId,
      });

      setSelectedCandidate(data);

    } catch (err) {
      setDetailsError(
        err instanceof Error
          ? err.message
          : "Failed to load candidate details."
      );

    } finally {
      setDetailsLoading(false);
    }
  };


  // =========================================================
  // Close modal
  // =========================================================

  const closeCandidateModal = () => {
    setSelectedCandidate(null);
    setDetailsError("");
  };


  // =========================================================
  // Format score
  // =========================================================

  const formatScore = (score) => {
    return `${(
      (score || 0) * 100
    ).toFixed(1)}%`;
  };


  // =========================================================
  // Candidate status
  // =========================================================

  const getCandidateStatus = (
    candidate
  ) => {
    if (
      candidate?.verification?.verified
    ) {
      return "Verified";
    }

    return "Needs Review";
  };


  // =========================================================
  // Format section name
  // =========================================================

  const formatSectionName = (
    section
  ) => {
    if (!section) {
      return "Resume";
    }

    return section
      .replace(/_/g, " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  };


  // =========================================================
  // Render
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="app-header">

        <div className="header-inner">

          <div className="brand">

            <div className="brand-icon">
              AI
            </div>

            <div>
              <h1>
                AI Recruitment RAG
              </h1>

              <p>
                Intelligent candidate search and matching
              </p>
            </div>

          </div>


          <button
            type="button"
            className="theme-toggle"
            onClick={() =>
              setTheme(
                theme === "light"
                  ? "dark"
                  : "light"
              )
            }
          >
            {theme === "light"
              ? "🌙"
              : "☀️"}

            <span>
              {theme === "light"
                ? "Dark"
                : "Light"}
            </span>
          </button>

        </div>

      </header>


      {/* =====================================================
          MAIN
      ===================================================== */}

      <main className="container">


        {/* ===================================================
            SEARCH CARD
        =================================================== */}

        <section className="search-card">

          <div className="section-heading">

            <span className="eyebrow">
              AI MATCHING
            </span>

            <h2>
              Find Matching Candidates
            </h2>

            <p>
              Upload a job description and let
              the AI recruitment engine analyze
              your candidate pool.
            </p>

          </div>


          <form
            onSubmit={handleSubmit}
            className="matching-form"
          >

            {/* Company */}

            <div className="form-group">

              <label htmlFor="companyId">
                Company ID
              </label>

              <input
                id="companyId"
                type="text"
                value={companyId}
                onChange={(event) =>
                  setCompanyId(
                    event.target.value
                  )
                }
                placeholder="Enter company ID"
              />

            </div>


            {/* Candidate count */}

            <div className="form-group">

              <label htmlFor="topK">
                Candidates to return
              </label>

              <input
                id="topK"
                type="number"
                min="1"
                value={topK}
                onChange={(event) =>
                  setTopK(
                    Number(
                      event.target.value
                    )
                  )
                }
              />

            </div>


            {/* JD upload */}

            <div className="form-group">

              <label htmlFor="jdFile">
                Job Description
              </label>

              <label
                htmlFor="jdFile"
                className="upload-area"
              >

                <span className="upload-icon">
                  ↑
                </span>

                <span className="upload-title">

                  {jdFile
                    ? jdFile.name
                    : "Upload Job Description PDF"}

                </span>

                <span className="upload-subtitle">

                  {jdFile
                    ? "File selected successfully"
                    : "PDF files only"}

                </span>

              </label>

              <input
                id="jdFile"
                type="file"
                accept=".pdf,application/pdf"
                onChange={(event) =>
                  setJdFile(
                    event.target.files?.[0] ||
                    null
                  )
                }
                hidden
              />

            </div>


            {/* Error */}

            {error && (
              <div className="error-message">

                <span>!</span>

                {error}

              </div>
            )}


            {/* Submit */}

            <button
              type="submit"
              className="primary-button"
              disabled={loading}
            >

              {loading ? (
                <>
                  <span className="spinner" />

                  Analyzing Candidates...
                </>
              ) : (
                <>
                  Find Matching Candidates

                  <span>
                    →
                  </span>
                </>
              )}

            </button>

          </form>

        </section>


        {/* ===================================================
            RESULTS
        =================================================== */}

        {result && (

          <section className="results-card">

            <div className="results-header">

              <div>

                <span className="eyebrow">
                  SEARCH RESULTS
                </span>

                <h2>
                  Matching Candidates
                </h2>

              </div>

              <div className="candidate-count">

                <strong>
                  {result.candidate_count}
                </strong>

                <span>
                  candidates
                </span>

              </div>

            </div>


            {/* Job summary */}

            {result.job_description && (

              <div className="job-summary">

                <div className="job-icon">
                  JD
                </div>

                <div className="job-info">

                  <h3>
                    {
                      result
                        .job_description
                        .job_title ||
                      "Job Description"
                    }
                  </h3>

                  <p>
                    <strong>
                      Required:
                    </strong>{" "}

                    {
                      result
                        .job_description
                        .required_skills
                        ?.join(", ") ||
                      "None specified"
                    }
                  </p>

                  <p>
                    <strong>
                      Preferred:
                    </strong>{" "}

                    {
                      result
                        .job_description
                        .preferred_skills
                        ?.join(", ") ||
                      "None specified"
                    }
                  </p>

                </div>

              </div>
            )}


            {/* Candidates */}

            <div className="candidate-list">

              {result.candidates?.map(
                (candidate) => (

                  <article
                    className="candidate-card"
                    key={
                      candidate.candidate_id
                    }
                    onClick={() =>
                      handleCandidateClick(
                        candidate.candidate_id
                      )
                    }
                  >

                    <div className="candidate-main">

                      <div className="candidate-avatar">

                        {candidate
                          .candidate_id
                          ?.replace(
                            "candidate_",
                            ""
                          )
                          .slice(0, 2)
                          .toUpperCase()}

                      </div>


                      <div className="candidate-info">

                        <div className="candidate-name-row">

                          <h3>
                            {
                              candidate
                                .candidate_id
                            }
                          </h3>

                          <span
                            className={
                              candidate
                                .verification
                                ?.verified
                                ? "status verified"
                                : "status review"
                            }
                          >
                            {
                              getCandidateStatus(
                                candidate
                              )
                            }
                          </span>

                        </div>

                        <p>
                          Click to view complete
                          candidate profile and evidence
                        </p>

                      </div>

                    </div>


                    <div className="score-block">

                      <span>
                        Match
                      </span>

                      <strong>
                        {
                          formatScore(
                            candidate
                              .scores
                              ?.final_score
                          )
                        }
                      </strong>

                    </div>


                    <div className="candidate-summary">

                      <div>

                        <span>
                          Required
                        </span>

                        <strong>
                          {
                            candidate
                              .matching
                              ?.required_matches
                              ?.length || 0
                          }
                        </strong>

                        <small>
                          matched
                        </small>

                      </div>


                      <div>

                        <span>
                          Missing
                        </span>

                        <strong>
                          {
                            candidate
                              .matching
                              ?.required_missing
                              ?.length || 0
                          }
                        </strong>

                        <small>
                          required
                        </small>

                      </div>


                      <div>

                        <span>
                          Preferred
                        </span>

                        <strong>
                          {
                            candidate
                              .matching
                              ?.preferred_matches
                              ?.length || 0
                          }
                        </strong>

                        <small>
                          matched
                        </small>

                      </div>

                    </div>


                    <div className="candidate-arrow">
                      →
                    </div>

                  </article>

                )
              )}

            </div>

          </section>
        )}

      </main>


      {/* =====================================================
          CANDIDATE MODAL
      ===================================================== */}

      {selectedCandidate && (

        <div
          className="modal-overlay"
          onMouseDown={(event) => {

            if (
              event.target ===
              event.currentTarget
            ) {
              closeCandidateModal();
            }

          }}
        >

          <div
            className="candidate-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="candidate-modal-title"
          >


            {/* =================================================
                MODAL HEADER
            ================================================= */}

            <div className="modal-header">

              <div className="modal-profile">

                <div className="modal-avatar">

                  {selectedCandidate
                    .candidate_id
                    ?.replace(
                      "candidate_",
                      ""
                    )
                    .slice(0, 2)
                    .toUpperCase()}

                </div>


                <div>

                  <span className="eyebrow">
                    CANDIDATE PROFILE
                  </span>

                  <h2 id="candidate-modal-title">

                    {
                      selectedCandidate
                        .profile
                        ?.full_name ||
                      selectedCandidate
                        .candidate_id
                    }

                  </h2>

                  <p>
                    Candidate ID:{" "}
                    {
                      selectedCandidate
                        .candidate_id
                    }
                  </p>

                </div>

              </div>


              <button
                type="button"
                className="modal-close"
                onClick={
                  closeCandidateModal
                }
                aria-label="Close candidate details"
              >
                ×
              </button>

            </div>


            {/* =================================================
                MODAL BODY
            ================================================= */}

            <div className="modal-body">

              {detailsLoading && (

                <div className="modal-loading">

                  <span className="large-spinner" />

                  <h3>
                    Loading candidate details
                  </h3>

                  <p>
                    Fetching resume information...
                  </p>

                </div>

              )}


              {detailsError && (

                <div className="error-message">

                  <span>
                    !
                  </span>

                  {detailsError}

                </div>

              )}


              {!detailsLoading &&
                !detailsError &&
                selectedCandidate.evidence && (

                  <>


                    {/* =========================================
                        PROFILE CONTACT INFORMATION
                    ========================================= */}

                    <div className="profile-contact-grid">


                      <div className="profile-contact-card">

                        <span>
                          Full Name
                        </span>

                        <strong>

                          {
                            selectedCandidate
                              .profile
                              ?.full_name ||
                            "Not available"
                          }

                        </strong>

                      </div>


                      <div className="profile-contact-card">

                        <span>
                          Phone
                        </span>

                        <strong>

                          {
                            selectedCandidate
                              .profile
                              ?.phone ||
                            "Not available"
                          }

                        </strong>

                      </div>


                      <div className="profile-contact-card">

                        <span>
                          Email
                        </span>

                        <strong>

                          {
                            selectedCandidate
                              .profile
                              ?.email ||
                            "Not available"
                          }

                        </strong>

                      </div>


                      <div className="profile-contact-card">

                        <span>
                          Address
                        </span>

                        <strong>

                          {
                            selectedCandidate
                              .profile
                              ?.address ||
                            "Not available"
                          }

                        </strong>

                      </div>


                      <div className="profile-contact-card">

                        <span>
                          Company
                        </span>

                        <strong>

                          {
                            selectedCandidate
                              .company_id
                          }

                        </strong>

                      </div>

                    </div>


                    {/* =========================================
                        STATISTICS
                    ========================================= */}

                    <div className="detail-grid">

                      <div className="detail-stat">

                        <span>
                          Resume Chunks
                        </span>

                        <strong>
                          {
                            selectedCandidate
                              .chunk_count
                          }
                        </strong>

                      </div>


                      <div className="detail-stat">

                        <span>
                          Sections
                        </span>

                        <strong>
                          {
                            selectedCandidate
                              .sections
                              ?.length || 0
                          }
                        </strong>

                      </div>


                      <div className="detail-stat">

                        <span>
                          Evidence
                        </span>

                        <strong>
                          {
                            selectedCandidate
                              .evidence
                              ?.length || 0
                          }
                        </strong>

                      </div>

                    </div>


                    {/* =========================================
                        RESUME SECTIONS
                    ========================================= */}

                    <div className="detail-section">

                      <div className="detail-section-heading">

                        <span className="eyebrow">
                          RESUME
                        </span>

                        <h3>
                          Resume Sections
                        </h3>

                      </div>


                      <div className="tag-list">

                        {selectedCandidate
                          .sections
                          ?.map(
                            (section) => (

                              <span
                                className="tag"
                                key={section}
                              >
                                {
                                  formatSectionName(
                                    section
                                  )
                                }
                              </span>

                            )
                          )}

                      </div>

                    </div>


                    {/* =========================================
                        EVIDENCE
                    ========================================= */}

                    <div className="detail-section">

                      <div className="detail-section-heading">

                        <span className="eyebrow">
                          EVIDENCE
                        </span>

                        <h3>
                          Resume Evidence
                        </h3>

                        <p>
                          Retrieved information
                          supporting this candidate
                          profile.
                        </p>

                      </div>


                      <div className="evidence-list">

                        {selectedCandidate
                          .evidence
                          ?.map(
                            (item, index) => (

                              <div
                                className="evidence-card"
                                key={
                                  item.id ||
                                  index
                                }
                              >

                                <div className="evidence-header">

                                  <span className="evidence-number">
                                    {String(
                                      index + 1
                                    ).padStart(
                                      2,
                                      "0"
                                    )}
                                  </span>

                                  <span className="evidence-section">
                                    {
                                      formatSectionName(
                                        item.section
                                      )
                                    }
                                  </span>

                                </div>

                                <p>
                                  {item.text}
                                </p>

                              </div>

                            )
                          )}

                      </div>

                    </div>

                  </>

                )}

            </div>


            {/* =================================================
                MODAL FOOTER
            ================================================= */}

            <div className="modal-footer">

              <span>
                AI Recruitment RAG
              </span>

              <button
                type="button"
                className="secondary-button"
                onClick={
                  closeCandidateModal
                }
              >
                Close
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}


export default App;