SELECT DISTINCT documents.* FROM documents

INNER JOIN documents_authorship
ON documents.scopus_id = documents_authorship.document_id

INNER JOIN authors
ON documents_authorship.author_id = authors.id

WHERE authors.affiliated_inst_id IN ('100459484', '60075514', '110906095', '100339616', '101349208', '100423925')
AND documents.pub_year = 2020
