#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import requests

from .database import Database, OrderCondition, WhereCondition
from . import exceptions

###############################################################################

log = logging.getLogger(__name__)

FIRESTORE_BASE_URI = "https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
FIRESTORE_QUERY_ADDITIONS = "{table}?{attachments}&fields=documents(fields%2Cname)"

###############################################################################


class NoCredResponseTypes:
    boolean: str = "booleanValue"
    double: str = "doubleValue"
    dt: str = "timestampValue"
    integer: str = "integerValue"
    null: str = "nullValue"
    string: str = "stringValue"


class CloudFirestoreDatabase(Database):

    def _initialize_creds_db(self, credentials_path: Union[str, Path], name: Optional[str] = None):
        # Resolve credentials
        credentials_path = Path(credentials_path).resolve(strict=True)

        # Initialize database reference
        cred = credentials.Certificate(str(credentials_path))

        # Check name
        # This is done as if the name is None we just want to initialize the main connection
        if name:
            firebase_admin.initialize_app(cred, name=name)
        else:
            firebase_admin.initialize_app(cred)

        # Store configuration
        self._credentials_path = credentials_path
        self._root = firestore.client()

    def __init__(
        self,
        project_id: Optional[str] = None,
        credentials_path: Optional[Union[str, Path]] = None,
        name: Optional[str] = None,
        **kwargs
    ):
        # With credentials:
        if credentials_path:
            self._initialize_creds_db(credentials_path, name)
        elif project_id:
            self._credentials_path = None
            self._project_id = project_id
            self._db_uri = FIRESTORE_BASE_URI.format(project_id=project_id)
        else:
            raise exceptions.MissingParameterError(["project_id", "credentials_path"])

    @staticmethod
    def _jsonify_firestore_response(fields: Dict) -> Dict:
        formatted = {}

        # Cast or parse values from returned
        for k, type_and_value in fields.items():
            if NoCredResponseTypes.boolean in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.boolean]
            elif NoCredResponseTypes.null in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.null]
            elif NoCredResponseTypes.string in type_and_value:
                formatted[k] = type_and_value[NoCredResponseTypes.string]
            elif NoCredResponseTypes.double in type_and_value:
                formatted[k] = float(type_and_value[NoCredResponseTypes.double])
            elif NoCredResponseTypes.integer in type_and_value:
                formatted[k] = int(type_and_value[NoCredResponseTypes.integer])
            elif NoCredResponseTypes.dt in type_and_value:
                if "." in type_and_value[NoCredResponseTypes.dt]:
                    formatted[k] = datetime.strptime(
                        type_and_value[NoCredResponseTypes.dt],
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    )
                else:
                    formatted[k] = datetime.strptime(
                        type_and_value[NoCredResponseTypes.dt],
                        "%Y-%m-%dT%H:%M:%SZ"
                    )
            else:
                formatted[k] = type_and_value

        return formatted

    def _select_row_by_id_with_creds(self, table: str, id: str) -> Dict:
        # Get result
        result = self._root.collection(table).document(id).get().to_dict()

        # Found, return expansion
        if result:
            return {f"{table}_id": id, **result}

        # Not found, return None
        return None

    def _select_row_by_id_no_creds(self, table: str, id: str) -> Dict:
        # Fill target uri
        target_uri = f"{self._db_uri}/{table}/{id}"

        # Get
        response = requests.get(target_uri)

        # Raise errors
        response.raise_for_status()

        # To json
        response = response.json()

        # Check for error
        if "fields" in response:
            # Format response
            return {f"{table}_id": id, **self._jsonify_firestore_response(response["fields"])}

        raise KeyError(f"No row with id: {id} exists.")

    def select_row_by_id(self, table: str, id: str, **kwargs) -> Dict:
        # With credentials
        if self._credentials_path:
            return self._select_row_by_id_with_creds(table=table, id=id)

        return self._select_row_by_id_no_creds(table=table, id=id)

    def _select_rows_as_list_with_creds(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        # Create base table ref
        ref = self._root.collection(table)

        # Apply filters
        if filters:
            for f in filters:
                # Construct WhereCondition
                f = self._construct_where_condition(f)
                # Apply
                ref = ref.where(f.column_name, f.operator, f.value)

        # Apply order by
        if order_by:
            order_by = self._construct_orderby_condition(order_by)
            ref = ref.order_by(order_by.column_name, direction=order_by.operator)

        # Apply limit
        if limit:
            ref = ref.limit(limit)

        # Get and expand
        return [{f"{table}_id": i.id, **i.to_dict()} for i in ref.stream()]

    def _select_rows_as_list_no_creds(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: int = 1000
    ) -> List[Dict]:
        # Warn filters
        if filters:
            log.warning(f"Filters are not currently supported for no credentials databases. Recieved: {filters}")

        # Format order by
        if order_by:
            if isinstance(order_by, str):
                order_by = f"orderBy={order_by}"
            else:
                raise TypeError(
                    f"order_by parameter value must be a string for no credentials databases. Recieved {order_by}"
                )
        else:
            order_by = ""

        # Override limit from None to default 1000
        if limit is None:
            limit = 1000

        # Format limit
        limit = f"pageSize={limit}"

        # Format attachments
        attachments = [order_by, limit]

        # Only attach if there was a value sent
        attachments = "&".join([a for a in attachments if len(a) > 0])

        # Construct query
        target_uri = f"{self._db_uri}/{FIRESTORE_QUERY_ADDITIONS}".format(table=table, attachments=attachments)

        # Get
        response = requests.get(target_uri)

        # Raise errors
        response.raise_for_status()

        # To json
        response = response.json()

        # Check for error
        if "documents" in response:
            return [
                {
                    f"{table}_id": d["name"].split("/")[-1],  # Get last item in the uri
                    **self._jsonify_firestore_response(d["fields"])
                } for d in response["documents"]
            ]

        raise KeyError(f"No table with name: '{table}' exits.")

    def select_rows_as_list(
        self,
        table: str,
        filters: Optional[List[Union[WhereCondition, List, Tuple]]] = None,
        order_by: Optional[Union[List, OrderCondition, str, Tuple]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> List[Dict]:
        # With credentials
        if self._credentials_path:
            return self._select_rows_as_list_with_creds(table=table, filters=filters, order_by=order_by, limit=limit)

        return self._select_rows_as_list_no_creds(table=table, filters=filters, order_by=order_by, limit=limit)

    def _select_rows_with_max_results_expectation(
        self,
        table: str,
        pks: List[Union[WhereCondition, List, Tuple]],
        expected_max_rows: int
    ):
        # Find matching
        pks = [self._construct_where_condition(pk) for pk in pks]
        matching = self.select_rows_as_list(table=table, filters=pks)

        # Handle expectation
        if len(matching) > expected_max_rows:
            raise exceptions.UniquenessError(table, [pk.column_name for pk in pks], matching)
        elif len(matching) == 0:
            return None
        else:
            return matching

    def _get_or_upload_row(self, table: str, pks: List[Union[WhereCondition, List, Tuple]], values: Dict) -> Dict:
        # Reject any upload without credentials
        if self._credentials_path is None:
            raise exceptions.MissingCredentialsError()

        # Fast return for already stored
        found = self._select_rows_with_max_results_expectation(
            table=table,
            pks=pks,
            expected_max_rows=1
        )
        # Return or upload
        if found:
            return found[0]
        else:
            # Create id
            id = str(uuid4())
            # Store the row
            self._root.collection(table).document(id).set(values)

            # Return row
            return {f"{table}_id": id, **values}

    def get_or_upload_body(self, name: str, description: Optional[str] = None) -> Dict:
        return self._get_or_upload_row(
            table="body",
            pks=[("name", name)],
            values={
                "name": name,
                "description": description,
                "created": datetime.utcnow()
            }
        )

    def get_event(self, video_uri: str) -> Dict:
        # Try find
        found = self._select_rows_with_max_results_expectation(
            table="event",
            pks=[("video_uri", video_uri)],
            expected_max_rows=1
        )
        if found:
            return found[0]

        return None

    def get_or_upload_event(
        self,
        body_id: str,
        event_datetime: str,
        source_uri: str,
        video_uri: str
    ) -> Dict:
        return self._get_or_upload_row(
            table="event",
            pks=[("video_uri", video_uri)],
            values={
                "body_id": body_id,
                "event_datetime": event_datetime,
                "source_uri": source_uri,
                "video_uri": video_uri,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_transcript(
        self,
        event_id: str,
        file_id: str,
        confidence: Optional[float] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="transcript",
            pks=[("event_id", event_id), ("file_id", file_id)],
            values={
                "event_id": event_id,
                "file_id": file_id,
                "confidence": confidence,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_algorithm(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict:
        return self._get_or_upload_row(
            table="algorithm",
            pks=[("name", name), ("version", version)],
            values={
                "name": name,
                "version": version,
                "description": description,
                "source": source,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run(self, algorithm_id: str, begin: datetime, completed: datetime) -> Dict:
        return self._get_or_upload_row(
            table="run",
            pks=[("algorithm_id", algorithm_id), ("begin", begin), ("completed", completed)],
            values={
                "algorithm_id": algorithm_id,
                "begin": begin,
                "completed": completed
            }
        )

    def get_or_upload_file(self, uri: str, filename: Optional[str] = None) -> Dict:
        """
        Get or upload a file.
        """
        if filename is None:
            filename = uri.split("/")[-1]

        return self._get_or_upload_row(
            table="file",
            pks=[("uri", uri)],
            values={
                "uri": uri,
                "filename": filename,
                "created": datetime.utcnow()
            }
        )

    def get_or_upload_run_input(self, run_id: str, type: str, value: Any) -> Dict:
        """
        Get or upload a run input.
        """
        return self._get_or_upload_row(
            table="run_input",
            pks=[("run_id", run_id), ("type", type), ("value", value)],
            values={
                "run_id": run_id,
                "type": type,
                "value": value
            }
        )

    def get_or_upload_run_input_file(self, run_id: str, file_id: str) -> Dict:
        """
        Get or upload a run input file.
        """
        return self._get_or_upload_row(
            table="run_input_file",
            pks=[("run_id", run_id), ("file_id", file_id)],
            values={
                "run_id": run_id,
                "file_id": file_id
            }
        )

    def get_or_upload_run_output(self, run_id: str, type: str, value: Any) -> Dict:
        """
        Get or upload a run output.
        """
        return self._get_or_upload_row(
            table="run_output",
            pks=[("run_id", run_id), ("type", type), ("value", value)],
            values={
                "run_id": run_id,
                "type": type,
                "value": value
            }
        )

    def get_or_upload_run_output_file(self, run_id: str, file_id: str) -> Dict:
        """
        Get or upload a run output file.
        """
        return self._get_or_upload_row(
            table="run_output_file",
            pks=[("run_id", run_id), ("file_id", file_id)],
            values={
                "run_id": run_id,
                "file_id": file_id
            }
        )

    def __str__(self):
        if self._credentials_path:
            return f"<CloudFirestoreDatabase [{self._credentials_path}]>"

        return f"<CloudFirestoreDatabase [{self._project_id}]>"

    def __repr__(self):
        return str(self)