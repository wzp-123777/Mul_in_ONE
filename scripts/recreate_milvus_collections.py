#!/usr/bin/env python3
"""Recreate Milvus collections with string primary keys.

This script drops existing collections and recreates them with VARCHAR primary keys
instead of the default INT64, ensuring compatibility with NAT's Document model.

Usage:
    python scripts/recreate_milvus_collections.py [--tenant-id TENANT] [--persona-id PERSONA]
    
    If no tenant/persona specified, recreates collection for default tenant and persona 1.
"""

import argparse
import sys
import uuid
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
)

# Configuration
MILVUS_HOST = "127.0.0.1"
MILVUS_PORT = "19530"
DEFAULT_EMBED_DIM = 4096  # Default: Qwen3-Embedding-8B dimension (was 1024 for nvidia/nv-embedqa-e5-v5)
VECTOR_FIELD = "vector"  # NAT framework default
CONTENT_FIELD = "text"  # Must match rag_adapter.py


def get_collection_name(tenant_id: str, persona_id: int) -> str:
    """Generate collection name following multi-tenant convention."""
    return f"{tenant_id}_persona_{persona_id}_rag"


def recreate_collection(tenant_id: str, persona_id: int, force: bool = False, embed_dim: int = DEFAULT_EMBED_DIM):
    """Drop and recreate a Milvus collection with string primary keys.
    
    Args:
        tenant_id: Tenant identifier
        persona_id: Persona identifier
        force: If True, skip confirmation prompt
        embed_dim: Embedding dimension (default: 4096 for Qwen3-Embedding-8B)
    """
    collection_name = get_collection_name(tenant_id, persona_id)
    
    print(f"\n{'='*60}")
    print(f"Collection: {collection_name}")
    print(f"Tenant: {tenant_id}, Persona: {persona_id}")
    print(f"{'='*60}\n")
    
    # Connect to Milvus
    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT}...")
    connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
    print("✓ Connected\n")
    
    # Check if collection exists
    exists = utility.has_collection(collection_name)
    
    if exists:
        print(f"⚠️  Collection '{collection_name}' exists and will be DROPPED.")
        print("   All existing data will be permanently lost!\n")
        
        if not force:
            response = input("Continue? [y/N]: ").strip().lower()
            if response != 'y':
                print("Aborted.")
                return
        
        print(f"Dropping collection '{collection_name}'...")
        utility.drop_collection(collection_name)
        print("✓ Collection dropped\n")
    else:
        print(f"Collection '{collection_name}' does not exist yet.\n")
    
    # Define schema with VARCHAR primary key
    print("Creating new collection schema with STRING primary keys...")
    fields = [
        FieldSchema(
            name="document_id",
            dtype=DataType.VARCHAR,
            max_length=64,
            is_primary=True,
            auto_id=False,  # We will supply UUID strings
        ),
        FieldSchema(
            name=VECTOR_FIELD,
            dtype=DataType.FLOAT_VECTOR,
            dim=embed_dim,
        ),
        FieldSchema(
            name=CONTENT_FIELD,
            dtype=DataType.VARCHAR,
            max_length=8192,
        ),
        FieldSchema(
            name="source",
            dtype=DataType.VARCHAR,
            max_length=256,
        ),
    ]
    
    schema = CollectionSchema(
        fields=fields,
        enable_dynamic_field=True,
        description=f"RAG background store for {tenant_id}/persona_{persona_id}",
    )
    
    # Create collection
    collection = Collection(name=collection_name, schema=schema)
    print(f"✓ Collection created: {collection_name}\n")
    
    # Create index on vector field
    print(f"Creating IVF_FLAT index on {VECTOR_FIELD} field...")
    collection.create_index(
        field_name=VECTOR_FIELD,
        index_params={
            "index_type": "IVF_FLAT",
            "metric_type": "L2",  # Match NAT framework default
            "params": {"nlist": 1024},
        },
    )
    print("✓ Index created\n")
    
    # Load collection into memory
    print("Loading collection into memory...")
    collection.load()
    print("✓ Collection loaded\n")
    
    # Display final schema
    print("Collection schema:")
    print(f"  Primary Key: document_id (VARCHAR, max_length=64)")
    print(f"  Vector Field: {VECTOR_FIELD} (FLOAT_VECTOR, dim={embed_dim})")
    print(f"  Content Field: {CONTENT_FIELD} (VARCHAR, max_length=8192)")
    print(f"  Source Field: source (VARCHAR, max_length=256)")
    print(f"  Dynamic Fields: Enabled\n")
    
    print(f"✅ Collection '{collection_name}' is ready for use!")
    print(f"   Remember to use STRING document IDs when ingesting (e.g., UUID strings)\n")


def main():
    parser = argparse.ArgumentParser(
        description="Recreate Milvus collections with string primary keys"
    )
    parser.add_argument(
        "--tenant-id",
        default="default",
        help="Tenant ID (default: 'default')",
    )
    parser.add_argument(
        "--persona-id",
        type=int,
        default=1,
        help="Persona ID (default: 1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--embed-dim",
        type=int,
        default=DEFAULT_EMBED_DIM,
        help=f"Embedding dimension (default: {DEFAULT_EMBED_DIM})",
    )
    
    args = parser.parse_args()
    
    try:
        recreate_collection(args.tenant_id, args.persona_id, args.force, args.embed_dim)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up connection
        connections.disconnect("default")


if __name__ == "__main__":
    main()
