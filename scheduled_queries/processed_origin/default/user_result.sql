WITH yesterday_table AS (
    SELECT *
    FROM "unitemate-api-prd"."origin_user_results-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND namespace = 'default'
), winner_table AS (
    SELECT match_id, max_by(winner, cnt) AS winner
    FROM (
        SELECT match_id, winner, COUNT(*) AS cnt
        FROM yesterday_table
        GROUP BY match_id, winner
        HAVING COUNT(*) >= 5
    )
    GROUP BY match_id
    HAVING max_by(winner, cnt) <> 'invalid'
)

SELECT
    'default' AS namespace,
    winner_table.match_id,
    user_id,
    time,
    'user_result' AS measure_name,
    IF(is_first_pick, 'first', 'second') AS pick_order,
    CASE
        WHEN IF(is_first_pick, 'first', 'second') = winner_table.winner
        THEN 'win' ELSE 'lose'
    END AS result,
    pokemon,
    move1,
    move2,
    rate
FROM winner_table
JOIN yesterday_table
ON winner_table.match_id = yesterday_table.match_id
