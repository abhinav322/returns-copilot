from pathlib import Path


def load_markdown_file(
    file_path: Path
) -> str:
    return file_path.read_text(
        encoding="utf-8"
    )


def split_by_headings(
    text: str
) -> list[dict]:

    chunks = []

    current_heading = None
    current_lines = []

    for line in text.splitlines():

        stripped = line.strip()

        if stripped.startswith("## "):

            if current_heading is not None:
                content = "\n".join(
                    current_lines
                ).strip()

                if content:
                    chunks.append(
                        {
                            "heading":
                                current_heading,
                            "text":
                                content
                        }
                    )

            current_heading = (
                stripped.removeprefix("## ")
            )

            current_lines = []

        elif not stripped.startswith("# "):
            current_lines.append(line)

    if current_heading is not None:
        content = "\n".join(
            current_lines
        ).strip()

        if content:
            chunks.append(
                {
                    "heading":
                        current_heading,
                    "text":
                        content
                }
            )

    return chunks