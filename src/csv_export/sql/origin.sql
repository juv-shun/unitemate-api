UNLOAD (
    SELECT *
    FROM "{db}"."{table}"
    WHERE time BETWEEN bin(now(), 1d) - 1d AND bin(now(), 1d)
) TO 's3://{bucket}/origin/{date}/{table}'
