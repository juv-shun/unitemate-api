UNLOAD (
    SELECT *
    FROM "{db}"."{table}"
    WHERE time BETWEEN '{yesterday}' AND '{yesterday}' + 1d
) TO 's3://{bucket}/origin/{yesterday}/{table}'
