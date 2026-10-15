from backend.rag.vector_database import (
    VectorBase,
    vector_engine,
)

from backend.rag.vector_models import (
    PolicyChunk,
)


print("Creating vector tables...")


VectorBase.metadata.create_all(
    bind=vector_engine
)


print("Done.")