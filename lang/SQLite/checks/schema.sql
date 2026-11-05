PRAGMA integrity_check;
PRAGMA foreign_key_check;

SELECT name AS non_strict_table
FROM pragma_table_list
WHERE
    schema = 'main'
    AND type = 'table'
    AND strict = 0
    AND name NOT LIKE 'sqlite_%';
