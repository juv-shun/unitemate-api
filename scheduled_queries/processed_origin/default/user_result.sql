WITH yesterday_table AS (
    SELECT *
    FROM "unitemate-api-prd"."origin_user_results-prd"
    WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
        AND namespace IN ('default', 'default_free')
), winner_table AS (
    SELECT namespace, match_id, max_by(winner, cnt) AS winner
    FROM (
        SELECT namespace, match_id, winner, COUNT(*) AS cnt
        FROM yesterday_table
        GROUP BY namespace, match_id, winner
        HAVING COUNT(*) >= 5
    )
    GROUP BY namespace, match_id
    HAVING max_by(winner, cnt) <> 'invalid'
)

SELECT
    winner_table.namespace,
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
ON winner_table.namespace = yesterday_table.namespace AND winner_table.match_id = yesterday_table.match_id
