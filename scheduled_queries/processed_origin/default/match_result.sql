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
), time_table AS (
    SELECT namespace, match_id, MIN(time) AS time
    FROM yesterday_table
    GROUP BY namespace, match_id
), rate_table AS (
    SELECT namespace, match_id, MIN(rate) AS rate
    FROM yesterday_table
    GROUP BY namespace, match_id
), banned_table AS (
    SELECT namespace, match_id, is_first_pick, max_by(banned_pokemon, banned_cnt) AS banned_pokemon
    FROM (
        SELECT namespace, match_id, is_first_pick, banned_pokemon_0 AS banned_pokemon, COUNT(*) AS banned_cnt
        FROM yesterday_table
        GROUP BY namespace, match_id, is_first_pick, banned_pokemon_0
    )
    GROUP BY namespace, match_id, is_first_pick
)

SELECT
    winner_table.namespace,
    winner_table.match_id,
    time_table.time,
    'match_result' AS measure_name,
    winner_table.winner,
    first_banned_pokemon0,
    second_banned_pokemon0,
    rate_table.rate
FROM winner_table
JOIN time_table ON winner_table.namespace = time_table.namespace AND winner_table.match_id = time_table.match_id
JOIN rate_table ON winner_table.namespace = rate_table.namespace AND winner_table.match_id = rate_table.match_id
LEFT JOIN (
    SELECT namespace, match_id, banned_pokemon AS first_banned_pokemon0
    FROM banned_table
    WHERE is_first_pick = true
) AS first_banned
ON winner_table.namespace = first_banned.namespace AND winner_table.match_id = first_banned.match_id
LEFT JOIN (
    SELECT namespace, match_id, banned_pokemon AS second_banned_pokemon0
    FROM banned_table
    WHERE is_first_pick = false
) AS second_banned
ON winner_table.namespace = second_banned.namespace AND winner_table.match_id = second_banned.match_id
