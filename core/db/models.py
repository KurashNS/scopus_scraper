from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Document(Base):
    __tablename__ = 'documents'

    scopus_id = Column(String, primary_key=True, index=True)
    main_title = Column(String, nullable=False)
    eid = Column(String, nullable=False, unique=True, index=True)

    titles = relationship('DocumentTitle', back_populates='document', cascade='all, delete-orphan')
    authors = relationship('DocumentAuthorship', back_populates='document', cascade='all, delete-orphan')

    pub_year = Column(Integer, nullable=False, index=True)

    document_type = Column(String, nullable=True)
    publication_stage = Column(String, nullable=True)
    total_authors = Column(Integer, nullable=True)

    abstract_available = Column(Boolean, nullable=True)
    abstract_texts = relationship('DocumentAbstractText', back_populates='document', cascade='all, delete-orphan')

    citations_count = Column(Integer, nullable=True)
    references_count = Column(Integer, nullable=True)

    status_type = Column(String, nullable=True)
    free_to_read = Column(Boolean, nullable=True)

    doi = Column(String, nullable=True, index=True)
    pui = Column(String, nullable=True, index=True)
    scopus_id_ = Column(String, nullable=True, index=True)
    src_occ_id = Column(String, nullable=True, index=True)
    reaxyscar = Column(String, nullable=True, index=True)
    cpx = Column(String, nullable=True, index=True)
    car_id = Column(String, nullable=True, index=True)
    sgr = Column(String, nullable=True, index=True)
    tpa_id = Column(String, nullable=True, index=True)

    subject_areas = relationship('DocumentSubjectArea', back_populates='document', cascade='all, delete-orphan')

    source_relationship = relationship(
        'DocumentSourceRelationship', back_populates='document', cascade='all, delete-orphan'
    )
    source = relationship('DocumentSource', back_populates='document', cascade='all, delete-orphan')


class DocumentTitle(Base):
    __tablename__ = 'documents_titles'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    document_id = Column(String, ForeignKey('documents.scopus_id'), nullable=False, index=True)
    document = relationship('Document', back_populates='titles')

    title = Column(String, nullable=False, unique=True)

    __table_args__ = (
        UniqueConstraint('document_id', 'title', name='_document_title_uc'),
    )


class DocumentAbstractText(Base):
    __tablename__ = 'documents_abstract_texts'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    document_id = Column(String, ForeignKey('documents.scopus_id'), nullable=False, index=True)
    document = relationship('Document', back_populates='abstract_texts')

    text = Column(Text, nullable=False, unique=True)

    __table_args__ = (
        UniqueConstraint('document_id', 'text', name='_document_abstract_text_uc'),
    )


class DocumentSubjectArea(Base):
    __tablename__ = 'documents_subject_areas'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    document_id = Column(String, ForeignKey('documents.scopus_id'), nullable=False, index=True)
    document = relationship('Document', back_populates='subject_areas')

    subject_area_code = Column(Integer, ForeignKey('subject_areas.code'), nullable=False, index=True)
    subject_area = relationship('SubjectArea', back_populates='document', cascade='all')

    __table_args__ = (
        UniqueConstraint('document_id', 'subject_area_code', name='_document_subject_areas_uc'),
    )


class DocumentSourceRelationship(Base):
    __tablename__ = 'documents_sources_relationships'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    document_id = Column(String, ForeignKey('documents.scopus_id'), nullable=False, unique=True, index=True)
    document = relationship('Document', back_populates='source_relationship')

    issue = Column(String, nullable=True)
    volume = Column(String, nullable=True)
    article_number = Column(String, nullable=True)

    page_count = Column(Integer, nullable=True)
    first_page = Column(Integer, nullable=True)
    last_page = Column(Integer, nullable=True)
    info_page = Column(Integer, nullable=True)


class DocumentSource(Base):
    __tablename__ = 'documents_sources'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    document_id = Column(String, ForeignKey('documents.scopus_id'), unique=True, nullable=False, index=True)
    document = relationship('Document', back_populates='source')

    source_id = Column(String, ForeignKey('sources.id'), nullable=False, index=True)
    source = relationship('Source', back_populates='documents')


