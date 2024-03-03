WITH yesterday_table AS (
    SELECT *
    FROM "unitemate-api-prd"."origin_user_results-prd"
    WHERE time > @scheduled_runtime - interval '30' minute
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
), banned_table AS (
    SELECT DISTINCT namespace, match_id, IF(is_first_pick, 'first', 'second') AS pick_order, banned_pokemon_0 AS banned_pokemon
    FROM yesterday_table
    WHERE banned_pokemon_0 != 'empty'
)

SELECT
    winner_table.namespace,
    winner_table.match_id,
    CONCAT(pick_order, '', banned_pokemon) AS ban_key,
    time_table.time,
    'ban_result' AS measure_name,
    pick_order,
    banned_pokemon
FROM winner_table
JOIN time_table ON winner_table.namespace = time_table.namespace AND winner_table.match_id = time_table.match_id
LEFT JOIN banned_table ON winner_table.namespace = banned_table.namespace AND winner_table.match_id = banned_table.match_id
