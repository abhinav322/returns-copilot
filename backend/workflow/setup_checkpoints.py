from backend.workflow.checkpoint_database import (
    CHECKPOINTER,
)


def setup():

    print(
        "Setting up LangGraph "
        "checkpoint tables..."
    )

    CHECKPOINTER.setup()

    print(
        "Checkpoint tables ready."
    )


if __name__ == "__main__":
    setup()