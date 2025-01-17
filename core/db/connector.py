from typing import Dict, List

from sqlalchemy import create_engine, exists
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from core import schemes
from core.db import models
from utils.log import ScopusClientLogger


class DatabaseConnector:
    DATABASE_URL = 'postgresql+psycopg2://postgres:123@localhost:5432/qwerty'

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnector, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._engine = create_engine(DatabaseConnector.DATABASE_URL)
        self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
        models.Base.metadata.create_all(bind=self._engine)

        self._logger = ScopusClientLogger()

    def __enter__(self) -> 'DatabaseConnector':
        self.session = self._SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self.session:
            self.session.close()
        return False

    def record_exists(self, model: models.Base, column_name: str, value: str):
        return self.session.query(exists().where(getattr(model, column_name) == value)).scalar()

    def insert_record(
            self,
            model: models.Base,
            record: Dict,
            index_elements: List[str],
            on_conflict_do_update: bool = True
    ) -> None:
        insert_record_stmt = insert(model).values(**record)
        if on_conflict_do_update:
            insert_record_stmt = insert_record_stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_={col_name: value for col_name, value in record.items() if col_name not in index_elements}
            )
        else:
            insert_record_stmt = insert_record_stmt.on_conflict_do_nothing(index_elements=index_elements)

        self.session.execute(insert_record_stmt)

    def insert_affiliated_institution(self, affiliated_institution: schemes.AffiliatedInstitution) -> None:
        affiliated_institution_desc = affiliated_institution.model_dump(by_alias=True)
        self.insert_record(model=models.AuthorAffiliatedInstitution, record=affiliated_institution_desc, index_elements=['id'])

    def insert_author(self, author: schemes.Author) -> None:
        author_dump = author.model_dump(by_alias=True, exclude={'name_variants', 'affiliated_institution', 'subject_areas'})
        self.insert_record(model=models.Author, record=author_dump, index_elements=['id'])

        author_name_variants = author.dump_name_variants()
        for name_variant in author_name_variants:
            self.insert_record(model=models.AuthorNameVariant, record=name_variant,
                               index_elements=['author_id', 'name'], on_conflict_do_update=False)

        author_subject_areas = author.dump_subject_areas()
        for author_subject_area in author_subject_areas:
            self.insert_record(model=models.AuthorSubjectArea, record=author_subject_area,
                               index_elements=['author_id', 'subject_area_codename'], on_conflict_do_update=False)

    def insert_source(self, source: schemes.Source) -> None:
        source_desc = source.model_dump(by_alias=True)
        self.insert_record(model=models.Source, record=source_desc, index_elements=['id'])

    def insert_document(self, document: schemes.Document) -> None:
        document_desc = document.dump()
        self.insert_record(model=models.Document, record=document_desc, index_elements=['scopus_id'])

        document_titles = document.dump_titles()
        for document_title in document_titles:
            self.insert_record(model=models.DocumentTitle, record=document_title,
                               index_elements=['document_id', 'title'], on_conflict_do_update=False)

        document_abstract_texts = document.dump_abstract_texts()
        for document_abstract_text in document_abstract_texts:
            self.insert_record(model=models.DocumentAbstractText, record=document_abstract_text,
                               index_elements=['document_id', 'text'], on_conflict_do_update=False)

        document_source = document.dump_source()
        self.insert_record(model=models.DocumentSource, record=document_source,
                           index_elements=['document_id', 'source_id'], on_conflict_do_update=False)

        document_source_relationship = document.dump_source_relationship()
        self.insert_record(
            model=models.DocumentSourceRelationship,
            record=document_source_relationship,
            index_elements=[
                'document_id', 'issue', 'volume', 'article_number', 'page_count', 'first_page', 'last_page', 'info_page'
            ],
            on_conflict_do_update=False)

        document_authors = document.dump_authors()
        for document_author in document_authors:
            self.insert_record(model=models.DocumentAuthorship, record=document_author,
                               index_elements=['document_id', 'author_id'], on_conflict_do_update=False)

        document_subject_areas = document.dump_subject_areas()
        for document_subject_area in document_subject_areas:
            self.insert_record(model=models.DocumentSubjectArea, record=document_subject_area,
                               index_elements=['document_id', 'subject_area_code'], on_conflict_do_update=False)

    def insert_subject_area(self, subject_area: schemes.SubjectArea):
        subject_area_desc = subject_area.model_dump(by_alias=True)
        insert_subject_area_stmt = insert(models.SubjectArea).values(**subject_area_desc)
        index_elements = ['name']
        update_values = {}

        if subject_area.code and not subject_area.codename:
            update_values = {'code': subject_area.code}
        elif not subject_area.code and subject_area.codename:
            update_values = {'codename': subject_area.codename}

        insert_subject_area_stmt = insert_subject_area_stmt.on_conflict_do_update(
            index_elements=index_elements, set_=update_values
        )
        self.session.execute(insert_subject_area_stmt)
