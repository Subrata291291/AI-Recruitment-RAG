from app.retrieval.sparse import build_and_save_bm25_index


if __name__ == "__main__":
    result = build_and_save_bm25_index()

    print("=" * 70)
    print("BM25 INDEX CREATED")
    print("=" * 70)

    print("Chunks:", result["chunks"])
    print("File:", result["file"])