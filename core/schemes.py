from typing import Any, Dict, List, Optional, Union

from pydantic import (
    BaseModel, ConfigDict, Field, field_validator, model_validator, NonNegativeInt, PositiveInt, ValidationError
)


class _BaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, coerce_numbers_to_str=True)

    @field_validator('*', mode='before')
    def empty_value_to_none(cls, v: Any) -> Any:
        if v == '':
            return None

        return v


class SubjectArea(_BaseModel):
    name: str
    code: Optional[PositiveInt] = None
    codename: Optional[str] = None

    @model_validator(mode='before')
    def prevalidate_subject_area_data(cls, data: Any) -> Any:
        if isinstance(data, Dict):
            data['name'] = data.get('displayName') or data.get('name')

            code_value = data.get('code')
            if isinstance(code_value, str) and not code_value.isdecimal():
                del data['code']
                data['codename'] = code_value

        return data


class SourceRelationship(_BaseModel):
    issue: Optional[str] = None
    volume: Optional[str] = None
    article_number: Optional[str] = Field(default=None, validation_alias='articleNumber')

    page_count: Optional[PositiveInt] = Field(default=None, validation_alias='pageCount')
    first_page: Optional[PositiveInt] = Field(default=None, validation_alias='pageFirst')
    last_page: Optional[PositiveInt] = Field(default=None, validation_alias='pageLast')
    info_page: Optional[PositiveInt] = Field(default=None, validation_alias='pageInfo')

    @model_validator(mode='before')
    def extract_pages_nums(cls, source_relationship_data: Any):
        if isinstance(source_relationship_data, dict):
            pages_nums = source_relationship_data.get('pages', {}) or {}
            if isinstance(pages_nums, dict):
                source_relationship_data.update(pages_nums)

        return source_relationship_data


class Source(_BaseModel):
    id: str

    title: str
    title_abbreviation: Optional[str] = Field(default=None, validation_alias='sourceTitleAbbreviation')

    pub_year: Optional[PositiveInt] = Field(default=None, validation_alias='publicationYear')
    publisher: Optional[str] = None
    is_active: Optional[bool] = Field(default=None, validation_alias='active')

    issn: Optional[str] = None
    coden: Optional[str] = None
    eissn: Optional[str] = None
    isbn: Optional[str] = None
    issnp: Optional[str] = None


class Document(_BaseModel):
    scopus_id: str = Field(validation_alias='scopusId')
    main_title: str = Field(validate_default='title')
    eid: str

    titles: List[str]
    authors_ids: List[str]

    pub_year: PositiveInt = Field(validation_alias='pubYear')

    document_type: Optional[str] = Field(default=None, validation_alias='documentType')
    publication_stage: Optional[str] = Field(default=None, validation_alias='publicationStage')
    total_authors: Optional[PositiveInt] = Field(default=None, validation_alias='totalAuthors')

    abstract_available: Optional[bool] = Field(default=None, validation_alias='abstractAvailable')
    abstract_texts: List[Optional[str]] = Field(default=[], validation_alias='abstractText')

    citations_count: Optional[NonNegativeInt] = None
    references_count: Optional[NonNegativeInt] = None

    status_type: Optional[str] = Field(default=None, validation_alias='statusType')
    free_to_read: Optional[bool] = Field(default=None, validation_alias='freetoread')

    doi: Optional[str] = None
    pui: Optional[str] = Field(default=None, validation_alias='PUI')
    scopus_id_: Optional[str] = Field(default=None, validation_alias='SCOPUS')
    src_occ_id: Optional[str] = Field(default=None, validation_alias='SRC-OCC-ID')
    reaxyscar: Optional[str] = Field(default=None, validation_alias='REAXYSCAR')
    cpx: Optional[str] = Field(default=None, validation_alias='CPX')
    car_id: Optional[str] = Field(default=None, validation_alias='CAR-ID')
    sgr: Optional[str] = Field(default=None, validation_alias='SGR')
    tpa_id: Optional[str] = Field(default=None, validation_alias='TPA-ID')

    subject_areas: List[SubjectArea] = Field(validation_alias='subjectAreas')

    source_relationship: SourceRelationship = Field(default=SourceRelationship(), validation_alias='sourceRelationship')
    source: Source

    @model_validator(mode='before')
    def prevalidate_input_data(cls, document_data: Any) -> Any:
        if isinstance(document_data, Dict):
            cls._extract_document_ids(document_data)
            cls._extract_authors_ids(document_data)

            cls._validate_titles(document_data)

            cls._extract_citations_count(document_data)
            cls._extract_references_count(document_data)

            return document_data
        else:
            raise ValidationError('Incorrect document data input')

    @staticmethod
    def _extract_document_ids(document_data: Dict) -> None:
        document_ids = document_data.get('databaseDocumentIds', {}) or {}
        if isinstance(document_ids, Dict):
            document_data.update(document_ids)

    @staticmethod
    def _extract_authors_ids(document_data: Dict) -> None:
        authors = document_data.get('authors', []) or []
        if isinstance(authors, List):
            document_data['authors_ids'] = [author.get('authorId') for author in authors
                                            if isinstance(author, Dict) and author.get('authorId')]

    @staticmethod
    def _validate_titles(document_data: Dict) -> None:
        def is_valid_title(title_: str) -> bool:
            return title_ and isinstance(title_, str)

        main_title = document_data.get('title') or None
        titles = document_data.get('titles', []) or []

        if isinstance(titles, List):
            titles.append(main_title)

            document_data['titles'] = list({title for title in titles if is_valid_title(title)})
            if not document_data['titles']:
                raise ValidationError('No document titles')
        else:
            if is_valid_title(main_title):
                document_data['titles'] = [main_title]
            else:
                raise ValidationError('No document titles')

    @staticmethod
    def _extract_citations_count(document_data: Dict) -> None:
        citations = document_data.get('citations', {}) or {}
        if isinstance(citations, Dict):
            document_data['citations_count'] = citations.get('count')

    @staticmethod
    def _extract_references_count(document_data: Dict) -> None:
        references = document_data.get('references', {}) or {}
        if isinstance(references, Dict):
            document_data['references_count'] = references.get('count')

    def dump_titles(self) -> List[Dict[str, str]]:
        return [{'document_id': self.scopus_id, 'title': title} for title in self.titles]

    def dump_abstract_texts(self) -> List[Dict[str, str]]:
        return [{'document_id': self.scopus_id, 'text': abstract_text} for abstract_text in self.abstract_texts]

    def dump_subject_areas(self) -> List[Dict[str, Union[str, PositiveInt]]]:
        return [
            {'document_id': self.scopus_id, 'subject_area_code': subject_area.code}
            for subject_area in self.subject_areas
        ]

    def dump_source_relationship(self) -> Dict:
        source_relationship = self.source_relationship.model_dump()
        source_relationship.update({'document_id': self.scopus_id})
        return source_relationship

    def dump_source(self) -> Dict[str, str]:
        return {'document_id': self.scopus_id, 'source_id': self.source.id}

    def dump_authors(self) -> List[Dict[str, str]]:
        return [{'document_id': self.scopus_id, 'author_id': author_id} for author_id in self.authors_ids]

    def dump(self) -> Dict[str, str]:
        return self.model_dump(
            by_alias=True,
            exclude={'titles', 'authors_ids', 'abstract_texts', 'subject_areas', 'source_relationship', 'source'}
        )


