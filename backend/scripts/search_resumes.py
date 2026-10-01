from pathlib import Path

from app.ingestion.jd_loader import load_jd
from app.matching.jd_parser import parse_jd_documents
from app.matching.query_builder import build_jd_query
from app.retrieval.hybrid import hybrid_search


BASE_DIR = Path(__file__).resolve().parent.parent
JD_DIR = BASE_DIR / "data" / "jd"


def main():
    print("=" * 70)
    print("AI Recruitment - JD Based Candidate Search")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Find available JDs
    # ---------------------------------------------------------

    jd_files = sorted(
        JD_DIR.glob("*.pdf")
    )

    if not jd_files:
        print(
            f"No JD PDFs found in: {JD_DIR}"
        )
        return

    print("\nAvailable Job Descriptions:")

    for index, jd_file in enumerate(
        jd_files,
        start=1,
    ):
        print(
            f"{index}. {jd_file.name}"
        )

    # ---------------------------------------------------------
    # 2. Select JD
    # ---------------------------------------------------------

    selection = input(
        "\nSelect JD number: "
    ).strip()

    if not selection.isdigit():
        print("Invalid selection.")
        return

    jd_index = int(selection) - 1

    if (
        jd_index < 0
        or jd_index >= len(jd_files)
    ):
        print("Invalid JD number.")
        return

    selected_jd = jd_files[jd_index]

    print(
        f"\nSelected JD: {selected_jd.name}"
    )

    # ---------------------------------------------------------
    # 3. Load and parse JD
    # ---------------------------------------------------------

    documents = load_jd(
        selected_jd
    )

    jd_requirements = parse_jd_documents(
        documents
    )

    required_skills = jd_requirements[
        "required_skills"
    ]

    preferred_skills = jd_requirements[
        "preferred_skills"
    ]

    # ---------------------------------------------------------
    # 4. Display parsed requirements
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("PARSED JOB REQUIREMENTS")
    print("=" * 70)

    print("\nRequired Skills:")

    for skill in required_skills:
        print(f"  - {skill}")

    print("\nPreferred Skills:")

    for skill in preferred_skills:
        print(f"  - {skill}")

    # ---------------------------------------------------------
    # 5. Build retrieval query
    # ---------------------------------------------------------

    query = build_jd_query(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        role_title=selected_jd.stem.replace(
            "_",
            " ",
        ),
    )

    print("\n" + "=" * 70)
    print("GENERATED RETRIEVAL QUERY")
    print("=" * 70)

    print(query)

    # ---------------------------------------------------------
    # 6. Hybrid candidate search
    # ---------------------------------------------------------

    results = hybrid_search(
        query=query,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    # ---------------------------------------------------------
    # 7. Display results
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print(
        f"Top {len(results)} Candidates"
    )
    print("=" * 70)

    for index, candidate in enumerate(
        results,
        start=1,
    ):
        matching = candidate.get(
            "matching",
            {},
        )

        print(f"\n#{index}")
        print("-" * 70)

        print(
            "Candidate:",
            candidate["candidate_id"],
        )

        # -----------------------------------------------------
        # Matching signals
        # -----------------------------------------------------

        print(
            "\nMatching Signals:"
        )

        print(
            "Requirement Match:",
            round(
                matching.get(
                    "match_score",
                    0.0,
                ),
                4,
            ),
        )

        print(
            "Required Score:",
            round(
                matching.get(
                    "required_score",
                    0.0,
                ),
                4,
            ),
        )

        print(
            "Preferred Score:",
            round(
                matching.get(
                    "preferred_score",
                    0.0,
                ),
                4,
            ),
        )

        # -----------------------------------------------------
        # Final ranking
        # -----------------------------------------------------

        print(
            "Rerank Score:",
            round(
                candidate.get(
                    "rerank_score",
                    0.0,
                ),
                4,
            ),
        )

        print(
            "Final Score:",
            round(
                candidate.get(
                    "final_score",
                    0.0,
                ),
                4,
            ),
        )

        print(
            "Rerank Method:",
            candidate.get(
                "rerank_method",
                "unknown",
            ),
        )

        print(
            "Rerank Reason:",
            candidate.get(
                "rerank_reason",
                "",
            ),
        )

        # -----------------------------------------------------
        # Required skills
        # -----------------------------------------------------

        print(
            "\nRequired Skills:"
        )

        for skill in matching.get(
            "required_matches",
            [],
        ):
            print(
                f"  ✓ {skill}"
            )

        for skill in matching.get(
            "required_missing",
            [],
        ):
            print(
                f"  ✗ {skill}"
            )

        # -----------------------------------------------------
        # Preferred skills
        # -----------------------------------------------------

        print(
            "\nPreferred Skills:"
        )

        for skill in matching.get(
            "preferred_matches",
            [],
        ):
            print(
                f"  ✓ {skill}"
            )

        for skill in matching.get(
            "preferred_missing",
            [],
        ):
            print(
                f"  ✗ {skill}"
            )

        # -----------------------------------------------------
        # Retrieval signals
        # -----------------------------------------------------

        print(
            "\nRetrieval Signals:"
        )

        print(
            "Best RRF Score:",
            round(
                candidate.get(
                    "best_rrf_score",
                    0.0,
                ),
                6,
            ),
        )

        print(
            "Best Dense Score:",
            round(
                candidate.get(
                    "best_dense_score",
                    0.0,
                ),
                4,
            ),
        )

        print(
            "Best BM25 Score:",
            round(
                candidate.get(
                    "best_sparse_score",
                    0.0,
                ),
                4,
            ),
        )

        # -----------------------------------------------------
        # Evidence
        # -----------------------------------------------------

        print(
            "\nEvidence chunks:",
            len(
                candidate.get(
                    "evidence",
                    [],
                )
            ),
        )

        print(
            "\nEvidence:"
        )

        for evidence in candidate.get(
            "evidence",
            [],
        ):
            print(
                f"\n[{evidence.get('section', 'Unknown section')}]"
            )

            print(
                "MMR Score:",
                round(
                    evidence.get(
                        "mmr_score",
                        0.0,
                    ),
                    6,
                ),
            )

            print(
                evidence.get(
                    "text",
                    "",
                )[:400]
            )


if __name__ == "__main__":
    main()