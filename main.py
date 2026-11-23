
import os
import json
import tempfile

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    UploadFile,
    File
)
from dotenv import load_dotenv

from schemas import SearchRequest, SearchResponse
from search import SemanticSearch
from auth import verify_api_key
from extract import extract_document
from chunking import split_text


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "chunks.jsonl"

MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2"
)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@asynccontextmanager
async def lifespan(app: FastAPI):

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    app.state.search_engine = SemanticSearch(
        MODEL_NAME,
        DATA_PATH
    )

    print("Semantic search API started!")

    yield

    print("Application shutting down...")


app = FastAPI(
    title="Semantic Document Search API",
    description="Document ingestion and semantic search",
    version="1.0.0",
    lifespan=lifespan
)


def save_records(records):

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing_records = []

    if DATA_PATH.exists():

        with open(DATA_PATH, "r", encoding="utf-8") as file:

            for line in file:
                if line.strip():
                    existing_records.append(json.loads(line))

    existing_records = [
        item for item in existing_records
        if item.get("source") != records[0]["source"]
    ]

    all_records = existing_records + records

    temp_path = DATA_DIR / "chunks.tmp"

    with open(temp_path, "w", encoding="utf-8") as file:

        for record in all_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    temp_path.replace(DATA_PATH)


@app.get("/")
def home():

    return {
        "message": "Welcome to Semantic Document Search API"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "message": "API is running"
    }


@app.get(
    "/documents",
    dependencies=[Depends(verify_api_key)]
)
def get_documents():

    return {
        "documents": app.state.search_engine.get_documents()
    }


@app.post(
    "/search",
    response_model=SearchResponse,
    dependencies=[Depends(verify_api_key)]
)
def search_documents(request: SearchRequest):

    results = app.state.search_engine.search(
        query=request.query,
        top_k=request.top_k,
        doc_type=request.doc_type,
        source=request.source,
        min_score=request.min_score
    )

    return {
        "results": results,
        "total_results": len(results)
    }


@app.post(
    "/documents",
    dependencies=[Depends(verify_api_key)]
)
async def upload_document(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    filename = Path(file.filename).name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Only PDF, DOCX and TXT files are supported"
        )

    content = await file.read()

    if not content or not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False
        ) as temp_file:

            temp_file.write(content)
            temp_path = Path(temp_file.name)

        pages = extract_document(temp_path)

        records = []

        for page_data in pages:

            chunks = split_text(
                page_data["text"],
                chunk_size=800,
                overlap=150
            )

            for chunk in chunks:

                records.append({
                    "source": filename,
                    "page": page_data["page"],
                    "section": Path(filename).stem,
                    "doc_type": extension.lstrip("."),
                    "text": chunk
                })

        if not records:
            raise HTTPException(
                status_code=400,
                detail="Document contains no extractable text"
            )

        save_records(records)

        app.state.search_engine.refresh()

        return {
            "message": "Document indexed successfully",
            "source": filename,
            "total_chunks": len(records)
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=503,
            detail=f"Document storage or indexing failed: {str(error)}"
        )

    finally:

        if temp_path and temp_path.exists():
            temp_path.unlink()


@app.delete(
    "/documents/{source}",
    dependencies=[Depends(verify_api_key)]
)
def delete_document(source: str):

    filename = Path(source).name

    if filename != source or source in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid document source"
        )

    try:

        if not DATA_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        with open(DATA_PATH, "r", encoding="utf-8") as file:

            records = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        updated_records = [
            item for item in records
            if item.get("source") != filename
        ]

        if len(updated_records) == len(records):
            raise HTTPException(
                status_code=404,
                detail="Document not found"
            )

        temp_path = DATA_DIR / "chunks.tmp"

        with open(temp_path, "w", encoding="utf-8") as file:

            for record in updated_records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

        temp_path.replace(DATA_PATH)

        app.state.search_engine.refresh()

        return {
            "message": "Document deleted successfully",
            "source": filename,
            "remaining_chunks": len(updated_records)
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=503,
            detail=f"Document deletion failed: {str(error)}"
        )