class AffiliatedInstitution(_BaseModel):
    id: str
    name: str

    country: str
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = Field(default=None, validation_alias='postalCode')
    street_address: Optional[str] = Field(default=None, validation_alias='streetAddress')

    url: Optional[str] = None
    domain: Optional[str] = None

    @model_validator(mode='before')
    def extract_address(cls, affiliated_institution_data: Any) -> Any:
        if isinstance(affiliated_institution_data, Dict):
            address = affiliated_institution_data.get('address', {}) or {}
            if isinstance(address, Dict):
                affiliated_institution_data.update(address)

        return affiliated_institution_data


class Author(_BaseModel):
    id: str = Field(validation_alias='authorId')
    eid: str
    orc_id: Optional[str] = Field(default=None, validation_alias='orcId')

    first_name: str = Field(validation_alias='first')
    last_name: str = Field(validation_alias='last')
    full_name: str = Field(validation_alias='full')
    name_variants: List[Optional[str]] = Field(default=[], validation_alias='nameVariants')
    email_address: Optional[str] = Field(default=None, validation_alias='emailAddress')

    affiliated_institution: 'AffiliatedInstitution' = Field(validation_alias='latestAffiliatedInstitution')
    affiliated_institution_id: str

    document_count: Optional[int] = Field(default=None, validation_alias='documentCount')
    coauthors_count: Optional[int] = Field(default=None, validation_alias='coAuthorsCount')

    citations_count: Optional[int] = Field(default=None, validation_alias='citationsCount')
    cited_by_count: Optional[int] = Field(default=None, validation_alias='citedByCount')
    h_index: Optional[int] = Field(default=None, validation_alias='hindex')

    subject_areas: List['SubjectArea'] = Field(validation_alias='publishedSubjectAreas')

    @model_validator(mode='before')
    def prevalidate_author_data(cls, author_data: Any) -> Any:
        if isinstance(author_data, Dict):
            cls._extract_names(author_data)
            cls._extract_affiliated_institution_id(author_data)
            return author_data
        else:
            raise ValidationError('Incorrect author data input')

    @staticmethod
    def _extract_names(author_data: Dict) -> None:
        names = author_data.get('preferredName', {}) or {}
        if isinstance(names, Dict):
            author_data.update(names)

    @staticmethod
    def _extract_affiliated_institution_id(author_data: Dict) -> None:
        affiliated_institution = author_data.get('latestAffiliatedInstitution', {}) or {}
        if isinstance(affiliated_institution, Dict):
            author_data.update({'affiliated_institution_id': affiliated_institution.get('id') or None})

    def dump_name_variants(self) -> List[Dict[str, str]]:
        return [{'author_id': self.id, 'name': name} for name in self.name_variants]

    def dump_subject_areas(self) -> List[Dict[str, str]]:
        return [
            {'author_id': self.id, 'subject_area_codename': subject_area.codename}
            for subject_area in self.subject_areas
        ]


