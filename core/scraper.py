import time
from typing import Dict, Optional

from requests import Session
from requests.cookies import RequestsCookieJar
from requests.exceptions import HTTPError, RequestException, JSONDecodeError, ProxyError, ConnectTimeout
from tenacity import retry, retry_if_exception_type as retry_if_exc_type, wait_random, stop_after_attempt
import ua_generator

from utils import constants
from utils.log import ScopusClientLogger


request_exc = (RequestException, JSONDecodeError, ProxyError, ConnectTimeout)

wait_to_retry = wait_random(min=30, max=45)
stop_retry = stop_after_attempt(5)


class ScopusClient:
    _instance = None

    def __new__(cls, proxies: Optional[Dict[str, str]] = None):
        if cls._instance is None:
            cls._instance = super(ScopusClient, cls).__new__(cls)
            cls._instance._init(proxies)
        return cls._instance

    def _init(self, proxies: Optional[Dict[str, str]] = None):
        self._proxies: Dict[str, str] = proxies or {}
        self._session: Session = Session()

        self._logger = ScopusClientLogger()

    def __enter__(self):
        self._init_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._session:
            self._session.close()
        return False

    def _init_client(self) -> None:
        self._session.proxies.update(self._proxies)
        self._update_session_headers()

        self._scopus_auth()

    def _reset_client(self) -> None:
        self._session.cookies = RequestsCookieJar()
        self._update_session_headers()

        self._scopus_auth()

    def _update_session_headers(self) -> None:
        ua = ua_generator.generate(device='desktop')
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': ua.ch.brands,
            'sec-ch-ua-mobile': ua.ch.mobile,
            'sec-ch-ua-platform': ua.ch.platform,
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': ua.text,
        }
        self._session.headers.update(headers)

    @retry(sleep=time.sleep, retry=retry_if_exc_type(request_exc), wait=wait_to_retry, reraise=True)
    def _scopus_auth(self) -> None:
        try:
            auth_claim_headers = {
                'accept': '*/*',
                'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
                'priority': 'u=1, i',
                'sec-ch-ua': self._session.headers.get('sec-ch-ua', ''),
                'sec-ch-ua-mobile': self._session.headers.get('sec-ch-ua-mobile', ''),
                'sec-ch-ua-platform': self._session.headers.get('sec-ch-ua-platform', ''),
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': self._session.headers.get('user-agent', ''),
                'x-requested-with': 'XMLHttpRequest',
            }           
            r = self._session.get(url=constants.AUTH_CLAIM_URI, headers=auth_claim_headers, proxies=self._session.proxies)
            print(r.text)
            r.raise_for_status()
            self._session.get(url=constants.SCOPUS_URL, proxies=self._session.proxies).raise_for_status()
        except HTTPError as e:
            self._logger.error(f'Unable to authorize to SCOPUS: {type(e)} - {str(e)}')
            self._reset_client()
            raise
        except (ProxyError, ConnectTimeout) as e:
            self._logger.error(f'Proxy error: {type(e)} - {str(e)}')
            raise

    @retry(sleep=time.sleep, retry=retry_if_exc_type(request_exc), wait=wait_to_retry, reraise=True)
    def get_author(self, author_id: str) -> Dict:
        try:
            response = self._session.get(url=f'{constants.BASE_AUTHOR_PROFILE_URL}{author_id}', proxies=self._session.proxies)
            if response.status_code in [400, 403, 404]:
                print(response.status_code)
                print(response.content)
                return {}
            else:
                response.raise_for_status()
            self._logger.info(f'Author ID: {author_id} | {response.json()}')
            return response.json()
        except (RequestException, JSONDecodeError) as e:
            self._logger.error(f'Author ID: {author_id} | Unable to get author description: {type(e)} - {str(e)}')
            self._reset_client()
            raise
        except (ProxyError, ConnectTimeout) as e:
            self._logger.error(f'Proxy error: {type(e)} - {str(e)}')
            raise

    @retry(sleep=time.sleep, retry=retry_if_exc_type(request_exc), wait=wait_to_retry, reraise=True)
    def get_author_documents(self, author_id: str) -> Dict:
        try:
            params = {
                'allauthors': 'false',
                'authorid': author_id,
                'documentClassificationEnum': 'primary',
                'itemcount': '10',
                'offset': '0',
                'outwardlinks': 'true',
                'preprint': 'false',
                'showAbstract': 'false',
                'sort': 'plf-f',
            }
            response = self._session.get(url=constants.AUTHOR_DOCS_LIST_URL, params=params, proxies=self._session.proxies)
            if response.status_code in [400, 403, 404]:
                return {}
            else:
                response.raise_for_status()
            self._logger.info(f'Author ID: {author_id} | {response.json()}')
            return response.json()
        except (RequestException, JSONDecodeError) as e:
            self._logger.error(f'Author ID: {author_id} | Unable to get author documents: {type(e)} - {str(e)}')
            self._reset_client()
            raise
        except (ProxyError, ConnectTimeout) as e:
            self._logger.error(f'Proxy error: {type(e)} - {str(e)}')
            raise


if __name__ == '__main__':
    proxies_ = {
        # 'http': 'http://yfy5n4:s4SsUv@176.10.97.89:20404',
        # 'https': 'http://yfy5n4:s4SsUv@176.10.97.89:20404'
    }

    # author_id_ = '34768872200'
    while True:
        with ScopusClient(proxies=proxies_) as client:
            ...

            # author_documents_descriptions = client.get_author_documents(author_id=author_id_)
            # print(author_documents_descriptions)
            # author_documents = [
            #     ScopusDocument(doc_desc=item)
            #     for item in author_documents_descriptions.get('items', [])
            #     if int(item.get('pubYear', 0) > 2021)
            # ]
            # print(author_documents)
            # print('-----------------------------------------------')
            #
            # coauthors_ids = []
            # for document in author_documents:
            #     coauthors_ids.extend(document.authors_id)
            #
            # coauthors_ids = list(set(coauthors_ids))
            # print(coauthors_ids)
            #
            # coauthors_descriptions = [client.get_author(author_id=coauthor_id) for coauthor_id in coauthors_ids]
            # print(coauthors_descriptions)
            # authors = [Author(author_desc=coauthor_description) for coauthor_description in coauthors_descriptions]
            # print(authors)
            # print('-----------------------------------------------')
