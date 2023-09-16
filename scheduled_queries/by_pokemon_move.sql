WITH valid_matches AS (
    SELECT match_id, max_by(winner, cnt) AS winner
    FROM (
        SELECT match_id, winner, COUNT(*) AS cnt
        FROM "unitemate-api-prd"."origin_user_results-prd"
        WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
            AND namespace = 'default'
        GROUP BY match_id, winner
        HAVING COUNT(*) >= 5
    )
    GROUP BY match_id
    HAVING max_by(winner, cnt) <> 'invalid'
), filter_by_valid_matches AS (
    SELECT
        valid_matches.match_id,
        valid_matches.winner,
        is_first_pick,
        time,
        pokemon,
        move1,
        move2,
        banned_pokemon_0,
        rate
    FROM "unitemate-api-prd"."origin_user_results-prd" AS origin
    JOIN valid_matches ON origin.match_id = valid_matches.match_id
)

SELECT
    total.pokemon,
    total.move1,
    total.move2,
    bin(@scheduled_runtime, 1d) - 1d AS time,
    'aggregate_by_pokemon_move' AS measure_name,
    picked_win,
    picked_lose,
    picked_total,
    (
        SELECT COUNT(match_id)
        FROM valid_matches
    ) AS match_total
FROM (
    SELECT pokemon, move1, move2, COUNT(DISTINCT match_id) AS picked_total
    FROM filter_by_valid_matches
    GROUP BY pokemon, move1, move2
) AS total
JOIN (
    SELECT pokemon, move1, move2, COUNT(DISTINCT match_id) AS picked_win
    FROM filter_by_valid_matches
    WHERE
        (winner = 'first' AND is_first_pick = true)
        OR (winner = 'second' AND is_first_pick = false)
    GROUP BY pokemon, move1, move2
) AS win
ON total.pokemon = win.pokemon AND total.move1 = win.move1 AND total.move2 = win.move2
JOIN (
    SELECT pokemon, move1, move2, COUNT(DISTINCT match_id) AS picked_lose
    FROM filter_by_valid_matches
    WHERE
        (winner = 'first' AND is_first_pick = false)
        OR (winner = 'second' AND is_first_pick = true)
    GROUP BY pokemon, move1, move2
) AS lose
ON total.pokemon = lose.pokemon AND total.move1 = lose.move1 AND total.move2 = lose.move2
ORDER BY picked_total DESC
