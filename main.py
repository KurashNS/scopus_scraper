import csv
from typing import Dict, List

from pydantic import ValidationError

from core import schemes
from core.db import models
from core.db.connector import DatabaseConnector, SQLAlchemyError
from core.scraper import ScopusClient
from utils.log import ScopusClientLogger


SCOPUS_IDS_CSV = 'storage/scopus_authors.csv'

OMSTU_AFF_INST_IDS = ['100459484', '60075514', '110906095', '100339616', '101349208', '100423925']
PUB_YEAR = [
    # 2020,
    # 2021,
    # 2022,
    # 2023,
    2024
]

_proxies = {
    'http': 'http://yfy5n4:s4SsUv@185.82.126.71:13502',
    'https': 'http://yfy5n4:s4SsUv@185.82.126.71:13502'
}

_logger = ScopusClientLogger()


def get_authors_id_from_csv():
    authors_id = []
    with open(SCOPUS_IDS_CSV, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            authors_id.extend(row)

    return authors_id


def remove_redundant_ids():
    source_ids = get_authors_id_from_csv()
    all_ids = []
    with open('scopus_authors_.csv', 'r') as csvf:
        reader = csv.reader(csvf)
        for row in reader:
            all_ids.extend(row)

    source_ids = set(source_ids)
    all_ids = set(all_ids)

    return list(all_ids.difference(source_ids))


def _get_documents(author_id: str) -> List[Dict]:
    with ScopusClient(_proxies) as client:
        with DatabaseConnector() as connector:
            documents = client.get_author_documents(author_id=author_id)
            return [
                document for document in documents.get('items', [])
                if document.get('pubYear', 0) or 0 in PUB_YEAR
                and not connector.record_exists(models.Document, 'scopus_id', document.get('scopusId', ''))
            ]


def _get_documents_authors(author_id: str, documents: List[Dict]) -> List[Dict]:
    authors_ids = [
        author.get('authorId')
        for document in documents
        for author in document.get('authors', []) or []
        if author.get('authorId')
    ]
    authors_ids.append(author_id)
    authors_ids = list(set(authors_ids))

    with ScopusClient(_proxies) as client:
        with DatabaseConnector() as connector:
            return [client.get_author(author_id=doc_author_id) for doc_author_id in authors_ids
                    if not connector.record_exists(models.Author, 'id', doc_author_id)]


def _insert_author(author_desc: Dict) -> None:
    with DatabaseConnector() as connector:
        try:
            author = schemes.Author.model_validate(obj=author_desc)
            if author.affiliated_institution_id not in OMSTU_AFF_INST_IDS:
                return

            connector.insert_affiliated_institution(author.affiliated_institution)

            published_subject_areas = author.subject_areas
            for subject_area in published_subject_areas:
                connector.insert_subject_area(subject_area)

            connector.insert_author(author)

            connector.session.commit()
        except ValidationError as e:
            author_id = author_desc.get('authorId')
            _logger.error(f'Author ID: {author_id} | {type(e)} - {str(e)}')
        except SQLAlchemyError as e:
            connector.session.rollback()
            _logger.error(f'Author ID: {author.id} | Unable to insert author description into database: {type(e)} - {str(e)}')


def _insert_document(author_id: str, document_desc: Dict) -> None:
    with DatabaseConnector() as connector:
        try:
            document = schemes.Document.model_validate(obj=document_desc)

            connector.insert_source(document.source)

            subject_areas = document.subject_areas
            for subject_area in subject_areas:
                connector.insert_subject_area(subject_area)

            connector.insert_document(document)

            connector.session.commit()
        except ValidationError as e:
            _logger.error(f'Author ID: {author_id} | {type(e)} - {str(e)}')
        except SQLAlchemyError as e:
            connector.session.rollback()
            _logger.error(f'Author ID: {author_id} | Unable to insert document description into database: {type(e)} - {str(e)}')


def main(authors_id: List[str]):
    for author_id in authors_id:
        documents = _get_documents(author_id=author_id)
        authors = _get_documents_authors(author_id=author_id, documents=documents)

        for author in authors:
            _insert_author(author_desc=author)

        for document in documents:
            _insert_document(author_id=author_id, document_desc=document)


if __name__ == '__main__':
    main(authors_id=get_authors_id_from_csv())