class Source(Base):
    __tablename__ = 'sources'

    id = Column(String, primary_key=True, index=True)

    title = Column(String, nullable=False)
    title_abbreviation = Column(String, nullable=True)

    pub_year = Column(Integer, nullable=True, index=True)
    publisher = Column(String, nullable=True, index=True)
    is_active = Column(Boolean, nullable=True, index=True)

    issn = Column(String, nullable=True, index=True)
    coden = Column(String, nullable=True, index=True)
    eissn = Column(String, nullable=True, index=True)
    isbn = Column(String, nullable=True, index=True)
    issnp = Column(String, nullable=True, index=True)

    documents = relationship('DocumentSource', back_populates='source', cascade='all')


class DocumentAuthorship(Base):
    __tablename__ = 'documents_authorship'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    document_id = Column(String, ForeignKey('documents.scopus_id'), nullable=False, index=True)
    document = relationship('Document', back_populates='authors', cascade='all')

    author_id = Column(String, ForeignKey('authors.id'), nullable=False, index=True)
    author = relationship('Author', back_populates='documents', cascade='all')

    __table_args__ = (
        UniqueConstraint('document_id', 'author_id', name='_document_author_uc'),
    )


class Author(Base):
    __tablename__ = 'authors'

    id = Column(String, primary_key=True, index=True)
    eid = Column(String, nullable=False, index=True)
    orc_id = Column(String, nullable=True, index=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    name_variants = relationship('AuthorNameVariant', back_populates='author', cascade='all, delete-orphan')

    email_address = Column(String, nullable=True)

    affiliated_institution_id = Column(String, ForeignKey('authors_affiliated_institutions.id'), nullable=False, index=True)
    affiliated_institution = relationship('AuthorAffiliatedInstitution',  back_populates='authors', cascade='all')

    document_count = Column(Integer, nullable=True, index=True)
    coauthors_count = Column(Integer, nullable=True, index=True)

    citations_count = Column(Integer, nullable=True, index=True)
    cited_by_count = Column(Integer, nullable=True, index=True)
    h_index = Column(Integer, nullable=True, index=True)

    subject_areas = relationship(
        'AuthorSubjectArea', back_populates='author', cascade='all, delete-orphan'
    )

    documents = relationship('DocumentAuthorship', back_populates='author', cascade='all')


class AuthorNameVariant(Base):
    __tablename__ = 'authors_name_variants'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    author_id = Column(String, ForeignKey('authors.id'), nullable=False, index=True)
    author = relationship('Author', back_populates='name_variants', cascade='all')

    name = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint('author_id', 'name', name='_author_name_uc'),
    )


class AuthorSubjectArea(Base):
    __tablename__ = 'authors_subject_areas'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    author_id = Column(String, ForeignKey('authors.id'), nullable=False, index=True)
    author = relationship('Author', back_populates='subject_areas', cascade='all')

    subject_area_codename = Column(String, ForeignKey('subject_areas.codename'), nullable=False, index=True)
    subject_area = relationship('SubjectArea', back_populates='author', cascade='all')

    __table_args__ = (
        UniqueConstraint('author_id', 'subject_area_codename', name='_author_subject_area_uc'),
    )


class AuthorAffiliatedInstitution(Base):
    __tablename__ = 'authors_affiliated_institutions'

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)

    domain = Column(String, nullable=True)
    url = Column(String, nullable=True)

    country = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True, index=True)
    city = Column(String, nullable=True, index=True)
    postal_code = Column(String, nullable=True)
    street_address = Column(String, nullable=True)

    authors = relationship('Author', back_populates='affiliated_institution', cascade='all')


class SubjectArea(Base):
    __tablename__ = 'subject_areas'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    code = Column(Integer, unique=True, nullable=True, index=True)
    document = relationship('DocumentSubjectArea', back_populates='subject_area', cascade='all, delete-orphan')

    codename = Column(String, unique=True, nullable=True, index=True)
    author = relationship('AuthorSubjectArea', back_populates='subject_area', cascade='all, delete-orphan')

    name = Column(String, unique=True, nullable=False)


if __name__ == '__main__':
    a = AuthorSubjectArea(
        author_id='12312312',
        subject_area_codename='COMP',
    ).__dict__

    print({col_name: value for col_name, value in a.items() if col_name[0] != '_'})
