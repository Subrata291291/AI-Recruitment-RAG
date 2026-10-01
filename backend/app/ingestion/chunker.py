import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Common resume section headings
SECTION_HEADINGS = [
    "PROFESSIONAL SUMMARY",
    "SUMMARY",
    "OBJECTIVE",
    "CORE TECHNICAL SKILLS",
    "TECHNICAL SKILLS",
    "SKILLS",
    "WORK EXPERIENCE",
    "PROFESSIONAL EXPERIENCE",
    "EXPERIENCE",
    "PROJECTS",
    "SELECTED PROJECTS",
    "SELECTED AI & SOFTWARE PROJECTS",
    "SOFTWARE PROJECTS",
    "PERSONAL PROJECTS",
    "EDUCATION",
    "CERTIFICATIONS",
    "ACHIEVEMENTS",
    "LANGUAGES",
]


def detect_sections(text: str) -> list[tuple[str, str]]:
    """
    Detect common resume sections.

    Returns:
        List of tuples:
        [
            ("professional_summary", "..."),
            ("skills", "..."),
            ("experience", "..."),
        ]
    """

    pattern = "|".join(
        re.escape(section)
        for section in SECTION_HEADINGS
    )

    matches = list(
        re.finditer(
            rf"(?im)^\s*({pattern})\s*$",
            text,
        )
    )

    if not matches:
        return [("general", text.strip())]

    sections = []

    for index, match in enumerate(matches):
        section_name = match.group(1).strip().lower()

        section_name = re.sub(
            r"[^a-z0-9]+",
            "_",
            section_name,
        ).strip("_")

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        content = text[start:end].strip()

        if content:
            sections.append(
                (
                    section_name,
                    content,
                )
            )

    return sections


def chunk_resume(
    documents: list[Document],
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[Document]:
    """
    Convert loaded resume pages into section-aware chunks.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []

    for document in documents:

        sections = detect_sections(
            document.page_content
        )

        for section_name, section_text in sections:

            section_chunks = splitter.split_text(
                section_text
            )

            for chunk_index, chunk_text in enumerate(section_chunks):

                chunk_text = chunk_text.strip()

                if not chunk_text:
                    continue

                metadata = document.metadata.copy()

                metadata.update({
                    "section": section_name,
                    "chunk_index": chunk_index,
                })

                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata=metadata,
                    )
                )

    return chunks