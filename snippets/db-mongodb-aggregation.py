import logging
from typing import Any, Optional

# This file contains examples of complex MongoDB aggregation pipelines for data analysis tasks
# like feature engineering, specifically for TF-IDF related calculations.
# The examples are desensitized and generalized.

def calculate_document_frequency(
    collection,
    term_field: str,
    document_field: str,
    timestamp_field: Optional[str] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
    rank: int = 0,
    world_size: int = 1,
    output_file: Optional[str] = None,
):
    """
    Calculates the Document Frequency (DF) for each term in a corpus.
    DF is the number of documents in which a term appears. It is a prerequisite
    for calculating Inverse Document Frequency (IDF).

    This function demonstrates several advanced MongoDB aggregation techniques:
    - Time-range filtering using $match. For Time Series collections, placing this
      filter at the beginning of the pipeline is crucial for performance as it
      allows the query optimizer to prune entire buckets.
    - Grouping by term and collecting unique documents with $group and $addToSet.
    - Calculating array sizes with $size.
    - Hashing string fields to integers for partitioning or indexing ($toHashedIndexKey).
    - Distributed computation by partitioning the aggregation workload.
    - Handling large aggregations with `allowDiskUse=True`.
    """
    pipeline: list[dict] = []
    match_filter = {}

    # Time-range filtering should be the first stage for Time Series collections
    # to enable bucket pruning.
    if timestamp_field and (start_ts or end_ts):
        time_filter = {}
        if start_ts:
            time_filter['$gte'] = start_ts
        if end_ts:
            time_filter['$lt'] = end_ts
        match_filter[timestamp_field] = time_filter

    # Add partitioning for distributed computation
    if world_size > 1:
        assert rank < world_size
        partition_expr = {
            "$eq": [
                {"$mod": [{"$toLong": {"$toHashedIndexKey": {"field": f"${term_field}"}}}, world_size]},
                rank
            ]
        }
        match_filter["$expr"] = partition_expr

    if match_filter:
        pipeline.append({"$match": match_filter})

    pipeline.extend([
      {'$project': {term_field: 1, document_field: 1, '_id': 0}},
      {"$group": {
        "_id": f"${term_field}",
        'unique_documents': {"$addToSet": f"${document_field}"},
        "total_occurrences": {"$sum": 1}
      }},
      {'$addFields': {
        'doc_frequency': {'$size': "$unique_documents"}
      }},
      {"$project": {
        "hashed_term_id": {'$bitAnd': [{"$toLong": {"$toHashedIndexKey": {"field": "$_id"}}}, 0x7FFFFFFFFFFFFFFF]},
        'doc_frequency': 1,
        "total_occurrences": 1,
        "_id": 0
      }}
    ])

    if output_file and world_size > 1:
      if '.' in output_file:
        base, ext = output_file.rsplit('.', 1)
        output_file = f'{base}_{rank}.{ext}'
      else:
        output_file = f'{output_file}_{rank}'

    cursor = collection.aggregate(pipeline, allowDiskUse=True)
    cursor.batch_size(1024)
    # Prevent cursor timeout for long-running aggregations
    cursor.no_cursor_timeout = True

    if output_file:
      with open(output_file, 'w') as f:
        for doc in cursor:
          f.write(f'{doc["hashed_term_id"]}\t{doc["doc_frequency"]}\n')
      return None
    else:
      results = {}
      for doc in cursor:
        results[doc['hashed_term_id']] = doc["doc_frequency"]
      return results


def calculate_term_frequency(
    collection,
    document_ids: list[str],
    document_id_field: str,
    term_id_field: str,
    event_type_field: Optional[str] = None,
    bhv_types: Optional[list[str]] = None,
    timestamp_field: Optional[str] = None,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
):
    """
    Calculates the Term Frequency (TF) for each term within a given set of documents.
    TF measures how frequently a term appears in a document.

    This function demonstrates:
    - Dynamic query building for the $match stage.
    - Separating high-selectivity filters from low-selectivity ones to guide
      the query optimizer. High-selectivity filters (e.g., document_id) are
      placed in the first $match stage to leverage indexes effectively.
    - Multi-level grouping to first count occurrences and then restructure the data.
    - Using $push to create nested arrays of objects.
    """
    # High-selectivity match stage: should be placed at the beginning to utilize indexes.
    high_selectivity_match = {
      document_id_field: {"$in": list(set(document_ids))}
    }
    if event_type_field and bhv_types:
        high_selectivity_match[event_type_field] = {"$in": list(set(bhv_types))}

    # Low-selectivity match stage: existence checks are better placed after
    # an initial filtering stage to avoid poor index selection.
    low_selectivity_match = {
        term_id_field: {"$ne": None, "$exists": True},
    }
    if timestamp_field:
        time_filter = {}
        if start_ts:
            time_filter['$gte'] = start_ts
        if end_ts:
            time_filter['$lt'] = end_ts
        if time_filter:
            low_selectivity_match[timestamp_field] = time_filter

    pipeline = [
      {"$match": high_selectivity_match},
      {"$match": low_selectivity_match},
      {'$project': {
        'doc_id': f'${document_id_field}',
        'term_id': f'${term_id_field}',
        '_id': 0
      }},
      # First group: count occurrences per (document, term)
      {'$group': {
        '_id': {'doc_id': "$doc_id", 'term_id': "$term_id"},
        'count': {'$sum': 1}
      }},
      # Second group: group by document and push term counts into an array
      {'$group': {
        '_id': "$_id.doc_id",
        'term_counts': {'$push': {'k': "$_id.term_id", 'v': "$count" }}
      }},
      {'$project': {
        'original_doc_id': '$_id',
        'hashed_doc_id': {'$bitAnd': [{"$toLong": {"$toHashedIndexKey": {"field": '$_id'}}}, 0x7FFFFFFFFFFFFFFF]},
        'term_counts': 1,
        '_id': 0
      }},
    ]

    cursor = collection.aggregate(pipeline, allowDiskUse=True)
    cursor.batch_size(1024)

    results = {}
    for doc in cursor:
        term_to_count = {item['k']: item['v'] for item in doc['term_counts']}
        results[doc['original_doc_id']] = {
            'hashed_doc_id': doc['hashed_doc_id'],
            'tf': term_to_count
        }
    return results


def ensure_timeseries_collection(
    client,
    db_name: str,
    coll_name: str,
    meta_field: str,
    time_field: str,
    granularity: Optional[str] = None,
    bucket_max_span_seconds: Optional[int] = None,
    bucket_rounding_seconds: Optional[int] = None,
):
    db = client[db_name]
    options: dict[str, Any] = {
        "timeField": time_field,
        "metaField": meta_field,
    }
    if granularity:
        options["granularity"] = granularity
    if bucket_max_span_seconds is not None:
        options["bucketMaxSpanSeconds"] = bucket_max_span_seconds
    if bucket_rounding_seconds is not None:
        options["bucketRoundingSeconds"] = bucket_rounding_seconds
    try:
        db.create_collection(coll_name, timeseries=options)
    except Exception:
        pass
    return db[coll_name]


def timeseries_query(
    collection,
    meta_filter: dict,
    time_field: str,
    start_ts: Optional[int] = None,
    end_ts: Optional[int] = None,
):
    match_stage = {**meta_filter}
    time_filter = {}
    if start_ts:
        time_filter["$gte"] = start_ts
    if end_ts:
        time_filter["$lt"] = end_ts
    if time_filter:
        match_stage[time_field] = time_filter
    pipeline = [{"$match": match_stage}]
    return list(collection.aggregate(pipeline, allowDiskUse=True))
