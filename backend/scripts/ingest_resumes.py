import argparse
from pathlib import Path

from app.ingestion.ingest import ingest_all_resumes
from app.retrieval.sparse import build_and_save_bm25_index


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest resumes for a company."
    )

    parser.add_argument(
        "--company-id",
        required=True,
        help="Unique identifier of the company.",
    )

    parser.add_argument(
        "--resume-dir",
        required=True,
        help="Directory containing resumes for this company.",
    )

    args = parser.parse_args()

    resume_dir = Path(args.resume_dir)

    result = ingest_all_resumes(
        company_id=args.company_id,
        resume_dir=resume_dir,
    )

    bm25_result = build_and_save_bm25_index(
        company_id=args.company_id,
        resume_dir=resume_dir,
    )

    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)

    print(
        f"Company ID:        {args.company_id}"
    )

    print(
        f"Resume directory:  {resume_dir}"
    )

    print(
        f"Resumes processed: {result['resumes']}"
    )

    print(
        f"Chunks created:    {result['chunks']}"
    )

    print(
        f"Vectors uploaded:  {result['vectors']}"
    )

    print(
        f"BM25 chunks:       {bm25_result['chunks']}"
    )

    print(
        f"Total BM25 chunks: {bm25_result['total_chunks']}"
    )


if __name__ == "__main__":
    main()