if __name__ == '__main__':
    a = {
        "citations": {
            "count": 1,
            "link": "https://www.scopus.com/api/documents/citations/count?eid=2-s2.0-85182507917"
        },
        "references": {
            "count": 22,
            "link": "https://www.scopus.com/api/documents/reference/count?eid=2-s2.0-85182507917"
        },
        "totalAuthors": 2,
        "freetoread": False,
        "abstractText": [
            "Researching bot attacks and creating possible ways to combat them is a new direction of research in the information security. Bot detection can become an important part of trusted interaction technology, as the relevance of such attacks is constantly increasing. Bots automate processes, simplify interaction with various services and help the user in solving various tasks. However, among the many useful bots, there are also bad bots that negatively impact users and organizations.This article discusses the advantages of detecting bots using mouse dynamics. An analysis of existing methods for identifying bots is carried out. Publicly available datasets that can be used to identify bots through mouse cursor movement patterns are reviewed."
        ],
        "eid": "2-s2.0-85182507917",
        "subjectAreas": [
            {
                "code": 17,
                "displayName": "Computer Science"
            },
            {
                "code": 18,
                "displayName": "Decision Sciences"
            },
            {
                "code": 22,
                "displayName": "Engineering"
            },
            {
                "code": 31,
                "displayName": "Physics and Astronomy"
            }
        ],
        "authors": [
            {
                "links": [
                    {
                        "rel": "self",
                        "type": "GET",
                        "href": "https://www.scopus.com/api/authors/58815351600"
                    }
                ],
                "authorId": "58815351600",
                "preferredName": {
                    "first": " N.S.",
                    "last": "Afanaseva",
                    "full": "Afanaseva, N.S."
                }
            },
            {
                "links": [
                    {
                        "rel": "self",
                        "type": "GET",
                        "href": "https://www.scopus.com/api/authors/55027255900"
                    }
                ],
                "authorId": "55027255900",
                "preferredName": {
                    "first": " P.S.",
                    "last": "Lozhnikov",
                    "full": "Lozhnikov, P.S."
                }
            }
        ],
        "statusType": "core",
        "abstractAvailable": True,
        "publicationStage": "final",
        "sourceRelationship": {
            "issue": "",
            "volume": "",
            "articleNumber": "",
            "pageCount": "",
            "pages": {
                "pageFirst": "",
                "pageLast": "",
                "pageInfo": ""
            }
        },
        "documentType": "Conference Paper",
        "doi": "10.1109/Dynamics60586.2023.10349640",
        "scopusId": "85182507917",
        "pubYear": 2023,
        "databaseDocumentIds": {
            "SCP": "85182507917",
            "PUI": "643236192",
            "SCOPUS": "20240247058",
            "CPX": "20240315399018",
            "CAR-ID": "953589449",
            "SGR": "85182507917"
        },
        "titles": [
            "Bot Detection Using Mouse Movements"
        ],
        "source": {
            "active": False,
            "publicationYear": "2023",
            "publisher": "Institute of Electrical and Electronics Engineers Inc.",
            "sourceType": "p",
            "issn": "",
            "coden": "",
            "eissn": "",
            "isbn": "9798350358315",
            "issnp": "",
            "sourceTitleAbbreviation": "Int. Sci. Tech. Conf. Dyn. Syst., Mech. Mach., Dynamics - Proc.",
            "title": "2023 International Scientific and Technical Conference on Dynamics of Systems, Mechanisms and Machines, Dynamics 2023 - Proceedings",
            "id": "21101196460"
        },
        "title": "Bot Detection Using Mouse Movements"
    }
    print(Document.model_validate(a).model_dump(by_alias=True))

    b = {
        "eid": "9-s2.0-58815351600",
        "emailAddress": "dikarevich.ns@gmail.com",
        "citedByCount": 1,
        "documentCount": 1,
        "authorId": "58815351600",
        "orcId": None,
        "preferredName": {
            "first": "N. S.",
            "last": "Afanaseva",
            "full": "Afanaseva, N. S."
        },
        "nameVariants": [],
        "latestAffiliatedInstitution": {
            "domain": None,
            "url": None,
            "name": "Omsk State Transport University",
            "id": "60104566",
            "address": {
                "streetAddress": None,
                "city": "Omsk",
                "postalCode": None,
                "country": "Russian Federation",
                "state": None
            }
        },
        "publishedSubjectAreas": [
            {
                "code": "COMP",
                "name": "Computer Science"
            },
            {
                "code": "ENGI",
                "name": "Engineering"
            },
            {
                "code": "PHYS",
                "name": "Physics and Astronomy"
            },
            {
                "code": "DECI",
                "name": "Decision Sciences"
            }
        ],
        "citationsCount": 1,
        "hindex": 1,
        "coAuthorsCount": 1
    }
    print(Author.model_validate(b).model_dump(by_alias=True))
