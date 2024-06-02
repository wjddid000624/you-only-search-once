from server.core.config import settings
from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError
from pymongo.server_api import ServerApi
from pymongo.results import InsertOneResult
from pydantic import BaseModel, ValidationError

MONGODB_URI = settings.MONGODB_URI
MONGODB_DATABASE = settings.MONGODB_DATABASE
MONGODB_COLLECTION = settings.MONGODB_COLLECTION


class Body(BaseModel):
    paragraph_id: int
    section: str
    text: str


class Figure(BaseModel):
    idx: int
    name: str
    caption: str
    related: list[int]
    summary: str


class Summary(BaseModel):
    domain: str
    problem: str
    solution: str
    keywords: list[str]


class Document(BaseModel):
    id: str
    abstract: str
    body: list[Body]
    impact: int = 0
    summary: Summary
    published_year: str | None = None
    reference: list[str]
    figures: list[Figure] = []
    tables: list[Figure] = []
    title: str


async def get_mongo_collection():
    client = MongoClient(MONGODB_URI, server_api=ServerApi("1"))
    database = client[MONGODB_DATABASE]
    collection = database[MONGODB_COLLECTION]

    try:
        yield collection
    finally:
        client.close()


def search_by_id(
    collection: Collection,
    id: str
) -> Document:
    """Fetches a document by ID.
    
    Fetch a single document with given ID from database.

    Args:
        collection: `pymongo.collection.Collection` to perform operations.
        id: id of the document to fetch.
    
    Returns:
        A `Document` object representing corresponding document.
    """
    document = collection.find_one({ "_id": id })
    document["id"] = document.pop("_id")

    return Document(**document)


def create_document(
    collection: Collection,
    document: Document
) -> str:
    """Upserts a document.
    
    Updates a document using data from `document`. If no document exists with 
    given id, create one.

    Args:
        collection: `pymongo.collection.Collection` to perform operations.
        document: Fields for documents. Must satisfy the schema `Document`.

    Returns:
        String id value of the upserted document.

    Raises:
        ValidationError: Arguments do not match the schema.
    """
    try:
        document = document.model_dump()
        document["_id"] = document.pop("id")
        
        result = collection.update_one(
            filter={ "_id": document["_id"] },
            update={ "$set": document },
            upsert=True
        )
        
        return result.upserted_id
    except ValidationError as e:
        raise e
